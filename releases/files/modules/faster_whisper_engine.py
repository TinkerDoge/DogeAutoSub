# v2.0.6 - Optimized batched inference and VAD parameters
"""
Faster-Whisper transcription engine for DogeAutoSub.
Uses CTranslate2 for GPU-accelerated transcription with 4x+ speed improvement.
"""

import os
import sys
from typing import Callable, List, Optional, Tuple

# Check for faster-whisper availability
try:
    from faster_whisper import WhisperModel, BatchedInferencePipeline
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False
    print("faster-whisper not available. Install with: pip install faster-whisper")

# Check for torch/CUDA
try:
    import torch
    CUDA_AVAILABLE = torch.cuda.is_available()
    if CUDA_AVAILABLE:
        VRAM_GB = torch.cuda.get_device_properties(0).total_memory / (1024**3)
    else:
        VRAM_GB = 0
except ImportError:
    CUDA_AVAILABLE = False
    VRAM_GB = 0


def get_optimal_compute_type(model_size: str, device: str) -> str:
    """
    Determine optimal compute type based on available resources.
    
    - float16: Fastest on GPU with sufficient VRAM
    - int8_float16: Good balance for limited VRAM
    - int8: CPU optimized
    """
    if device == "cpu":
        return "int8"
    
    # VRAM requirements (approximate) for float16
    vram_requirements = {
        "tiny": 1.0,
        "base": 1.5,
        "small": 2.5,
        "medium": 5.0,
        "large": 10.0,
        "large-v2": 10.0,
        "large-v3": 10.0,
        "large-v3-turbo": 6.0,
        "turbo": 6.0,
        "distil-large-v3": 6.0,
    }
    
    required = vram_requirements.get(model_size.lower(), 5.0)
    
    if VRAM_GB >= required * 1.2:  # 20% headroom
        return "float16"
    elif VRAM_GB >= required * 0.6:
        return "int8_float16"
    else:
        return "int8"


class FasterWhisperRecognizer:
    """
    GPU-optimized Whisper transcription using faster-whisper (CTranslate2).
    
    Features:
    - 4x faster than OpenAI Whisper on GPU
    - Built-in VAD filtering to skip silence
    - Batched inference for additional speedup
    - Auto compute type selection based on VRAM
    """
    
    def __init__(
        self,
        model_size: str = "turbo",
        language: Optional[str] = None,
        device: Optional[str] = None,
        compute_type: Optional[str] = None,
        download_root: Optional[str] = None,
    ):
        """
        Initialize FasterWhisperRecognizer.
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large-v3, turbo, distil-large-v3)
            language: Source language code (None for auto-detection)
            device: "cuda" or "cpu" (auto-detected if None)
            compute_type: "float16", "int8_float16", or "int8" (auto-selected if None)
            download_root: Custom model download directory
        """
        if not FASTER_WHISPER_AVAILABLE:
            raise ImportError(
                "faster-whisper is not installed. "
                "Install with: pip install faster-whisper"
            )
        
        self.language = language if language != "auto" else None
        
        # Map friendly names to faster-whisper model names
        model_mapping = {
            "turbo": "large-v3-turbo",
            "large": "large-v3",
        }
        self.model_size = model_mapping.get(model_size.lower(), model_size)
        
        # Auto-detect device
        if device is None:
            self.device = "cuda" if CUDA_AVAILABLE else "cpu"
        else:
            self.device = device
        
        # Auto-select compute type
        if compute_type is None:
            self.compute_type = get_optimal_compute_type(self.model_size, self.device)
        else:
            self.compute_type = compute_type
        
        # Model download path
        if download_root is None:
            download_root = os.path.join(os.path.dirname(__file__), "models", "faster_whisper")
        os.makedirs(download_root, exist_ok=True)
        
        print(f"Loading faster-whisper model: {self.model_size}")
        print(f"  Device: {self.device}, Compute type: {self.compute_type}")
        
        try:
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
                download_root=download_root,
            )
            
            # Create batched pipeline for additional speedup
            if self.device == "cuda":
                self.batched_model = BatchedInferencePipeline(model=self.model)
            else:
                self.batched_model = None
                
            print("faster-whisper model loaded successfully")
            
        except Exception as e:
            print(f"Error loading faster-whisper model: {e}")
            raise
    
    def detect_language(self, audio_path: str) -> Optional[str]:
        """
        Detect the language spoken in the audio.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Detected language code or None on error
        """
        try:
            segments, info = self.model.transcribe(
                audio_path,
                beam_size=1,
                vad_filter=True,
            )
            # Consume generator to get info
            _ = list(segments)
            detected = info.language
            print(f"Detected language: {detected} (probability: {info.language_probability:.2f})")
            return detected
        except Exception as e:
            print(f"Error during language detection: {e}")
            return None
    
    def transcribe(
        self,
        audio_path: str,
        ffmpeg_path: Optional[str] = None,  # Kept for API compatibility
        progress_callback: Optional[Callable[[int], None]] = None,
        use_vad: bool = True,
        batch_size: int = 16,
        max_segment_length: float = 10.0,  # Max seconds per subtitle segment
    ) -> Tuple[List[dict], Optional[str]]:
        """
        Transcribe audio using faster-whisper.
        
        Args:
            audio_path: Path to audio file
            ffmpeg_path: Unused, kept for API compatibility
            progress_callback: Callback function for progress updates (0-100)
            use_vad: Enable Voice Activity Detection to skip silence
            batch_size: Batch size for batched inference (GPU only)
            max_segment_length: Maximum length of a subtitle segment in seconds
            
        Returns:
            Tuple of (segments list, detected language code)
        """
        try:
            if not os.path.exists(audio_path):
                print(f"Error: Audio file not found at {audio_path}")
                return [], None
            
            print(f"Transcribing: {audio_path}")
            
            # Use regular model (not batched) for word-level timestamps
            # Word timestamps are needed for proper sentence segmentation
            segments_gen, info = self.model.transcribe(
                audio_path,
                language=self.language,
                beam_size=5,
                vad_filter=use_vad,
                vad_parameters=dict(min_silence_duration_ms=500),
                word_timestamps=True,  # Enable word-level timestamps for sentence splitting
            )
            
            # Convert generator to list and track progress
            raw_segments = []
            detected_language = info.language
            
            # Estimate total duration for progress (if available)
            estimated_duration = getattr(info, 'duration', None)
            
            for segment in segments_gen:
                seg_dict = {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip(),
                    "words": segment.words if hasattr(segment, 'words') else None,
                }
                raw_segments.append(seg_dict)
                
                # Update progress based on segment end time
                if progress_callback and estimated_duration and estimated_duration > 0:
                    progress = min(75, int((segment.end / estimated_duration) * 75))
                    progress_callback(progress)
            
            print(f"Raw transcription: {len(raw_segments)} segments")
            
            # Split long segments into subtitle-appropriate lengths
            segments = self._split_long_segments(raw_segments, max_segment_length)
            
            print(f"After splitting: {len(segments)} segments, language: {detected_language}")
            
            if progress_callback:
                progress_callback(75)
            
            return segments, detected_language
            
        except Exception as e:
            print(f"Error during transcription: {e}")
            import traceback
            traceback.print_exc()
            return [], None
    
    def _split_long_segments(
        self,
        segments: List[dict],
        max_length: float = 10.0,
        max_chars: int = 100,
    ) -> List[dict]:
        """
        Split long segments into subtitle-appropriate lengths.
        
        Uses word-level timestamps when available to split at natural breaks.
        
        Args:
            segments: List of segment dicts with optional 'words' key
            max_length: Maximum segment duration in seconds
            max_chars: Maximum characters per segment
            
        Returns:
            List of split segments
        """
        result = []
        
        for seg in segments:
            duration = seg["end"] - seg["start"]
            text = seg["text"]
            words = seg.get("words")
            
            # If segment is short enough, keep as-is
            if duration <= max_length and len(text) <= max_chars:
                result.append({
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": text,
                })
                continue
            
            # If we have word timestamps, use them for intelligent splitting
            if words and len(words) > 1:
                current_words = []
                current_start = None
                current_end = None
                current_text = ""
                
                for word in words:
                    word_text = word.word if hasattr(word, 'word') else str(word.get('word', ''))
                    word_start = word.start if hasattr(word, 'start') else word.get('start', 0)
                    word_end = word.end if hasattr(word, 'end') else word.get('end', 0)
                    
                    if current_start is None:
                        current_start = word_start
                    
                    potential_text = current_text + word_text
                    potential_duration = word_end - current_start
                    
                    # Check if adding this word would exceed limits
                    should_split = (
                        potential_duration > max_length or
                        len(potential_text) > max_chars
                    )
                    
                    # Also check for natural split points (punctuation)
                    ends_sentence = any(word_text.rstrip().endswith(p) for p in '.!?。？！')
                    
                    if should_split and current_text.strip():
                        # Save current segment
                        result.append({
                            "start": current_start,
                            "end": current_end,
                            "text": current_text.strip(),
                        })
                        # Start new segment with this word
                        current_start = word_start
                        current_text = word_text
                        current_end = word_end
                    elif ends_sentence and potential_duration > max_length * 0.5:
                        # Split at sentence end if segment is getting long
                        current_text = potential_text
                        current_end = word_end
                        result.append({
                            "start": current_start,
                            "end": current_end,
                            "text": current_text.strip(),
                        })
                        current_start = None
                        current_text = ""
                        current_end = None
                    else:
                        current_text = potential_text
                        current_end = word_end
                
                # Don't forget the last segment
                if current_text.strip():
                    result.append({
                        "start": current_start,
                        "end": current_end,
                        "text": current_text.strip(),
                    })
            else:
                # No word timestamps - split by character count with estimated timing
                words_list = text.split()
                if not words_list:
                    result.append(seg)
                    continue
                    
                chars_per_second = len(text) / max(duration, 0.1)
                current_text = ""
                current_start = seg["start"]
                
                for word in words_list:
                    if len(current_text) + len(word) + 1 > max_chars and current_text:
                        # Calculate estimated end time
                        chunk_duration = len(current_text) / chars_per_second
                        result.append({
                            "start": current_start,
                            "end": current_start + chunk_duration,
                            "text": current_text.strip(),
                        })
                        current_start = current_start + chunk_duration
                        current_text = word + " "
                    else:
                        current_text += word + " "
                
                # Last chunk
                if current_text.strip():
                    result.append({
                        "start": current_start,
                        "end": seg["end"],
                        "text": current_text.strip(),
                    })
        
        return result
    
    def transcribe_chunk(
        self,
        audio_path: str,
        time_offset: float = 0.0,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> Tuple[List[dict], Optional[str]]:
        """
        Transcribe an audio chunk and apply time offset to segments.
        
        Args:
            audio_path: Path to the chunk audio file
            time_offset: Time offset to add to all segment timestamps
            progress_callback: Callback for progress updates
            
        Returns:
            Tuple of (segments with adjusted timestamps, detected language)
        """
        segments, language = self.transcribe(audio_path, progress_callback=progress_callback)
        
        # Apply time offset to segments
        if time_offset > 0:
            for seg in segments:
                seg["start"] += time_offset
                seg["end"] += time_offset
        
        return segments, language
    
    def translate(
        self,
        audio_path: str,
        target_language: str,
        ffmpeg_path: Optional[str] = None,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> List[dict]:
        """
        Translate audio to English using Whisper's translation task.
        
        Note: Whisper can only translate TO English, not to other languages.
        For other target languages, use external translation after transcription.
        
        Args:
            audio_path: Path to audio file
            target_language: Target language (only "en" supported natively)
            ffmpeg_path: Unused, kept for API compatibility
            progress_callback: Callback for progress updates
            
        Returns:
            List of translated segments
        """
        try:
            if target_language.lower() not in ["en", "english"]:
                print(f"Warning: Whisper can only translate to English. "
                      f"Use external translation for '{target_language}'.")
                # Fall back to transcription for external translation
                segments, _ = self.transcribe(audio_path, progress_callback=progress_callback)
                return segments
            
            print(f"Translating audio to English: {audio_path}")
            
            segments_gen, info = self.model.transcribe(
                audio_path,
                task="translate",
                beam_size=5,
                vad_filter=True,
            )
            
            segments = []
            for segment in segments_gen:
                segments.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip(),
                })
            
            if progress_callback:
                progress_callback(80)
            
            print(f"Translation complete: {len(segments)} segments")
            return segments
            
        except Exception as e:
            print(f"Error during translation: {e}")
            return []


# Fallback to standard Whisper if faster-whisper not available
def get_recognizer(
    model_size: str = "turbo",
    language: Optional[str] = None,
    prefer_faster: bool = True,
) -> "FasterWhisperRecognizer":
    """
    Factory function to get the appropriate recognizer.
    
    Tries faster-whisper first if available and preferred,
    falls back to standard Whisper otherwise.
    """
    if FASTER_WHISPER_AVAILABLE and prefer_faster:
        return FasterWhisperRecognizer(model_size=model_size, language=language)
    else:
        # Import and return legacy recognizer
        # This maintains backward compatibility
        raise ImportError(
            "faster-whisper not available and no fallback configured. "
            "Install with: pip install faster-whisper"
        )
