from __future__ import unicode_literals
import sys
import json

import pysrt

text_type = str if sys.version_info >= (3,) else unicode


def force_unicode(s, encoding="utf-8"):
    if isinstance(s, text_type):
        return s
    return s.decode(encoding)


def srt_formatter(subtitles, show_before=0, show_after=0):
    f = pysrt.SubRipFile()
    for i, (rng, text) in enumerate(subtitles, 1):
        item = pysrt.SubRipItem()
        item.index = i
        item.text = force_unicode(text)
        start, end = rng
        item.start.seconds = max(0, start - show_before)
        item.end.seconds = end + show_after
        f.append(item)
    return '\n'.join(str(item) for item in f)


def vtt_formatter(subtitles, show_before=0, show_after=0):
    text = srt_formatter(subtitles, show_before, show_after)
    text = 'WEBVTT\n\n' + text.replace(',', '.')
    return text


def json_formatter(subtitles):
    subtitle_dicts = [{'start': r[0], 'end': r[1], 'content': t} for r, t in subtitles]
    return json.dumps(subtitle_dicts)


def raw_formatter(subtitles):
    return ' '.join(text for rng, text in subtitles)


FORMATTERS = {
    'srt': srt_formatter,
    'vtt': vtt_formatter,
    'json': json_formatter,
    'raw': raw_formatter,
}
