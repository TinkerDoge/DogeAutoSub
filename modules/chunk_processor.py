"""
Chunk-based parallel audio processing for DogeAutoSub.
Enables parallel extraction and transcription for accurate progress tracking.
"""

import os
import math
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, List, Optional, Tuple


class ChunkStatus(Enum):
    """Status of a processing chunk."""
    PENDING = "pending"
    EXTRACTING = "extracting"
    EXTRACTED = "extracted"
    TRANSCRIBING = "transcribing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AudioChunk:
    """Represents a processing unit with timing metadata."""
    index: int
    start_time: float
    end_time: float
    audio_path: Optional[str] = None
    status: ChunkStatus = ChunkStatus.PENDING
    segments: List[dict] = field(default_factory=list)
    error: Optional[str] = None
    
    @property
    def duration(self) -> float:
        """Duration of the chunk in seconds."""
        return self.end_time - self.start_time


def get_audio_duration_ffprobe(
    source_path: str,
    ffprobe_path: Optional[str] = None,
) -> Optional[float]:
    """
    Get audio/video duration using ffprobe.
    
    Args:
        source_path: Path to the media file
        ffprobe_path: Path to ffprobe executable
        
    Returns:
        Duration in seconds, or None on error
    """
    if ffprobe_path is None:
        # Try to find ffprobe next to the script
        script_dir = os.path.dirname(os.path.dirname(__file__))
        probe_candidate = os.path.join(script_dir, "modules", "ffmpeg", "bin", "ffprobe.exe")
        if os.path.exists(probe_candidate):
            ffprobe_path = probe_candidate
        else:
            ffprobe_path = "ffprobe"  # System PATH
    
    try:
        cmd = [
            ffprobe_path,
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            source_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except Exception as e:
        print(f"Error getting duration with ffprobe: {e}")
        return None


class ChunkProcessor:
    """
    Manages parallel chunk extraction and transcription.
    
    Processing flow:
    1. Probe total duration with ffprobe
    2. For faster-whisper: Use single-pass processing with native VAD
    3. For legacy whisper: Create chunk schedule with VAD-aware boundaries
    4. Extract chunks in parallel (I/O bound)
    5. Transcribe chunks sequentially (GPU bound)
    6. Merge all segments with corrected timestamps
    """
    
    def __init__(
        self,
        chunk_duration: float = 30.0,
        overlap: float = 1.0,
        max_extract_workers: int = 3,
        temp_dir: Optional[str] = None,
        ffmpeg_path: Optional[str] = None,
        volume_boost: str = "3",
        use_chunking: bool = False,  # Default to False - let faster-whisper use native VAD
    ):
        """
        Initialize ChunkProcessor.
        
        Args:
            chunk_duration: Duration of each chunk in seconds (default: 30s)
            overlap: Overlap between chunks in seconds for word boundary handling
            max_extract_workers: Max parallel extraction workers (I/O bound)
            temp_dir: Directory for temporary chunk files
            ffmpeg_path: Path to ffmpeg executable
            volume_boost: Audio volume boost factor
            use_chunking: If False, process entire file at once (recommended for faster-whisper)
                         If True, split into chunks (for legacy whisper or very long files)
        """
        self.chunk_duration = chunk_duration
        self.overlap = overlap
        self.max_extract_workers = max_extract_workers
        self.volume_boost = volume_boost
        self.use_chunking = use_chunking
        
        # Setup paths
        if temp_dir is None:
            script_dir = os.path.dirname(os.path.dirname(__file__))
            temp_dir = os.path.join(script_dir, "modules", "temp", "chunks")
        self.temp_dir = temp_dir
        os.makedirs(self.temp_dir, exist_ok=True)
        
        if ffmpeg_path is None:
            script_dir = os.path.dirname(os.path.dirname(__file__))
            ffmpeg_candidate = os.path.join(script_dir, "modules", "ffmpeg", "bin", "ffmpeg.exe")
            if os.path.exists(ffmpeg_candidate):
                ffmpeg_path = ffmpeg_candidate
            else:
                ffmpeg_path = "ffmpeg"
        self.ffmpeg_path = ffmpeg_path
        
        # Processing state
        self.chunks: List[AudioChunk] = []
        self.total_duration: float = 0.0
    
    def create_chunk_schedule(self, source_path: str) -> List[AudioChunk]:
        """
        Create list of chunks with timing info.
        
        Args:
            source_path: Path to the source media file
            
        Returns:
            List of AudioChunk objects
        """
        # Get total duration
        self.total_duration = get_audio_duration_ffprobe(source_path) or 0.0
        
        if self.total_duration <= 0:
            print("Warning: Could not determine duration, using single chunk")
            self.chunks = [AudioChunk(
                index=0,
                start_time=0.0,
                end_time=0.0,  # Will process entire file
            )]
            return self.chunks
        
        # Calculate number of chunks
        effective_duration = self.chunk_duration - self.overlap
        num_chunks = max(1, math.ceil(self.total_duration / effective_duration))
        
        print(f"Creating chunk schedule: {num_chunks} chunks for {self.total_duration:.1f}s audio")
        
        self.chunks = []
        for i in range(num_chunks):
            start = i * effective_duration
            end = min(start + self.chunk_duration, self.total_duration)
            
            self.chunks.append(AudioChunk(
                index=i,
                start_time=start,
                end_time=end,
            ))
        
        return self.chunks
    
    def extract_chunk(self, source_path: str, chunk: AudioChunk) -> str:
        """
        Extract a single audio chunk using ffmpeg with fast seek.
        
        Args:
            source_path: Path to source media file
            chunk: AudioChunk object with timing info
            
        Returns:
            Path to extracted chunk audio file
        """
        chunk.status = ChunkStatus.EXTRACTING
        
        # Generate unique chunk filename
        chunk_filename = f"chunk_{chunk.index:04d}_{int(chunk.start_time):06d}.wav"
        chunk_path = os.path.join(self.temp_dir, chunk_filename)
        
        # Build ffmpeg command with fast seek (-ss before -i)
        cmd = [
            self.ffmpeg_path,
            "-hide_banner",
            "-loglevel", "warning",
            "-y",  # Overwrite output
        ]
        
        # Add seek before input for fast seeking
        if chunk.start_time > 0:
            cmd.extend(["-ss", str(chunk.start_time)])
        
        cmd.extend([
            "-i", source_path,
        ])
        
        # Add duration limit
        if chunk.end_time > chunk.start_time:
            duration = chunk.end_time - chunk.start_time
            cmd.extend(["-t", str(duration)])
        
        # Audio output settings
        cmd.extend([
            "-ac", "1",  # Mono
            "-ar", "16000",  # 16kHz sample rate (Whisper requirement)
            "-filter:a", f"volume={self.volume_boost}",
            "-vn",  # No video
            "-f", "wav",
            chunk_path,
        ])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            chunk.audio_path = chunk_path
            chunk.status = ChunkStatus.EXTRACTED
            print(f"Extracted chunk {chunk.index + 1}: {chunk.start_time:.1f}s - {chunk.end_time:.1f}s")
            return chunk_path
        except subprocess.CalledProcessError as e:
            chunk.status = ChunkStatus.FAILED
            chunk.error = f"FFmpeg error: {e.stderr}"
            print(f"Error extracting chunk {chunk.index}: {e.stderr}")
            raise
    
    def _deduplicate_segments(
        self,
        all_segments: List[dict],
        overlap_threshold: float = 0.5,
    ) -> List[dict]:
        """
        Remove duplicate segments from chunk overlaps.
        
        Args:
            all_segments: All segments from all chunks (sorted by start time)
            overlap_threshold: Maximum time difference to consider as duplicate
            
        Returns:
            Deduplicated segment list
        """
        if not all_segments:
            return []
        
        # Sort by start time
        sorted_segs = sorted(all_segments, key=lambda s: s["start"])
        
        deduped = [sorted_segs[0]]
        for seg in sorted_segs[1:]:
            last = deduped[-1]
            
            # Check for overlap/duplicate
            time_diff = abs(seg["start"] - last["start"])
            text_match = seg["text"].strip().lower() == last["text"].strip().lower()
            
            if time_diff < overlap_threshold and text_match:
                # Duplicate, skip
                continue
            elif seg["start"] < last["end"] and time_diff < overlap_threshold:
                # Overlapping segment, keep the one with more text
                if len(seg["text"]) > len(last["text"]):
                    deduped[-1] = seg
                continue
            else:
                deduped.append(seg)
        
        return deduped
    
    def process_parallel(
        self,
        source_path: str,
        recognizer,
        progress_callback: Optional[Callable[[int, int, str, float], None]] = None,
    ) -> Tuple[List[dict], Optional[str]]:
        """
        Process audio with parallel extraction and sequential transcription.
        
        Args:
            source_path: Path to source media file
            recognizer: FasterWhisperRecognizer instance
            progress_callback: Callback(completed_chunks, total_chunks, stage, eta_seconds)
            
        Returns:
            Tuple of (merged segments, detected language)
        """
        start_time = time.time()
        
        # For faster-whisper: Use single-pass processing with native VAD
        # This properly detects sentence boundaries using silence detection
        if not self.use_chunking:
            print("Single-pass mode - faster-whisper will use native VAD for sentence boundaries")
            
            # Get total duration for stats
            self.total_duration = get_audio_duration_ffprobe(source_path) or 0.0
            print(f"Video duration: {self.total_duration:.1f}s")
            
            if progress_callback:
                progress_callback(0, 1, "Extracting audio", 0)
            
            # Extract full audio
            full_audio = self._extract_full_audio(source_path)
            
            if progress_callback:
                progress_callback(0, 1, "Transcribing with VAD...", 0)
            
            segments, language = recognizer.transcribe(full_audio)
            
            total_time = time.time() - start_time
            print(f"Single-pass complete: {len(segments)} segments in {total_time:.1f}s")
            
            if progress_callback:
                progress_callback(1, 1, "Completed", 0)
            
            # Cleanup
            self._cleanup_chunks()
            
            return segments, language
        
        # Legacy chunking mode (for very long files or legacy whisper)
        print("Chunked mode - splitting audio for parallel processing")
        
        # Create chunk schedule
        self.create_chunk_schedule(source_path)
        total_chunks = len(self.chunks)
        
        if total_chunks == 0:
            print("No chunks to process")
            return [], None
        
        print(f"Processing {total_chunks} chunks from: {source_path}")
        
        # Phase 1: Parallel extraction
        extracted_chunks = []
        chunk_times = []  # Track processing times for ETA
        
        if progress_callback:
            progress_callback(0, total_chunks, "Extracting audio chunks", 0)
        
        with ThreadPoolExecutor(max_workers=self.max_extract_workers) as executor:
            future_to_chunk = {
                executor.submit(self.extract_chunk, source_path, chunk): chunk
                for chunk in self.chunks
            }
            
            for future in as_completed(future_to_chunk):
                chunk = future_to_chunk[future]
                try:
                    future.result()
                    extracted_chunks.append(chunk)
                except Exception as e:
                    print(f"Chunk {chunk.index} extraction failed: {e}")
        
        # Sort by index for sequential transcription
        extracted_chunks.sort(key=lambda c: c.index)
        
        # Phase 2: Sequential transcription (GPU bound)
        all_segments = []
        detected_language = None
        completed = 0
        
        for chunk in extracted_chunks:
            if chunk.audio_path is None:
                continue
            
            chunk.status = ChunkStatus.TRANSCRIBING
            chunk_start_time = time.time()
            
            if progress_callback:
                # Calculate ETA based on average chunk time
                if chunk_times:
                    avg_time = sum(chunk_times) / len(chunk_times)
                    remaining = (total_chunks - completed) * avg_time
                else:
                    remaining = 0
                progress_callback(completed, total_chunks, f"Transcribing chunk {chunk.index + 1}/{total_chunks}", remaining)
            
            try:
                # Transcribe with time offset
                segments, lang = recognizer.transcribe_chunk(
                    chunk.audio_path,
                    time_offset=chunk.start_time,
                )
                
                chunk.segments = segments
                chunk.status = ChunkStatus.COMPLETED
                all_segments.extend(segments)
                
                if detected_language is None and lang:
                    detected_language = lang
                
                # Track timing
                chunk_time = time.time() - chunk_start_time
                chunk_times.append(chunk_time)
                completed += 1
                
                print(f"Transcribed chunk {chunk.index + 1}/{total_chunks} in {chunk_time:.1f}s")
                
            except Exception as e:
                chunk.status = ChunkStatus.FAILED
                chunk.error = str(e)
                print(f"Error transcribing chunk {chunk.index}: {e}")
                completed += 1
        
        # Phase 3: Merge and deduplicate
        merged_segments = self._deduplicate_segments(all_segments)
        
        # Re-index segments
        for i, seg in enumerate(merged_segments, start=1):
            seg["id"] = i
        
        total_time = time.time() - start_time
        print(f"Processing complete: {len(merged_segments)} segments in {total_time:.1f}s")
        
        if progress_callback:
            progress_callback(total_chunks, total_chunks, "Completed", 0)
        
        # Cleanup temp files
        self._cleanup_chunks()
        
        return merged_segments, detected_language
    
    def _extract_full_audio(self, source_path: str) -> str:
        """Extract full audio for single-chunk mode."""
        audio_path = os.path.join(self.temp_dir, "full_audio.wav")
        
        cmd = [
            self.ffmpeg_path,
            "-hide_banner",
            "-loglevel", "warning",
            "-y",
            "-i", source_path,
            "-ac", "1",
            "-ar", "16000",
            "-filter:a", f"volume={self.volume_boost}",
            "-vn",
            "-f", "wav",
            audio_path,
        ]
        
        subprocess.run(cmd, capture_output=True, check=True)
        return audio_path
    
    def _cleanup_chunks(self):
        """Remove temporary chunk files."""
        for chunk in self.chunks:
            if chunk.audio_path and os.path.exists(chunk.audio_path):
                try:
                    os.remove(chunk.audio_path)
                except Exception as e:
                    print(f"Warning: Could not remove temp file {chunk.audio_path}: {e}")
        
        # Also clean full audio if exists
        full_audio = os.path.join(self.temp_dir, "full_audio.wav")
        if os.path.exists(full_audio):
            try:
                os.remove(full_audio)
            except Exception:
                pass
