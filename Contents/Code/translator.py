# -*- coding: utf-8 -*-
import threading
import time

import utils
from api_client import api
from constants import *

# plex debugging
try:
    import plexhints  # noqa: F401
except ImportError:
    pass
else:  # the code is running outside of Plex
    from plexhints.locale_kit import Locale  # locale kit
    from plexhints.log_kit import Log  # log kit
    from plexhints.prefs_kit import Prefs  # prefs kit

TRANSLATOR_LOCK = threading.Lock()


def translate_text(text, lang, fallback=None):
    with TRANSLATOR_LOCK:

        translated_text = fallback

        if not text:
            Log.Warn('Translation text is empty')
            return translated_text

        if Prefs[KEY_TRANSLATION_MODE] == TRANSLATION_MODE_DISABLED:
            Log.Warn('Translation is disabled')
            return translated_text

        if lang == Locale.Language.Japanese:
            Log.Warn('Translation not applied to Japanese')
            return translated_text

        engine = Prefs[KEY_TRANSLATION_ENGINE]
        params = utils.parse_table(Prefs[KEY_TRANSLATION_ENGINE_PARAMETERS], origin_key=True)

        forced_lang = params.pop('to', None)
        if forced_lang:
            Log.Info('Force setting translation language from {lang} to {forced_lang}'
                     .format(lang=lang, forced_lang=forced_lang))
            lang = forced_lang

        Log.Info('Translate text to {lang}: {text}'.format(lang=lang, text=text))

        # limit translate request rate to 1 rps.
        time.sleep(1.0)

        def translate():
            return api.translate(q=text, to=lang, engine=engine,
                                 **params).translated_text

        return retry(func=translate, fallback=translated_text)


def retry(func, fallback=None, count=3):
    i = 1
    while i <= count:
        try:
            return func()
        except Exception as e:
            Log.Warn('Retry function {func} ({count}): {error}'
                     .format(func=getattr(func, '__name__', func),
                             count=i, error=e))
        i = i + 1
    return fallback
