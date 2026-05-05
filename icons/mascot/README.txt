Mascot asset folder.

Expected GIF/PNG pairs (PNG fallback used when GIF is missing or when
View → Reduce Motion is off):

  idle_subtitles.gif  /  idle_subtitles.png
  idle_notes.gif      /  idle_notes.png
  idle_translate.gif  /  idle_translate.png
  preparing.gif       /  preparing.png
  extracting.gif      /  extracting.png
  transcribing.gif    /  transcribing.png
  translating.gif     /  translating.png
  saving.gif          /  saving.png
  done.gif            /  done.png

If neither file is present for a given key, the mascot widget falls back
to the legacy `icons/start.gif` / `icons/done.jpg` so the UI never breaks.
