#####################################################################################
#  _     _                   ____                           _          _            #
# | |   (_)_ __  _   ___  __/ ___|_ __ __ _ _ __ ___       | |__   ___| |_ __ _     #
# | |   | | '_ \| | | \ \/ / |  _| '__/ _` | '_ ` _ \ _____| '_ \ / _ \ __/ _` |    #
# | |___| | | | | |_| |>  <| |_| | | | (_| | | | | | |_____| |_) |  __/ || (_| |    #
# |_____|_|_| |_|\__,_/_/\_\\____|_|  \__,_|_| |_| |_|     |_.__/ \___|\__\__,_|    #
#####################################################################################
#   qr linuxgram!   #
#####################

import qrcode


def render_qr_ascii(data: str) -> str:
    """Render a QR code as block text suitable for a terminal UI."""
    qr = qrcode.QRCode(border=1)
    qr.add_data(data)
    qr.make(fit=True)
    return '\n'.join(''.join('██' if cell else '  ' for cell in row) for row in qr.get_matrix())


class QRRenderer:
    """Compatibility wrapper for QR helpers."""

    render_qr_ascii = staticmethod(render_qr_ascii)


__all__ = ['render_qr_ascii', 'QRRenderer']
