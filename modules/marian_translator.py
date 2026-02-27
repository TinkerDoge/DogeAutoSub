"""
MarianMT translation engine for offline translation.
Extracted from AutoUI.py for cleaner code organization.
"""

import os
import sys
from typing import Callable, List, Optional

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

# Check for MarianMT availability
try:
    if sys.version_info < (3, 8):
        raise ImportError("Python 3.8+ required for transformers")
    
    from transformers import MarianMTModel, MarianTokenizer
    import transformers
    
    transformers_version = tuple(map(int, transformers.__version__.split('.')[:2]))
    if transformers_version < (4, 20):
        print(f"Warning: transformers version {transformers.__version__} may not be fully compatible. Recommended: 4.20+")
    
    MARIAN_AVAILABLE = True
    print(f"MarianMT available with transformers v{transformers.__version__}")

except ImportError as e:
    MARIAN_AVAILABLE = False
    print(f"MarianMT not available: {e}")


class MarianTranslator:
    """MarianMT translation engine for offline translation."""
    
    def __init__(self, src_lang: str, tgt_lang: str):
        if not MARIAN_AVAILABLE:
            raise ImportError("MarianMT requires transformers library and Python 3.8+")
        
        self.src_lang = src_lang
        self.tgt_lang = tgt_lang
        self.model = None
        self.tokenizer = None
        self._pipeline = None
        self.tgt_token = None
        self._fallback_pipeline = None
        self._fallback_model_name = None
        
        self.lang_mapping = {
            'en': 'en', 'vi': 'vi', 'zh': 'zh', 'ja': 'ja',
            'ko': 'ko', 'fr': 'fr', 'de': 'de', 'es': 'es',
            'it': 'it', 'pt': 'pt', 'ru': 'ru', 'ar': 'ar',
        }
    
    def _get_model_name(self) -> str:
        """Get the appropriate MarianMT model name for the language pair."""
        src = self.lang_mapping.get(self.src_lang, self.src_lang)
        tgt = self.lang_mapping.get(self.tgt_lang, self.tgt_lang)
        return f"Helsinki-NLP/opus-mt-{src}-{tgt}"

    def _get_fallback_model_name(self) -> str:
        tgt = self.lang_mapping.get(self.tgt_lang, self.tgt_lang)
        return f"Helsinki-NLP/opus-mt-mul-{tgt}"
    
    def load_model(self, progress_callback: Optional[Callable] = None) -> bool:
        """Load the MarianMT model and tokenizer."""
        try:
            model_name = self._get_model_name()
            print(f"Loading MarianMT model: {model_name}")
            
            if progress_callback:
                progress_callback(0.1)
            
            cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "marian_cache")
            
            self.tokenizer = MarianTokenizer.from_pretrained(model_name, cache_dir=cache_dir)
            
            if progress_callback:
                progress_callback(0.5)
            
            self.model = MarianMTModel.from_pretrained(model_name, cache_dir=cache_dir)
            
            if progress_callback:
                progress_callback(0.8)
            
            # Move to GPU if available
            if TORCH_AVAILABLE and torch.cuda.is_available():
                try:
                    self.model = self.model.to('cuda')
                    print("MarianMT model moved to GPU")
                except RuntimeError as e:
                    print(f"Failed to move model to GPU: {e}, using CPU")
            
            # Set forced BOS token for target language
            self._setup_target_token()
            
            if progress_callback:
                progress_callback(1.0)
            
            print("MarianMT model loaded successfully")
            return True
            
        except Exception as e:
            print(f"Failed to load MarianMT model: {e}")
            return self._try_fallback_model()
    
    def _setup_target_token(self):
        """Configure forced BOS token for target language."""
        try:
            tgt = self.lang_mapping.get(self.tgt_lang, self.tgt_lang)
            special = f">>{tgt}<<"
            token_id = None
            try:
                token_id = self.tokenizer.convert_tokens_to_ids(special)
            except Exception:
                token_id = None
            
            if isinstance(token_id, int) and token_id >= 0 and token_id != getattr(self.tokenizer, 'unk_token_id', -1):
                self.model.config.forced_bos_token_id = token_id
                self.tgt_token = special
                print(f"Set forced_bos_token_id: '{special}' -> id {token_id}")
            elif hasattr(self.tokenizer, 'lang_code_to_id') and tgt in getattr(self.tokenizer, 'lang_code_to_id', {}):
                self.model.config.forced_bos_token_id = self.tokenizer.lang_code_to_id[tgt]
                print(f"Set forced_bos_token_id via lang_code_to_id for '{tgt}'")
        except Exception as e:
            print(f"Could not set forced_bos_token_id: {e}")
    
    def _try_fallback_model(self) -> bool:
        """Try loading a multilingual fallback model."""
        try:
            fallback_model = self._get_fallback_model_name()
            print(f"Trying fallback model: {fallback_model}")
            
            self.tokenizer = MarianTokenizer.from_pretrained(fallback_model)
            self.model = MarianMTModel.from_pretrained(fallback_model)
            
            if TORCH_AVAILABLE and torch.cuda.is_available():
                try:
                    self.model = self.model.to('cuda')
                except RuntimeError:
                    pass
            
            print("Fallback MarianMT model loaded successfully")
            return True
        except Exception as e2:
            print(f"Fallback model also failed: {e2}")
            return False
    
    def translate_batch(self, texts: List[str], batch_size: int = 4, progress_cb: Optional[Callable] = None) -> List[str]:
        """Translate a batch of texts with pipeline-first approach and fallbacks."""
        if not self.model or not self.tokenizer:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        translated = []

        if TORCH_AVAILABLE and not torch.cuda.is_available():
            batch_size = min(batch_size, 2)

        def _norm(t: str) -> str:
            return (t or "").strip().lower()

        def _apply_target_prefix(batch_list):
            if self.tgt_token:
                try:
                    tid = self.tokenizer.convert_tokens_to_ids(self.tgt_token)
                    if isinstance(tid, int) and tid >= 0 and tid != getattr(self.tokenizer, 'unk_token_id', -1):
                        return [f"{self.tgt_token} {t}" if t else self.tgt_token for t in batch_list]
                except Exception:
                    pass
            return batch_list

        def _pipeline_translate(batch_list, model_name_override=None):
            try:
                from transformers import pipeline
                if model_name_override is None:
                    if self._pipeline is None:
                        src = self.lang_mapping.get(self.src_lang, self.src_lang)
                        tgt = self.lang_mapping.get(self.tgt_lang, self.tgt_lang)
                        task = f"translation_{src}_to_{tgt}"
                        mn = self._get_model_name()
                        device = 0 if (TORCH_AVAILABLE and torch.cuda.is_available() and next(self.model.parameters()).is_cuda) else -1
                        try:
                            self._pipeline = pipeline(task, model=mn, device=device)
                        except Exception:
                            self._pipeline = pipeline("translation", model=mn, device=device)
                    results = self._pipeline(batch_list, clean_up_tokenization_spaces=True)
                else:
                    if self._fallback_pipeline is None:
                        device = 0 if (TORCH_AVAILABLE and torch.cuda.is_available()) else -1
                        try:
                            self._fallback_pipeline = pipeline("translation", model=model_name_override, device=device)
                        except Exception:
                            src = self.lang_mapping.get(self.src_lang, self.src_lang)
                            tgt = self.lang_mapping.get(self.tgt_lang, self.tgt_lang)
                            task = f"translation_{src}_to_{tgt}"
                            self._fallback_pipeline = pipeline(task, model=model_name_override, device=device)
                    results = self._fallback_pipeline(batch_list, clean_up_tokenization_spaces=True)
                return [r.get('translation_text', '') for r in results]
            except Exception as e:
                print(f"Pipeline translate failed: {e}")
                return [""] * len(batch_list)

        def _generate_translate(batch_list, beams=2):
            inputs = self.tokenizer(
                batch_list,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512,
            )
            if TORCH_AVAILABLE and torch.cuda.is_available() and next(self.model.parameters()).is_cuda:
                inputs = {k: v.to('cuda') for k, v in inputs.items()}
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=512,
                    num_beams=beams,
                    early_stopping=True,
                    do_sample=False,
                )
            return self.tokenizer.batch_decode(outputs, skip_special_tokens=True)

        total = max(1, len(texts))
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_pref = _apply_target_prefix(batch)
            try:
                batch_translated = _pipeline_translate(batch_pref)
                
                # Detect identity translations
                try:
                    same_count = sum(1 for src, tgt in zip(batch, batch_translated) if _norm(src) == _norm(tgt))
                except Exception:
                    same_count = 0
                
                if same_count >= max(2, int(0.6 * len(batch))):
                    print("Identity translations detected; falling back to generate()")
                    batch_translated = _generate_translate(batch_pref, beams=2)
                    try:
                        same_count2 = sum(1 for src, tgt in zip(batch, batch_translated) if _norm(src) == _norm(tgt))
                    except Exception:
                        same_count2 = 0
                    if same_count2 >= max(2, int(0.6 * len(batch))):
                        print("Still identity; trying multilingual fallback")
                        fb_name = self._fallback_model_name or self._get_fallback_model_name()
                        self._fallback_model_name = fb_name
                        batch_translated = _pipeline_translate(batch_pref, model_name_override=fb_name)
                
                translated.extend(batch_translated)
                
                if progress_cb:
                    try:
                        progress_cb(min(1.0, (i + len(batch)) / total))
                    except Exception:
                        pass
                        
            except RuntimeError as e:
                if "out of memory" in str(e).lower():
                    print(f"GPU OOM; falling back to CPU for batch {i}")
                    if TORCH_AVAILABLE and torch.cuda.is_available():
                        self.model = self.model.to('cpu')
                        torch.cuda.empty_cache()
                    batch_translated = _generate_translate(batch_pref, beams=1)
                    try:
                        same_count = sum(1 for src, tgt in zip(batch, batch_translated) if _norm(src) == _norm(tgt))
                    except Exception:
                        same_count = 0
                    if same_count >= max(2, int(0.8 * len(batch))):
                        batch_translated = _pipeline_translate(batch_pref)
                    translated.extend(batch_translated)
                    if progress_cb:
                        try:
                            progress_cb(min(1.0, (i + len(batch)) / total))
                        except Exception:
                            pass
                else:
                    raise e

        return translated
