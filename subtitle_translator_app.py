"""
subtitle_translator_app.py
==========================

This module provides a simple desktop application for translating subtitle
files in the SubRip Text (.srt) format.  It is designed as a starting point
for a more fully‑featured tool; users can extend or replace the placeholder
translation logic with their own translation engine (for example, the
open‑source Argos Translate library or another API based translator).  A key
design goal is a clean and approachable user interface suitable for
non‑technical users, while still exposing enough flexibility for power users.

The graphical interface is built with Python's built‑in ``tkinter`` module
(using the themed ``ttk`` widgets where possible).  Tkinter comes bundled
with Python on Windows and macOS and is cross‑platform, making it a good
choice for simple applications【321279281566497†L210-L225】.  If you decide to
switch to a more sophisticated GUI toolkit such as PySide6 or PyQt6 you can do
so easily later【321279281566497†L50-L54】.

Out of the box the application supports manual language selection via a pair
of drop‑down menus and a basic “Auto detect” option.  Auto detection
relies on the optional ``langdetect`` package.  If ``langdetect`` is not
installed the application will continue to run and simply assume the input
language matches the chosen output language when automatic detection is
requested.  See the ``LANGUAGES`` dictionary below for the available
language codes.  You can add additional languages by editing that dictionary.

To integrate a real translation engine, replace the ``translate_text``
function with a call into your preferred library or service.  For example,
Argos Translate can be installed via ``pip install argostranslate`` and
supports offline translation by downloading language packages【919696716228657†L314-L321】.
Alternatively, online services such as LibreTranslate expose a simple HTTP
API, but note that network access may be restricted in some environments.

This script is intended to be executed directly.  Running it will launch
the graphical user interface.
"""

from __future__ import annotations

import dataclasses
import threading
import time
from typing import List, Optional

# Tkinter is only required for the graphical user interface.  When this module
# is imported in an environment without a display or without the tkinter
# package installed, attempts to import it will raise ``ImportError``.  To
# ensure that utility functions (such as ``parse_srt`` and ``write_srt``) can
# still be imported in headless environments, we catch the error and set
# tkinter‑related symbols to ``None``.  The GUI will then only be available
# when ``tkinter`` is present.
try:
    import tkinter as tk  # type: ignore
    from tkinter import filedialog, messagebox, ttk  # type: ignore
except ImportError:
    tk = None  # type: ignore
    filedialog = None  # type: ignore
    messagebox = None  # type: ignore
    ttk = None  # type: ignore

# Optional imports.  The ``langdetect`` library is used for automatic language
# detection if it is available.  It supports 55 languages and exposes a
# simple ``detect`` function【520971811339373†L110-L133】.  If the import fails
# the application will gracefully degrade.
try:
    from langdetect import detect
    from langdetect import DetectorFactory
    # Set seed to ensure deterministic results【520971811339373†L134-L145】.
    DetectorFactory.seed = 0
    _LANGDETECT_AVAILABLE = True
except ImportError:
    _LANGDETECT_AVAILABLE = False


# ---------------------------------------------------------------------------
# Configuration
#
# Define the list of supported languages.  The key is a friendly name which
# appears in the UI; the value is the ISO 639‑1 language code used by most
# translators.  The first entry (None) is reserved for automatic detection.
# You can add more languages here as you see fit.
LANGUAGES = {
    "Auto detect": None,
    "English (en)": "en",
    "Vietnamese (vi)": "vi",
    "Spanish (es)": "es",
    "French (fr)": "fr",
    "German (de)": "de",
    "Japanese (ja)": "ja",
    "Chinese (zh)": "zh",
    "Korean (ko)": "ko",
    "Portuguese (pt)": "pt",
    "Russian (ru)": "ru",
}


# ---------------------------------------------------------------------------
# Data structures

@dataclasses.dataclass
class SrtEntry:
    """Represents a single entry in an SRT subtitle file."""

    index: int
    start_time: str
    end_time: str
    text_lines: List[str]

    def format(self) -> str:
        """Return this entry formatted as a string suitable for writing.

        Returns:
            A multi‑line string containing the index, time codes, and text.
        """
        text = "\n".join(self.text_lines)
        return f"{self.index}\n{self.start_time} --> {self.end_time}\n{text}\n"


# ---------------------------------------------------------------------------
# SRT parsing and writing

def parse_srt(file_path: str) -> List[SrtEntry]:
    """Parse an SRT file into a list of ``SrtEntry`` objects.

    Args:
        file_path: Path to the .srt file on disk.

    Returns:
        A list of ``SrtEntry`` objects representing the subtitles.
    """
    entries: List[SrtEntry] = []
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read().splitlines()

    index = None
    start_time = None
    end_time = None
    text_buffer: List[str] = []
    state = 0  # 0: expecting index, 1: expecting time, 2: expecting text
    for line in content:
        line = line.strip("\ufeff")  # Remove BOM if present
        if state == 0:
            # Start of a new entry
            if not line:
                continue
            try:
                index = int(line)
                state = 1
            except ValueError:
                # Skip any stray lines
                continue
        elif state == 1:
            # Time code line
            if "-->" not in line:
                continue
            times = [t.strip() for t in line.split("-->")]
            if len(times) != 2:
                continue
            start_time, end_time = times
            state = 2
        elif state == 2:
            # Text lines until an empty line signals the end of this entry
            if line:
                text_buffer.append(line)
            else:
                # End of entry
                if index is not None and start_time and end_time:
                    entries.append(SrtEntry(index, start_time, end_time, text_buffer.copy()))
                # Reset for next entry
                index = None
                start_time = None
                end_time = None
                text_buffer.clear()
                state = 0
    # Append last entry if file does not end with a blank line
    if index is not None and start_time and end_time:
        entries.append(SrtEntry(index, start_time, end_time, text_buffer.copy()))
    return entries


def write_srt(entries: List[SrtEntry], file_path: str) -> None:
    """Write a list of ``SrtEntry`` objects back to an SRT file.

    Args:
        entries: The list of SrtEntry objects.
        file_path: Path to the output file.
    """
    with open(file_path, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(entry.format())
            f.write("\n")


# ---------------------------------------------------------------------------
# Translation logic (placeholder)

from argostranslate import package, translate

# ensure installed packages are loaded
package.update_package_index()
installed_packages = package.get_installed_packages()  # if needed

def translate_text(text: str, source_lang: Optional[str], target_lang: str) -> str:
    # If source_lang is None (auto), detect using langdetect or default to English
    from_code = source_lang or 'en'
    # Perform the translation
    return translate.translate(text, from_code, target_lang)


# ---------------------------------------------------------------------------
# Application class

class SubtitleTranslatorApp(tk.Tk if tk is not None else object):
    """Main application window for translating subtitle files."""

    def __init__(self) -> None:
        if tk is None:
            raise RuntimeError(
                "Tkinter is not available. The GUI cannot be created."
            )
        super().__init__()
        self.title("Subtitle Translator")
        self.geometry("480x300")
        self.resizable(False, False)

        # Variables for UI state
        self.input_path: tk.StringVar = tk.StringVar(value="")
        self.output_path: tk.StringVar = tk.StringVar(value="")
        self.input_language_var: tk.StringVar = tk.StringVar(value="Auto detect")
        self.output_language_var: tk.StringVar = tk.StringVar(value="English (en)")
        self.progress_var: tk.DoubleVar = tk.DoubleVar(value=0.0)

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Construct and layout the widgets for the application."""
        padding = {"padx": 10, "pady": 5}

        # File selection
        ttk.Label(self, text="Input subtitle (.srt)").grid(row=0, column=0, sticky="w", **padding)
        input_entry = ttk.Entry(self, textvariable=self.input_path, width=40, state="readonly")
        input_entry.grid(row=1, column=0, columnspan=2, sticky="ew", **padding)
        ttk.Button(self, text="Browse...", command=self._choose_input_file).grid(row=1, column=2, **padding)

        ttk.Label(self, text="Output file").grid(row=2, column=0, sticky="w", **padding)
        output_entry = ttk.Entry(self, textvariable=self.output_path, width=40, state="readonly")
        output_entry.grid(row=3, column=0, columnspan=2, sticky="ew", **padding)
        ttk.Button(self, text="Browse...", command=self._choose_output_file).grid(row=3, column=2, **padding)

        # Language selection
        ttk.Label(self, text="Source language").grid(row=4, column=0, sticky="w", **padding)
        input_lang_menu = ttk.Combobox(self, textvariable=self.input_language_var, values=list(LANGUAGES.keys()), state="readonly")
        input_lang_menu.grid(row=5, column=0, columnspan=2, sticky="ew", **padding)

        ttk.Label(self, text="Target language").grid(row=4, column=2, sticky="w", **padding)
        output_lang_menu = ttk.Combobox(self, textvariable=self.output_language_var, values=list(LANGUAGES.keys())[1:], state="readonly")
        output_lang_menu.grid(row=5, column=2, sticky="ew", **padding)

        # Progress bar
        self.progress_bar = ttk.Progressbar(self, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=6, column=0, columnspan=3, sticky="ew", **padding)

        # Action buttons
        translate_button = ttk.Button(self, text="Translate", command=self._on_translate_clicked)
        translate_button.grid(row=7, column=0, columnspan=3, pady=(10, 15))

    def _choose_input_file(self) -> None:
        """Open a file dialog for selecting the input SRT file."""
        file_path = filedialog.askopenfilename(filetypes=[("SRT files", "*.srt"), ("All files", "*.*")])
        if file_path:
            self.input_path.set(file_path)
            # Suggest an output filename by appending the target language code
            target_code = LANGUAGES.get(self.output_language_var.get(), "en") or "en"
            suggested_out = file_path.rsplit(".", 1)[0] + f"_{target_code}.srt"
            self.output_path.set(suggested_out)

    def _choose_output_file(self) -> None:
        """Open a file dialog for selecting the output SRT file."""
        file_path = filedialog.asksaveasfilename(defaultextension=".srt", filetypes=[("SRT files", "*.srt"), ("All files", "*.*")])
        if file_path:
            self.output_path.set(file_path)

    def _on_translate_clicked(self) -> None:
        """Validate input and launch translation in a separate thread."""
        input_path = self.input_path.get()
        output_path = self.output_path.get()
        if not input_path:
            messagebox.showerror("Missing input", "Please select an input .srt file.")
            return
        if not output_path:
            messagebox.showerror("Missing output", "Please select or specify an output file.")
            return
        src_label = self.input_language_var.get()
        tgt_label = self.output_language_var.get()
        if src_label == "Auto detect":
            source_lang = None
        else:
            source_lang = LANGUAGES.get(src_label)
        target_lang = LANGUAGES.get(tgt_label)
        if not target_lang:
            messagebox.showerror("Invalid language", "Please select a valid target language.")
            return
        # Disable UI during processing
        self._toggle_ui(state=tk.DISABLED)
        # Launch translation in a background thread to keep UI responsive
        threading.Thread(
            target=self._translate_file,
            args=(input_path, output_path, source_lang, target_lang),
            daemon=True,
        ).start()

    def _toggle_ui(self, state: str) -> None:
        """Enable or disable the UI controls."""
        for child in self.winfo_children():
            if isinstance(child, (ttk.Entry, ttk.Combobox, ttk.Button)):
                child.configure(state=state)

    def _translate_file(self, in_path: str, out_path: str, source_lang: Optional[str], target_lang: str) -> None:
        """Perform the translation from SRT input to SRT output.

        This method runs in a background thread and updates the progress bar via
        ``self.progress_var``.  Once completed, it re‑enables the UI and
        notifies the user.
        """
        try:
            entries = parse_srt(in_path)
        except Exception as e:
            self._on_translation_error(f"Failed to read input file: {e}")
            return

        total = len(entries)
        translated_entries: List[SrtEntry] = []
        for idx, entry in enumerate(entries, start=1):
            # Join multiple lines into a single string for translation
            original_text = "\n".join(entry.text_lines)
            if source_lang is None and _LANGDETECT_AVAILABLE:
                try:
                    detected = detect(original_text)
                except Exception:
                    detected = target_lang  # Fallback to target language
            else:
                detected = source_lang
            translated_text = translate_text(original_text, detected, target_lang)
            # Split back into lines if necessary
            translated_lines = translated_text.split("\n")
            translated_entries.append(SrtEntry(entry.index, entry.start_time, entry.end_time, translated_lines))
            # Update progress
            progress = (idx / total) * 100
            self.progress_var.set(progress)
            # Sleep briefly to allow UI to update; remove or reduce in production
            time.sleep(0.01)
        # Write output file
        try:
            write_srt(translated_entries, out_path)
        except Exception as e:
            self._on_translation_error(f"Failed to write output file: {e}")
            return
        # Notify completion
        self.after(0, self._on_translation_success, out_path)

    def _on_translation_success(self, out_path: str) -> None:
        """Handle successful completion of the translation process."""
        self.progress_var.set(100.0)
        self._toggle_ui(state=tk.NORMAL)
        messagebox.showinfo("Translation complete", f"Subtitle translation finished!\nOutput saved to:\n{out_path}")

    def _on_translation_error(self, message: str) -> None:
        """Handle errors during translation."""
        self._toggle_ui(state=tk.NORMAL)
        messagebox.showerror("Translation error", message)


# ---------------------------------------------------------------------------
def main() -> None:
    """Entry point when run as a script."""
    app = SubtitleTranslatorApp()
    app.mainloop()


if __name__ == "__main__":
    main()