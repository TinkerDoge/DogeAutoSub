# DogeAutoSub UI Redesign — Dark macOS + Atari Stripe

**Date:** 2026-05-05
**Status:** Approved (awaiting plan)
**Supersedes:** `2026-05-05-win95-doge-redesign-design.md`

## Summary

Replace the current Win95-styled UI with a dark, macOS Big Sur-inspired chrome
that carries a single retro signal — a muted color stripe across the title bar,
selectable from four palettes. Layout switches from top tabs to a Finder-style
sidebar. Doge mascot integration is reduced to three intentional moments
(idle, progress, completion). The status, ETA, and log systems are rebuilt for
clarity.

The application's three workflows (Subtitles, Meeting Notes, Translate File)
and all underlying engines (faster-whisper, MLAAS, MarianMT, Google Translate,
auto-updater) remain unchanged. This is a UI/UX overhaul, not a feature change.

## Goals

- Modern, clean, dark UI that reads as macOS-native at a glance.
- A single, cohesive retro signal (the stripe) instead of scattered Win95 chrome.
- Replace ambiguous status/ETA/log surfaces with a layered system that tells
  users what is happening, how long it will take, and (only on demand) why.
- Preserve every existing widget object name and signal so `AutoUI.py` and the
  worker threads need no rewiring.

## Non-goals

- Light mode (removed).
- Resizable sidebar.
- Custom palette editor (4 baked-in palettes only).
- Reordering or hiding workflows.
- Auto-updater UX changes.
- Replacing the splash screen.

## Visual language

### Window chrome

- Frameless `Qt.FramelessWindowHint` window, 12px rounded corners.
- Custom title bar (`fauxTitleBar`, restyled): three traffic-light dots
  (red close / yellow minimize / green zoom) wired to real window actions,
  centered title text, palette-dropdown button on the right.
- Drag-to-move on the title bar.
- Surface tones (shared across all palettes):
  - `#0e0e10` desktop / window backdrop
  - `#1c1c1f` window body
  - `#161618` sidebar
  - `#232327` titlebar
  - `#0f0f11` inputs
  - `#2a2a2e` 1px borders
  - `#cfcfd2` primary text / `#9a9a9f` secondary / `#6a6a70` tertiary
- No translucency or backdrop blur (Qt blur is unreliable on Windows; the dark
  flat surfaces alone carry the macOS feel).
- No emoji anywhere in the UI. The mascot carries personality.

### Stripe

A 3px tall band sits directly below the title bar, full width, divided into
the active palette's bands. This is the only loud retro element; everywhere
else the palette contributes a single accent color.

### Palettes

Four palettes; each defines `stripe` (4–6 band colors), `accent` (one primary
color used for buttons / progress fill / focus rings / active sidebar item),
and `accent_text` (foreground color when text sits on the accent). All other
tokens are shared across palettes — switching is instant and cannot break
contrast.

| ID | Name | Stripe (left → right) | Accent |
|---|---|---|---|
| `atari` *(default)* | Atari Sunset | `#7a3b2e` `#9a5a36` `#b8823a` `#c9a558` | `#b8823a` on `#1a1207` text |
| `rainbow` | Apple Six-Stripe | `#6f8c52` `#c2a85a` `#c4884a` `#a85049` `#7a4a8a` `#4f7a9a` | `#6f8c52` on `#0e0e10` text |
| `crt` | CRT Dusk | `#3a6a8a` `#5a7a9a` `#8a5a8a` `#a85a6a` | `#5a7a9a` on `#0e0e10` text |
| `famicom` | Famicom | `#8a2a2a` `#b84a3a` `#d6c7b5` `#3a3a3a` | `#b84a3a` on `#0e0e10` text |

Selection persists in `QSettings` under key `theme/palette`. Default `atari`.

### Palette dropdown

Title-bar button on the right. Click → opens a dark-styled `QMenu` with
4 rows; each row shows a 32×8 mini-stripe + palette name, with a check on the
active row. Selecting a row immediately rebuilds the stylesheet.

### Typography

- **Body / inputs / buttons / sidebar items** — SF Pro on macOS, Inter on
  Windows, system sans fallback. 12–13px.
- **Pixel accents** — the existing bundled "Pixelated MS Sans Serif" used only
  for: sidebar section labels (`WORKFLOWS`, `RECENT`), small uppercase labels
  above inputs (`SOURCE`, `LANGUAGES`), stat readouts
  (`00:42 / 01:08 · 12.4× realtime`), and badges in the status bar. 9–10px.
- The contrast — sharp modern text for content, chunky bitmap for chrome
  labels — is what does the heavy lifting on the modern-with-retro-accents feel.

## Layout

Window is **900×640**, resizable down to 800×580. Three regions:

```
┌──────────────────────────────────────────┐
│ ● ● ●          DogeAutoSub          [▼] │  title bar (24px) — palette dropdown
├──────────────────────────────────────────┤
│ ▓▓▓▓ ▓▓▓▓ ▓▓▓▓ ▓▓▓▓                       │  stripe (3px)
├────────────┬─────────────────────────────┤
│ WORKFLOWS  │                             │
│ ▸ Subtitles│   active workflow pane      │
│   Notes    │                             │
│   Translate│                             │
│            │                             │
│ RECENT     │                             │
│   file1    │                             │
│   file2    │                             │
├────────────┴─────────────────────────────┤
│ v2.2.5 · GPU: NVIDIA RTX · ● Ready       │  status bar (18px)
└──────────────────────────────────────────┘
```

- **Sidebar (180px fixed).** Section labels in pixel font, uppercase,
  letter-spaced. Workflow rows render with an active-state pill in
  accent-tint (not full accent). The "Recent" section lists the last 5 input
  files; click to reload that file into the active workflow. Recent files are
  persisted in `QSettings` under `recents/<workflow>` (max 5 each).
- **Main pane.** Vertical stack of cards (1px border at `#2a2a2e`, 8px
  radius, 12px internal padding). Each card is a logical group — Source,
  Output, Languages, Action, Phase + Status, Detail log. Same density and
  card grammar across all three workflows.
- **Status bar (18px).** Replaces today's scattered status labels. Shows app
  version, GPU detection, ready/working dot in palette accent. Always visible.

## Doge mascot

GIFs live in a new `icons/mascot/` folder. Three triggers, each falls back
gracefully if its GIF asset is missing (uses a static PNG, no breakage).

### Idle / empty states

When a workflow has no input loaded, the main pane renders a centered slot:
64×64 doge area + a small speech bubble with a tip. Each workflow has its
own GIF and tip:

| Workflow | GIF | Tip |
|---|---|---|
| Subtitles | `idle_subtitles.gif` | "drop video here" |
| Meeting Notes | `idle_notes.gif` | "drop transcript here" |
| Translate File | `idle_translate.gif` | "drop file here" |

### Progress companion

While processing, a 32×32 doge GIF sits to the left of the progress bar
inside the active card. The GIF is phase-aware, driven by the same phase
signal that feeds the phase strip:

| Phase | GIF |
|---|---|
| Preparing | `preparing.gif` |
| Reading video | `extracting.gif` |
| Transcribing | `transcribing.gif` |
| Translating | `translating.gif` |
| Saving | `saving.gif` |

### Completion toast

On success, a toast slides up from the bottom-right with a 24×24 celebrating
doge (`done.gif`) + filename. 4-second auto-dismiss. Reuses existing
`toast.py`. On error, the existing shake + error-toast animations stay as-is
with no doge — keeps failure reads clean.

### View toggles

- **View → Doge Tips off** → static placeholder PNG, no GIFs animate; toast
  copy strips doge slang.
- **View → Reduce Motion off** → first frame only, no looping; toast slide
  becomes instant fade; phase strip transitions skip animation.
- **View → Sounds** unchanged from current behavior.

## Status, ETA, and progress

The current single-label status surface is replaced by three layers, each
with one job and one audience.

### Phase strip

A row of 5 dots with a connecting line, sitting at the top of the active
card. Replaces the current 5-step pipeline indicator. Phase names are
user-facing, not engineering steps:

| Old (engineering) | New (user-facing) |
|---|---|
| Load model | Preparing |
| Extract audio | Reading video |
| Transcribe | Transcribing |
| Translate | Translating |
| Save SRT | Saving |

The active phase is filled with palette accent and labeled below; completed
phases get a small check; pending phases are muted at `#3a3a3e`. The Meeting
Notes workflow uses 3 dots (Reading transcript / Summarizing / Formatting);
Translate File uses 4 (Reading file / Detecting language / Translating /
Formatting output).

### Live status line

A single line directly under the phase strip:

```
Transcribing · 00:42 / 01:08 · ~26s left
```

Three slots, in this order:

1. **Phase verb** — matches the phase strip's active label.
2. **Position** — `mm:ss / mm:ss` of audio processed when known; chunk or item
   count for non-audio phases (`page 2 of 4`, `3 of 12 segments`). When a
   phase has no meaningful position (e.g. model loading), this slot is
   omitted: `Preparing · ~3s left`.
3. **Time remaining** — see EtaTracker below.

Updates at 1–2 Hz.

### EtaTracker

A new estimator replaces the current ad-hoc `tracker.eta_string()`. Three
changes:

1. **Phase-weighted total.** Each phase carries a calibrated default cost
   share, scaled by input size (audio seconds for Subtitles, character count
   for Notes/Translate). Starting shares per workflow (each row sums to 1.0;
   refined against real-run data during implementation):

   | Workflow | Phase shares |
   |---|---|
   | Subtitles | Preparing 5% / Reading video 5% / Transcribing 70% / Translating 18% / Saving 2% |
   | Meeting Notes | Reading transcript 5% / Summarizing 90% / Formatting 5% |
   | Translate File | Reading file 5% / Detecting language 5% / Translating 85% / Formatting 5% |

   The displayed `time remaining` is current-phase ETA plus the sum of
   remaining-phase default costs.
2. **EMA smoothing.** Within a phase, throughput is smoothed with an
   exponential moving average (α = 0.3). No more ±50% jumps between samples.
3. **Cold-start fallback.** Before any throughput sample is available
   (first ~2s of a phase), display the calibrated default for that phase
   prefixed with `~`. Once real throughput arrives, the value transitions to
   the measured estimate. Never display `--:--:--`.

The progress bar's filled width is driven by the **same overall progress
fraction** that feeds the ETA, so the bar and the time always agree.

### Detail log

A collapsible drawer at the bottom of the active card, closed by default.
Closed state shows a thin row labeled `Show details ▾`. Open state reveals
two side-by-side filters:

- **Events** — only structured events: phase started, phase done with
  duration, warnings, errors. No doge quips, no per-segment chatter. This is
  what a user would screenshot to ask for help.
- **Raw output** — the existing terminal-style stream including
  faster-whisper stdout. For developers / debugging only.

Doge narrator output (the `DogeNarrator` "such wow / much progress" lines)
**moves out** of the log entirely and into the toast/mascot system. The
View → Doge Tips toggle now controls only the mascot speech bubble + the
completion toast copy.

### Error surfacing

When an error fires, three things happen at once:

1. The live status line turns to the palette's error red (`#ff6b6b` on dark)
   and shows a one-line summary.
2. The detail log auto-opens to the **Events** filter.
3. The existing shake + error-toast animations play.

The user sees the message immediately, the cause is one click away, and
there is no need to scroll a terminal log to find what broke.

## Animation language

- All transitions: 180ms, ease-out (cubic-bezier 0.2, 0, 0, 1).
- Sidebar workflow switch: 120ms cross-fade of the main pane.
- Toast slide: 240ms slide-up from below + 80ms fade-out.
- Confetti + shake (existing) preserved unchanged.
- Progress-bar shimmer (existing) preserved, recolored to use palette accent.
- All animations gated by **View → Reduce Motion** — when off, durations are
  set to 0 (no easing, no fades, no slides).

## Architecture

The existing module boundaries hold. The redesign is implemented by
expanding the theme system, rewriting one widget tree, adding two small
modules, and editing four existing ones.

### Files touched

| File | Change |
|---|---|
| `modules/theme_tokens.py` | Replace `light`/`dark` keys with 4 palette keys (`atari`, `rainbow`, `crt`, `famicom`); add `accent`, `accent_text`, `stripe` token shapes; rewrite stylesheet template for new chrome (frameless window, sidebar, cards, dropdown menu styling) |
| `modules/ui_DogeAutoSub.py` | Rewrite widget tree as sidebar layout. **Every existing widget object name and signal is preserved** so `AutoUI.py` and the worker threads need no changes. Tab widget is replaced with a `QStackedWidget` driven by sidebar selection |
| `AutoUI.py` | Wire palette dropdown to `QSettings`; handle frameless-window drag/close/min/zoom; remove dark/light toggle; wire phase strip + live status line + EtaTracker; auto-open detail log on error |
| `modules/eta_tracker.py` | **New.** Phase-weighted, EMA-smoothed estimator. Single class `EtaTracker` with `start_phase(name)`, `update(position, total)`, `current_eta_string()`, `overall_fraction()` |
| `modules/log_panel.py` | Split current pipeline timeline into the new `PhaseStrip` widget + `DetailLog` widget. Remove `DogeNarrator` interleaving — narrator output is now routed to mascot/toast only |
| `modules/mascot.py` | Add `set_phase(phase)` for progress companion; add `set_idle(workflow)` for empty-state slot; add static-PNG fallback path |
| `modules/toast.py` | Add `success_with_doge(message, filename)` variant |
| `icons/mascot/` | **New folder.** `idle_subtitles.gif`, `idle_notes.gif`, `idle_translate.gif`, `preparing.gif`, `extracting.gif`, `transcribing.gif`, `translating.gif`, `saving.gif`, `done.gif`, plus matching static PNG fallbacks |

### Signal flow

Worker threads (`subtitle_thread.py`, `meeting_notes_thread.py`,
`translate_thread.py`) keep emitting their existing signals
(`status_update`, `progress_update`, `step_start`, `step_done`,
`duration_update`, etc.). `AutoUI.py` translates these on receipt:

- `step_start(name)` → `EtaTracker.start_phase(name)` + `PhaseStrip.set_active(name)` + `Mascot.set_phase(name)`
- `step_done(name)` → `PhaseStrip.mark_done(name)`
- `progress_update(value)` → `EtaTracker.update(...)` (and the bar reads the
  tracker's `overall_fraction()` rather than the raw value, so bar and ETA
  always agree)
- `status_update(text)` → routed to detail log only; the live status line
  composes its text from phase + tracker state, not from this signal

Worker threads do **not** change. The translation between engineering step
names ("Load model", "Save SRT") and user-facing phase names ("Preparing",
"Saving") happens in `AutoUI.py` via a small mapping table.

### Palette switching

`build_stylesheet(palette_id)` returns a string; switching is:

```python
QApplication.instance().setStyleSheet(build_stylesheet(palette_id))
QSettings().setValue("theme/palette", palette_id)
StripeWidget.set_palette(palette_id)  # repaints the title-bar stripe bands
```

No widget reconstruction. No restart.

## Testing

- `theme_tokens.py` — assert each palette defines all required keys; assert
  `build_stylesheet` returns non-empty for each palette and contains the
  expected accent color.
- `eta_tracker.py` — golden tests:
  - Cold start (0–2s into a phase) returns a sensible default, prefixed `~`.
  - EMA-smoothed throughput against a synthetic stepwise input never moves
    more than 30% between consecutive samples.
  - Overall fraction monotonically increases as phases advance.
  - Phase weights sum to 1.0 for each workflow.
- `log_panel.py` — `DogeNarrator` output never reaches the events filter.
- Manual: load a video on each palette, confirm switching is instant, no
  layout shift, no contrast regression. Run a real transcription end-to-end
  on each workflow with Reduce Motion both on and off. Force an error path
  and confirm the live status line, detail log, and toast all surface.

## Migration / compatibility

- `QSettings` key `theme/dark` (old boolean) is read once on first launch,
  ignored (light mode is removed), and deleted. The new key
  `theme/palette` defaults to `atari` for all users on first launch of the
  redesigned build. Subsequent launches read `theme/palette` directly.
- Existing `mlaas_config.json`, `updater_config.json`, and other on-disk
  state are untouched.
- The auto-updater continues to ship modules as `.py` data files in
  `_internal/`. The new `eta_tracker.py` and `icons/mascot/` are added to
  the `.spec` data list; no PYZ change.

## Open questions

None. All design questions resolved in the brainstorm. Default cost shares
for the EtaTracker are starting values — they will be calibrated against
real-run data during implementation and can be tuned without API changes.
