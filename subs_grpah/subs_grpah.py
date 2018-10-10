# -*- coding: utf-8 -*-

"""Main module."""
from subliminal import *
from babelfish import *

video = Video.fromname('The Godfather 1972')
print(video)
best_subtitles = download_best_subtitles([video], {Language('eng')})
print(best_subtitles[video])
best_subtitle = best_subtitles[video][0]
print(len(best_subtitle.content.split(b'\n')))
