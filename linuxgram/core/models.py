#####################################################################################
#  _     _                   ____                           _          _            #
# | |   (_)_ __  _   ___  __/ ___|_ __ __ _ _ __ ___       | |__   ___| |_ __ _     #
# | |   | | '_ \| | | \ \/ / |  _| '__/ _` | '_ ` _ \ _____| '_ \ / _ \ __/ _` |    #
# | |___| | | | | |_| |>  <| |_| | | | (_| | | | | | |_____| |_) |  __/ || (_| |    #
# |_____|_|_| |_|\__,_/_/\_\____|_|  \__,_|_| |_| |_|     |_.__/ \___|\__\__,_|    #
#####################################################################################
#   models linuxgram!   #
########################

class ContactDialog:
    """Lightweight dialog-like proxy used for contact search results."""

    __slots__ = ('entity', 'name', 'unread_count', 'member_count', 'online_count')

    def __init__(self, entity, name: str):
        self.entity = entity
        self.name = name
        self.unread_count = 0
        self.member_count = None
        self.online_count = None


class AppState:
    """Future home for shared mutable state currently stored on LinuxGramTUI."""
    pass
