#####################################################################################
#  _     _                   ____                           _          _            #
# | |   (_)_ __  _   ___  __/ ___|_ __ __ _ _ __ ___       | |__   ___| |_ __ _     #
# | |   | | '_ \| | | \ \/ / |  _| '__/ _` | '_ ` _ \ _____| '_ \ / _ \ __/ _` |    #
# | |___| | | | | |_| |>  <| |_| | | | (_| | | | | | |_____| |_) |  __/ || (_| |    #
# |_____|_|_| |_|\__,_/_/\_\\____|_|  \__,_|_| |_| |_|     |_.__/ \___|\__\__,_|    #
#####################################################################################
#   credentials linuxgram!   #
##############################

import json
import os
from pathlib import Path

from .constants import CREDENTIALS_FILE


def load_credentials(credentials_file: str = CREDENTIALS_FILE) -> dict | None:
    """Load Telegram API credentials from disk."""
    try:
        with open(credentials_file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def save_credentials(api_id, api_hash, phone=None, credentials_file: str = CREDENTIALS_FILE) -> None:
    """Atomically save credentials with owner-only permissions."""
    creds = {
        "api_id": api_id,
        "api_hash": api_hash,
        "phone": phone,
    }
    credentials_path = Path(credentials_file)
    tmp_path = credentials_path.with_suffix(credentials_path.suffix + '.tmp')
    with open(tmp_path, 'w') as f:
        json.dump(creds, f, indent=2)
    os.chmod(tmp_path, 0o600)
    os.replace(tmp_path, credentials_path)
    os.chmod(credentials_path, 0o600)


def mask_phone(phone: str | None) -> str:
    """Return a phone string safe enough for logs and notifications."""
    if not phone:
        return "<empty>"
    digits = ''.join(ch for ch in str(phone) if ch.isdigit())
    if len(digits) <= 4:
        return "***"
    return f"***{digits[-4:]}"


class CredentialsManager:
    """Compatibility wrapper for credentials helpers during migration."""

    load_credentials = staticmethod(load_credentials)
    save_credentials = staticmethod(save_credentials)
    mask_phone = staticmethod(mask_phone)


__all__ = ['CredentialsManager', 'load_credentials', 'save_credentials', 'mask_phone']
