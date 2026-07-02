#####################################################################################
#  _     _                   ____                           _          _            #
# | |   (_)_ __  _   ___  __/ ___|_ __ __ _ _ __ ___       | |__   ___| |_ __ _     #
# | |   | | '_ \| | | \ \/ / |  _| '__/ _` | '_ ` _ \ _____| '_ \ / _ \ __/ _` |    #
# | |___| | | | | |_| |>  <| |_| | | | (_| | | | | | |_____| |_) |  __/ || (_| |    #
# |_____|_|_| |_|\__,_/_/\_\\____|_|  \__,_|_| |_| |_|     |_.__/ \___|\__\__,_|    #
#####################################################################################
#   constants linuxgram!   #
############################

import os

SESSION_FILE = 'linuxgram.session'
DOWNLOADS_DIR = 'downloads'
CONFIG_FILE = 'config.json'
CREDENTIALS_FILE = 'credentials.json'
PLUGINS_DIR = 'plugins'
LOGS_DIR = 'logs'
LOG_FILE = os.path.join(LOGS_DIR, 'linuxgram.log')
TRACE_LEVEL = 5

MONO_PALETTE = [
    ('header', 'white', 'black'),
    ('footer', 'white', 'black'),
    ('selected', 'white', 'black', 'bold'),
    ('dialog_name', 'white', 'black'),
    ('status', 'white', 'black'),
    ('title', 'white', 'black', 'bold'),
    ('button', 'white', 'black', 'bold'),
    ('input', 'white', 'black'),
    ('error', 'white', 'black', 'standout'),
    ('success', 'white', 'black'),
    ('reaction', 'white', 'black'),
    ('notification', 'white', 'black', 'standout'),
]

DEFAULT_THEMES = {
    'mono': MONO_PALETTE,
    'default': MONO_PALETTE,
    'dark': MONO_PALETTE,
    'blue': MONO_PALETTE,
}

REACTION_LABELS = {
    '👍': 'thumbs_up',
    '👎': 'thumbs_down',
    '❤️': 'heart',
    '🔥': 'fire',
    '🎉': 'party',
    '😁': 'grin',
    '🤔': 'thinking',
    '😱': 'shock',
    '😭': 'cry',
    '🍌': 'banana',
    '💯': 'hundred',
    '👌': 'ok',
    '🙏': 'pray',
    '🤝': 'handshake',
    '🏆': 'trophy',
    '🤡': 'clown',
    '🗿': 'moai',
    '🤬': 'angry',
    '😐': 'neutral',
}

LABEL_TO_EMOJI = {v: k for k, v in REACTION_LABELS.items()}

LAYOUT_MAP = {
    'ru': {
        'q': 'й', 'w': 'ц', 'e': 'у', 'r': 'к', 't': 'е', 'y': 'н', 'u': 'г', 'i': 'ш', 'o': 'щ', 'p': 'з',
        '[': 'х', ']': 'ъ', 'a': 'ф', 's': 'ы', 'd': 'в', 'f': 'а', 'g': 'п', 'h': 'р', 'j': 'о', 'k': 'л',
        'l': 'д', ';': 'ж', "'": 'э', 'z': 'я', 'x': 'ч', 'c': 'с', 'v': 'м', 'b': 'и', 'n': 'т', 'm': 'ь',
        ',': 'б', '.': 'ю', '/': '.',
        'Q': 'Й', 'W': 'Ц', 'E': 'У', 'R': 'К', 'T': 'Е', 'Y': 'Н', 'U': 'Г', 'I': 'Ш', 'O': 'Щ', 'P': 'З',
        '{': 'Х', '}': 'Ъ', 'A': 'Ф', 'S': 'Ы', 'D': 'В', 'F': 'А', 'G': 'П', 'H': 'Р', 'J': 'О', 'K': 'Л',
        'L': 'Д', ':': 'Ж', '"': 'Э', 'Z': 'Я', 'X': 'Ч', 'C': 'С', 'V': 'М', 'B': 'И', 'N': 'Т', 'M': 'Ь',
        '<': 'Б', '>': 'Ю', '?': ',',
    },
    'en': {},
}

REVERSE_LAYOUT_MAP = {
    'ru': {v: k for k, v in LAYOUT_MAP['ru'].items()},
    'en': {},
}


class Constants:
    """Compatibility wrapper for grouped constants during migration."""

    SESSION_FILE = SESSION_FILE
    DOWNLOADS_DIR = DOWNLOADS_DIR
    CONFIG_FILE = CONFIG_FILE
    CREDENTIALS_FILE = CREDENTIALS_FILE
    PLUGINS_DIR = PLUGINS_DIR
    LOGS_DIR = LOGS_DIR
    LOG_FILE = LOG_FILE
    TRACE_LEVEL = TRACE_LEVEL
    MONO_PALETTE = MONO_PALETTE
    DEFAULT_THEMES = DEFAULT_THEMES
    REACTION_LABELS = REACTION_LABELS
    LABEL_TO_EMOJI = LABEL_TO_EMOJI
    LAYOUT_MAP = LAYOUT_MAP
    REVERSE_LAYOUT_MAP = REVERSE_LAYOUT_MAP


__all__ = [
    'SESSION_FILE', 'DOWNLOADS_DIR', 'CONFIG_FILE', 'CREDENTIALS_FILE', 'PLUGINS_DIR',
    'LOGS_DIR', 'LOG_FILE', 'TRACE_LEVEL', 'MONO_PALETTE', 'DEFAULT_THEMES',
    'REACTION_LABELS', 'LABEL_TO_EMOJI', 'LAYOUT_MAP', 'REVERSE_LAYOUT_MAP', 'Constants',
]
