#####################################################################################
#  _     _                   ____                           _          _            #
# | |   (_)_ __  _   ___  __/ ___|_ __ __ _ _ __ ___       | |__   ___| |_ __ _     #
# | |   | | '_ \| | | \ \/ / |  _| '__/ _` | '_ ` _ \ _____| '_ \ / _ \ __/ _` |    #
# | |___| | | | | |_| |>  <| |_| | | | (_| | | | | | |_____| |_) |  __/ || (_| |    #
# |_____|_|_| |_|\__,_/_/\_\\____|_|  \__,_|_| |_| |_|     |_.__/ \___|\__\__,_|    #
#####################################################################################
#   utils linuxgram!   #
########################


def get_peer_chat_id(peer_id) -> int | None:
    """Extract the numeric chat ID from a Telethon peer_id object."""
    for attr in ('channel_id', 'chat_id', 'user_id'):
        if hasattr(peer_id, attr):
            return getattr(peer_id, attr)
    return None


def format_file_size(size: int) -> str:
    """Return a human-readable file-size string."""
    for unit, threshold in (('GB', 1024 ** 3), ('MB', 1024 ** 2), ('KB', 1024)):
        if size >= threshold:
            return f'{size / threshold:.1f} {unit}'
    return f'{size} B'


class PeerUtils:
    """Compatibility wrapper for peer helpers."""

    get_peer_chat_id = staticmethod(get_peer_chat_id)


class FormatUtils:
    """Compatibility wrapper for formatting helpers."""

    format_file_size = staticmethod(format_file_size)


__all__ = ['get_peer_chat_id', 'format_file_size', 'PeerUtils', 'FormatUtils']
