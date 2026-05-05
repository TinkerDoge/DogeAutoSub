# DogeAutoSub — Win95-Modernized Redesign

**Date:** 2026-05-05
**Scope:** Frontend redesign of `AutoUI.py` + `modules/ui_DogeAutoSub.py` + theme stylesheets, plus new logging panel, mascot widget, animations, and boot splash. Backend logic (subtitle/notes/translate threads, MLAAS client, updater) is unchanged except for added log signal emissions.

---

## 1. Goals

1. Make the UI feel cleaner, neater, and more modern while keeping the retro and doge personality of the app.
2. Land on a coherent visual system: Windows 95/98-inspired chrome, modernized interior.
3. Improve runtime feedback: replace the single status line with a step-pipeline timeline plus a collapsible terminal-style console, and persist logs to disk.
4. Add expressive animations: mascot state machine, micro-interactions, completion celebration, error shake, phase-aware loading visuals, retro boot splash.
5. Ship in three independently testable phases (Skin → Logging → Animation) with no functional regressions.

## 2. Non-Goals

- Rewriting any backend module (whisper engine, MLAAS, updater).
- Adding new product features (new tabs, new pipelines, new export formats).
- Going fully frameless / custom-titlebar — native window frame stays.
- Localization, accessibility audit beyond a `reduce_motion` toggle.

## 3. Decisions Already Made

| Question | Decision |
|---|---|
| Visual direction | Windows 95/98 modernized (beveled chrome + title bar + tabs, but softer shadows, slight rounding, white content cards inside grey frame) |
| Logging style | Hybrid: top step-timeline + bottom collapsible terminal console |
| Animations | All six: mascot states, UI micro-interactions, completion celebration, error shake, smarter phase-aware loading visuals, retro boot splash |
| Implementation | Phased rollout: A Skin → B Logging → C Animation |
| Window size | 720 × 1080, fixed (non-resizable) |

## 4. Visual System (Phase A)

### 4.1 Window frame

- Outer backdrop colour: teal `#2a8e8e`.
- Main panel: `#d4d0c8` background, 1px bevel border (top/left `#ffffff`, bottom/right `#707070`), 4px corner radius, 0 4px 14px rgba(0,0,0,0.25) drop shadow.
- Cosmetic title bar: gradient `linear-gradient(90deg, #0a246a, #3a6ea5)`, 12px white bold text "🐕 DogeAutoSub — v{APP_VERSION}", with `_` and `×` chrome buttons rendered for visual fidelity. Native window controls remain authoritative — these are decorative.
- Cosmetic menu bar: "File · Edit · View · Help" rendered below the title bar. Only "View" is functionally wired (settings popover) in Phase C; the rest are inert decoration.

### 4.2 Tabs

- `QTabWidget` restyled. Tab height 28px, 12px font weight 600. Beveled top corners, selected tab merges into pane with `border-bottom: 2px solid #ece9d8` overlap.
- Three tabs: 📝 Subtitles · 📋 Meeting Notes · 🌐 Translate.

### 4.3 Interior

- Tab pane background `#ece9d8` (Luna-era beige).
- Cards: white `#ffffff` background, 1px `#a0a0a0` border, 4px radius, 12px padding, `inset 0 1px 0 #f8f8f8` highlight.
- Section headers inside cards: 11px uppercase, 0.5px letter-spacing, color `#505050`, with emoji icon prefix preserved.
- Spacing: 14px page padding, 10px between cards, 8px inside cards.

### 4.4 Typography

- Font stack: `"Pixelated MS Sans Serif", "MS Sans Serif", Tahoma, "Segoe UI", system-ui, sans-serif`.
- Body 12px, labels 11px uppercase tracked, monospace `"Consolas", "Courier New", monospace` for the log console only.

### 4.5 Color tokens (defined as Python dict in a new `modules/theme_tokens.py`)

| Token | Light | Dark |
|---|---|---|
| `chrome_bg` | `#d4d0c8` | `#3a3a3a` |
| `interior_bg` | `#ece9d8` | `#1e1e1e` |
| `card_bg` | `#ffffff` | `#2a2a2a` |
| `card_border` | `#a0a0a0` | `#505050` |
| `title_bar` | `#0a246a → #3a6ea5` | `#000040 → #1a3a6a` |
| `desktop_bg` | `#2a8e8e` | `#1a4040` |
| `text_primary` | `#202020` | `#e0e0e0` |
| `text_secondary` | `#505050` | `#a0a0a0` |
| `text_muted` | `#808080` | `#707070` |
| `accent_primary` | `#1854b0` | `#4a8eea` |
| `accent_success` | `#7ed957` | `#7ed957` |
| `accent_warn` | `#ffd166` | `#ffd166` |
| `accent_error` | `#e63946` | `#ff6b6b` |

Stylesheet files (`modules/styleSheetDark.css`, `modules/styleSheetLight.css`) are regenerated from these tokens.

### 4.6 Buttons

- Default: `linear-gradient(180deg, #ffffff, #d4d0c8)`, 1px `#707070` border, 3px radius, `inset 0 1px 0 #ffffff` + `0 1px 2px rgba(0,0,0,0.1)` shadow. On press, gradient inverts and shadow flattens.
- Primary (START PROCESSING, Generate Notes, Translate File): solid blue `#1854b0` with darker bottom edge for the bevel feel, white text.
- Icon-only (theme toggle, open folder, chrome buttons): 28px × 28px, transparent until hover.

### 4.7 Inputs

- `QComboBox`, `QLineEdit`: white background, 1px `#a0a0a0` inset border (Win95 sunken look), 3px radius, 11px font.
- `QSlider`: blue gradient sub-page, 14px circular handle with 1px bevel.
- `QProgressBar`: `#e8e4d8` track, 8px radius, blue gradient chunk, 10px height (slimmer than current 14px). Animated shimmer overlay (Phase C).

### 4.8 Tooltips, scrollbars, dialogs

- Tooltips: light beige `#ffffe1` background, 1px `#707070` border, 11px MS Sans Serif (matches Win95 native tooltips).
- Scrollbars: 14px wide, beveled grey thumb on light track. Native arrow buttons at top/bottom.
- `QMessageBox` inherits the global stylesheet automatically.

## 5. Layout & Window Structure (Phase A)

### 5.1 Window

- `QMainWindow`, fixed 720 × 1080, native frame.
- Window title: `DogeAutoSub v{APP_VERSION}` (unchanged).

### 5.2 Top bar (replaces today's `headerLayout`)

- Container: `QFrame#fauxTitleBar` styled as the gradient title bar.
- Left: doge favicon + bold app title + version badge (`#a0c0e0` faded).
- Right: chrome buttons row (`_` minimize, `□` maximize, `×` close) rendered for visual fidelity only. They are inert decoration — the native OS title bar (still present, since we keep the native frame) handles real window operations. Existing `themeBtn` and `openFolderBtn` move into a small toolstrip just below the menu bar instead of the title bar.

### 5.3 Cosmetic menu bar

- `QFrame#menuBar` 22px tall, beige background, "File · Edit · View · Help" labels with hover highlight.
- Phase C: clicking "View" opens a small `QMenu` with Reduce Motion / Mute Sounds / Show Doge Tips toggles.

### 5.4 Subtitles tab

Cards in order:

1. **Input / Output card** — fieldset legend "📁 Input / Output". Two beveled buttons (Select Video / Output Folder) on one row, file path label below. No structural change versus today; cosmetics only.
2. **Settings card** — fieldset legend "⚙️ Settings". 2×2 grid:
   - Row 1: Source Lang | Target Lang
   - Row 2: Engine | Volume Boost (slider + numeric label)
   - Below: nested MLAAS API mini-card (status dot + bearer token QLineEdit + "Get Token" button), unchanged behavior.
3. **Action card** — START PROCESSING button (full width, primary), progress bar, status row (label + ETA), then `LogPanel` widget, then mascot strip.
4. **Mascot strip** — 130px tall card containing `MascotWidget` on the left and a transparent `QLabel#speechBubble` area on the right that materializes when the mascot speaks.

Hidden widgets retained for backend compatibility (`model_size_dropdown`, `VRamUsage`, `rSpeed`, `llmApiUrl`, `llmApiKey`, `llmModelName`): same widget names, same signals, `setVisible(False)`.

### 5.5 Notes tab

Same fieldset/card pattern. Cards:

1. **Transcript card** — Upload DOCX button + path label.
2. **Info banner** — "ℹ️ Uses MLAAS API token from Subtitles tab."
3. **Generate / Output card** — Generate + Save buttons, status label, `QTextEdit` output. Uses LogPanel in Phase B.

### 5.6 Translate tab

1. **Source file card.**
2. **Settings card** — Source Lang | Target Lang | Engine.
3. **Translate / Output card** — Translate + Save buttons, status label, output `QTextEdit`. Uses LogPanel in Phase B.

## 6. LogPanel Widget (Phase B)

### 6.1 File and class

- New module `modules/log_panel.py`.
- New class `LogPanel(QFrame)`.

### 6.2 Public API

```python
def set_pipeline(self, steps: list[str]) -> None
def step_start(self, step: str) -> None
def step_done(self, step: str, detail: str = "") -> None
def step_error(self, step: str, detail: str = "") -> None
def log(self, level: str, text: str) -> None
def clear(self) -> None
```

`level` ∈ `{"info", "success", "warn", "error", "doge"}`.

### 6.3 Internal layout

- Top: timeline as a custom `QWidget` painting one row per step. Row contents: status dot + step name (bold when active) + duration/detail (right-aligned greyed) + timestamp on far right. Active row gets `#fffbe5` background, pending rows greyed at 0.5 opacity.
- Bottom: `QPlainTextEdit` (read-only, monospace, 9.5px, dark `#0c0c0c` background). Line color set per `level` via `QTextCharFormat`. Auto-scroll to bottom; pause auto-scroll when user scrolls up, resume when user scrolls back to bottom.
- Toggle: a small clickable `QLabel` "▼ Show details / ▲ Hide details" between the two regions. Console region collapses; timeline always visible. State persisted in `QSettings("DogeAutoSub", "ui").value("log/console_open", True)`.

### 6.4 Pipeline definitions

Constants in `modules/log_panel.py`:

```python
PIPELINE_SUBTITLES = ["Load model", "Extract audio", "Transcribe", "Translate", "Save SRT"]
PIPELINE_NOTES     = ["Read transcript", "Summarize", "Format"]
PIPELINE_TRANSLATE = ["Read file", "Detect language", "Translate", "Format output"]
```

The owning UI calls `log_panel.set_pipeline(PIPELINE_SUBTITLES)` before starting work.

### 6.5 Wiring threads

Each existing thread keeps its current signals (`status_update`, `progress_update`, `task_start`, `task_complete`, etc.) and gains one additional signal:

```python
log_event = Signal(dict)
# {"kind": "step_start"|"step_done"|"step_error"|"log",
#  "step": str | None,
#  "level": str | None,
#  "text": str | None,
#  "detail": str | None}
```

Touched files:

- `modules/subtitle_thread.py` — emit `step_start`/`step_done` around model load, ffmpeg extraction, per-chunk transcription, translation, SRT save. Existing `progress_update` stays as the source of truth for the progress bar.
- `modules/meeting_notes_thread.py` — same pattern around read / summarize / format stages.
- `modules/translate_thread.py` — same pattern around read / detect / translate / format stages.
- `modules/mlaas_client.py` — add a thin optional callback parameter `on_log: Callable[[str, str], None] | None = None` to `translate_segments_mlaas` and `summarize_text_mlaas`. Threads pass through their own bound emitter so MLAAS chatter (retries, rate limits, model fallbacks) lands in the console.

### 6.6 DogeNarrator

- Helper class inside `modules/log_panel.py`.
- On every Nth `step_done` (N = 2 by default) and on every overall task completion, posts a random short doge line as `level="doge"`: "such wow.", "much progress.", "very SRT.", "wow. so transcribe.", "many subtitles.", etc.
- Toggle: `QSettings` key `doge/tips_enabled`, default `True`. Wired to "View → Show Doge Tips" menu entry in Phase C.

### 6.7 Disk persistence

- New `modules/log_writer.py`: a singleton that writes every `LogPanel.log` line (and step events flattened to text) to `logs/dogeautosub-YYYYMMDD.log` in the app directory. Daily rotation; keeps last 7 files; older deleted on app start.
- Format: `[HH:MM:SS] [LEVEL] message`.

## 7. Animation System (Phase C)

### 7.1 New modules

- `modules/animations.py` — reusable helpers (no QObject subclassing where avoidable).
- `modules/mascot.py` — `MascotWidget` and `DogeStateMachine`.
- `modules/splash.py` — `BootSplash` widget.
- `modules/toast.py` — `Toast` notification widget.

### 7.2 MascotWidget (`modules/mascot.py`)

- States: `idle`, `idle_blink`, `thinking`, `working`, `celebrate`, `confused`, `sleepy`, `error`.
- Each state maps to `icons/mascot/<state>.gif`. Missing files fall back to existing `start.gif` (idle/sleepy), `loading.gif` (thinking/working), `done.jpg` (celebrate). Error/confused fall back to `start.gif` with a red tint applied via `QGraphicsColorizeEffect`. This means Phase C ships even before any new art exists.
- `set_state(name)` swaps the active `QMovie`.
- `say(text, ms=2500)`: shows a `QLabel#speechBubble` (beveled, white background, dark border, tail pointing left to mascot). Fade in 200ms, hold `ms`, fade out 200ms, then `deleteLater` the label. Multiple rapid `say` calls queue (FIFO) rather than overlap.
- Auto-transitions:
  - 60s idle with no `log_event` → `sleepy`.
  - During `working`, alternate between `thinking` and `working` every 8s for variety.
  - On any `step_done` → flash `celebrate` for 600ms then return to previous state.
  - On any `step_error` or `log_event.level == "error"` → `confused` for 3s.
- Subscribes to the `LogPanel.log_event` signal so behavior is automatic; no per-call bookkeeping in the main window.

### 7.3 Micro-interactions (`modules/animations.py`)

```python
def lift_on_hover(widget: QWidget, dy: int = 2, duration_ms: int = 120) -> None
def slide_tab(stack: QStackedWidget, direction: str = "left", duration_ms: int = 180) -> None
def pulse(target: QWidget, min_opacity: float = 0.45, max_opacity: float = 1.0, period_ms: int = 1200) -> QPropertyAnimation
def shimmer(progress_bar: QProgressBar, period_ms: int = 1600) -> QPropertyAnimation
```

- Button press depth comes from CSS `:pressed` pseudo-state; no Python helper required.
- `lift_on_hover` installs a `QObject` event filter on enter/leave events, animating `pos`. Used on cards inside Subtitles/Notes/Translate tabs.
- `slide_tab` connects to `QTabWidget.currentChanged`. Implemented via a `QGraphicsOpacityEffect` plus a `QPropertyAnimation` on `pos` (12px offset).
- `pulse` returns the animation so the caller can stop it. LogPanel uses this on the active timeline dot.
- `shimmer` animates a CSS gradient stop position on the progress bar's chunk by re-applying stylesheet on a QTimer tick (15 fps is enough, doesn't need 60).

### 7.4 Completion celebration

- `animations.confetti_burst(parent: QWidget) -> None`: spawns ~40 small `QLabel` particles (5×5 colored squares, plus 4 tiny pixel-doge sprites). Each particle gets a `QPropertyAnimation` group: outward velocity in random angle, gravity downward, opacity fade. Total duration 900ms, then particles `deleteLater()`.
- Status card flash: temporary stylesheet swap to green border + green-tinted background, reverted via `QTimer.singleShot(300)`.
- Optional sound: `QSoundEffect` plays `sounds/complete.wav` if present and `QSettings("sound/enabled")` is true (default true, mutable from View menu).
- Wired to `task_complete` signal of all three threads.

### 7.5 Error feedback

- `animations.shake(widget: QWidget, amplitude: int = 8, cycles: int = 3, duration_ms: int = 220) -> None`: animates `geometry` X offset back and forth.
- `Toast(parent, text, kind="error", duration_ms=4000)`: borderless `QFrame` child, slides in from top center, holds, slides out. Style differs by `kind` (`error` red, `warn` yellow, `info` blue, `success` green).
- Triggered on any `log_event.level == "error"` or `step_error`.

### 7.6 Phase-aware loading visuals

In `LogPanel`, the active timeline row's status dot is replaced with a small custom widget specific to that step:

- `Load model`: custom `QWidget` whose `paintEvent` rotates a gear icon, driven by a `QVariantAnimation` ticking the rotation angle every 33ms.
- `Extract audio` / `Save SRT`: animated disk icon (3-frame GIF).
- `Transcribe`: 12-bar audio waveform widget (`QWidget.paintEvent`, `QTimer` driving randomized bar heights at 30 fps).
- `Translate`: src-flag → arrow → dst-flag, arrow opacity pulses.
- `Read transcript` / `Read file` / `Detect language` / `Summarize` / `Format` / `Format output`: spinning gear (default fallback).

Each widget is a small `QWidget` subclass in `modules/animations.py`, ~60 LOC each. LogPanel chooses the widget by step name at `step_start` time, swapping it back to a static dot at `step_done`.

### 7.7 Boot splash (`modules/splash.py`)

- `BootSplash(QWidget)`, frameless, 360×220, Win95-styled mini window centered on primary screen.
- Shown immediately at `__main__` start, before importing `torch`, `whisper`, or constructing `DogeAutoSub`.
- Contents: doge logo, "DogeAutoSub v{APP_VERSION}", "loading…" with three animated dots, thin progress bar driven by milestones:
  - `import torch` → 25%
  - `import faster_whisper / whisper engine` → 60%
  - `DogeAutoSub.__init__` start → 85%
  - `__init__` done / window.show() → 100%, splash closes via `QPropertyAnimation` fade-out (200ms).
- Skippable on click (closes immediately).
- Honors `--no-splash` CLI flag (added to `AutoUI.py`'s arg parsing).

### 7.8 Reduce-motion / mute toggles

- `QSettings("DogeAutoSub", "ui")` keys:
  - `motion/reduce` (default false)
  - `sound/enabled` (default true)
  - `doge/tips_enabled` (default true)
- View menu (rendered as a small `QMenu` from the cosmetic "View" menu-bar item) lists these as checkable actions.
- All animation helpers in `modules/animations.py` early-return to instant transitions when `motion/reduce` is true.
- All sound playback in `modules/animations.py` and `modules/mascot.py` no-ops when `sound/enabled` is false.

## 8. Files Touched / Added

### Phase A — Skin

- **Modified:** `modules/ui_DogeAutoSub.py` (full layout rebuild, but same widget names/signals).
- **Modified:** `modules/styleSheetDark.css`, `modules/styleSheetLight.css` (regenerated from new tokens).
- **Modified:** `AutoUI.py` (window size, title bar wiring, no functional changes to threads).
- **Added:** `modules/theme_tokens.py` (color/spacing constants, single source of truth).

### Phase B — Logging

- **Added:** `modules/log_panel.py` (LogPanel widget + DogeNarrator).
- **Added:** `modules/log_writer.py` (disk log rotation).
- **Modified:** `modules/subtitle_thread.py`, `modules/meeting_notes_thread.py`, `modules/translate_thread.py` (add `log_event` signal + emissions; existing signals untouched).
- **Modified:** `modules/mlaas_client.py` (optional `on_log` callback parameter).
- **Modified:** `AutoUI.py` (instantiate LogPanel, connect `log_event` signals, set pipelines).

### Phase C — Animation

- **Added:** `modules/animations.py`, `modules/mascot.py`, `modules/splash.py`, `modules/toast.py`.
- **Added:** `icons/mascot/{idle,idle_blink,thinking,working,celebrate,confused,sleepy,error}.gif` — placeholders fall back to existing GIFs at runtime.
- **Optional asset:** `sounds/complete.wav` (graceful absent fallback).
- **Modified:** `AutoUI.py` (mount BootSplash before heavy imports, instantiate MascotWidget, wire view menu, hook `task_complete` to confetti, hook errors to shake/toast).
- **Modified:** `modules/ui_DogeAutoSub.py` (replace `statusImage` QLabel with `MascotWidget` placeholder; add cosmetic View menu wiring).

## 9. Phase Acceptance Criteria

### Phase A — Skin
- App launches at 720×1080 with Win95-style faux title bar, menu bar, tabs, beveled cards, and updated typography.
- Both Dark and Light themes render coherently.
- Every existing button, dropdown, slider, and progress bar still works exactly as before.
- All three tabs render their content in fieldset-styled cards. No layout overflow at 1080p screen height.
- No new runtime errors on cold start. `print` boot log unchanged.

### Phase B — Logging
- LogPanel appears under the action card in Subtitles/Notes/Translate tabs.
- Starting a subtitle run advances the 5-step timeline: each step changes from pending → active (animated) → done (with timing detail).
- Console shows time-stamped color-coded lines from threads and MLAAS client.
- Toggling "▼ Show details" hides/reveals the console; the choice persists across restarts.
- Log file `logs/dogeautosub-{YYYYMMDD}.log` is created with the same content; old files (>7 days) are pruned at startup.
- Doge tips appear in console at expected milestones; toggling off via View menu silences them immediately.

### Phase C — Animation
- Mascot reacts to events: thinking/working during runs, celebrate flash on each step, confused on errors, sleepy after 60s idle.
- Speech bubble appears, holds, fades out without overlapping.
- Card hover lifts; tab switch slides; active timeline dot pulses; progress bar shimmers.
- On task completion: confetti burst + green flash + (optional) chime. None block input or hang the UI thread.
- On error: window shake + error toast + mascot confused. No crashes when the same error fires repeatedly.
- Phase-aware loading visuals replace the static dot at the active timeline step, then revert on `step_done`.
- Boot splash shows on startup, advances through milestones, fades out when window appears, dismissible by click. `--no-splash` flag bypasses it entirely.
- Reduce Motion toggle short-circuits all animations to instant transitions; Mute toggle silences all sounds.

## 10. Risk Notes

- **GIF assets for mascot states:** new states (`idle_blink`, `confused`, `sleepy`, `celebrate`, `error`) require art that does not yet exist. Fallback to existing GIFs is built in so Phase C can ship; richer art can be added later without code changes.
- **Pixelated MS Sans Serif font:** likely not installed by default on Windows 11. Stack falls back to MS Sans Serif → Tahoma → system. Optional: bundle the font in `fonts/` and load via `QFontDatabase.addApplicationFont` at startup; deferred decision, not in this spec.
- **Frameless window not used:** keeping native frame avoids custom hit-test and keeps Aero Snap, Win+Arrow, multi-monitor DPI behavior. The faux title bar is purely cosmetic; the real window controls remain authoritative.
- **Confetti / shimmer perf:** all animations short-circuit when `motion/reduce` is true. Particle count capped at 40. No per-frame stylesheet thrash beyond the 15 fps shimmer.
- **Backwards compatibility:** all hidden widgets in `ui_DogeAutoSub.py` (`model_size_dropdown`, `VRamUsage`, `rSpeed`, `llmApiUrl`, `llmApiKey`, `llmModelName`) are retained with the same names and `setVisible(False)` so `AutoUI.py` requires no changes to those code paths.
- **Updater unaffected:** `modules/updater.py` and `releases/files/**` mirror is not touched by this spec. The existing replace-files-on-disk update flow continues to work because module names and signal names are preserved.

## 11. Open Questions

None at this time. All design decisions are recorded in §3.
