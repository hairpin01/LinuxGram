import asyncio
import os
import mimetypes
import json
import random
import re
import aiohttp
import math
import asyncio
import sys
import aiohttp
import time
import colorama
import hashlib
import getpass
import signal
from cryptography.fernet import Fernet
from colorama import Fore, Back, Style, init as colorama_init
from urllib.parse import urlparse
from datetime import datetime
from telethon import TelegramClient, events, functions, types
from telethon.tl import functions
from telethon.tl.types import DocumentAttributeFilename, DocumentAttributeVideo, DocumentAttributeAudio
from telethon.network import ConnectionTcpMTProxyAbridged
# i use arch Linux btw
try:
    import socks
except ImportError:
    print("Установка необходимой библиотеки PySocks...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "PySocks"])
    import socks
try:
    from tqdm import tqdm
except ImportError:
    print("Установка необходимой библиотеки tqdm...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "tqdm"])
    from tqdm import tqdm

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "linuxgram")
SECRET_FILE = os.path.join(CONFIG_DIR, "secrets.json")
KEY_FILE = os.path.join(CONFIG_DIR, ".key")

# Конфигурация прокси 
PROXY_CONFIG = {
    "proxify": {
        "name": "Proxify",
        "base_url": "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies",
        "types": {"all": "/all/data.txt", "http": "/protocols/http/data.txt", "socks4": "/protocols/socks4/data.txt", "socks5": "/protocols/socks5/data.txt", "us_socks": "/countries/US/data.txt"}
    },
    "skillter": {
        "name": "Skillter",
        "base_url": "https://raw.githubusercontent.com/Skillter/ProxyGather/refs/heads/master/proxies",
        "types": {"all": "/working-proxies-all.txt", "http": "/working-proxies-http.txt", "socks4": "/working-proxies-socks4.txt", "socks5": "/working-proxies-socks5.txt", "scraped": "/scraped-proxies.txt"}
    },
    "hideip": {
        "name": "HideIP.me",
        "base_url": "https://github.com/zloi-user/hideip.me/raw/refs/heads/master",
        "types": {"http": "/http.txt", "https": "/https.txt", "socks4": "/socks4.txt", "socks5": "/socks5.txt", "connect": "/connect.txt"}
    },
    "anonym": {
        "name": "Anonym0usWork",
        "base_url": "https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/refs/heads/main/proxy_files",
        "types": {"http": "/http_proxies.txt", "https": "/https_proxies.txt", "socks4": "/socks4_proxies.txt", "socks5": "/socks5_proxies.txt"}
    },
    "dpangestuw": {
        "name": "dpangestuw",
        "base_url": "https://raw.githubusercontent.com/dpangestuw/Free-Proxy/refs/heads/main",
        "types": {"all": "/All_proxies.txt", "http": "/http_proxies.txt", "socks4": "/socks4_proxies.txt", "socks5": "/socks5_proxies.txt"}
    },
    "zenjahid": {
        "name": "zenjahid",
        "base_url": "https://raw.githubusercontent.com/zenjahid/FreeProxy4u/master",
        "types": {"http": "/http.txt", "socks4": "/socks4.txt", "socks5": "/socks5.txt"}
    },
    "zebbern": {
        "name": "zebbern",
        "base_url": "https://raw.githubusercontent.com/zebbern/Proxy-Scraper/refs/heads/main",
        "types": {"http": "/http.txt", "https": "/https.txt", "socks4": "/socks4.txt", "socks5": "/socks5.txt"}
    },
    "vmheaven": {
        "name": "VMHeaven",
        "base_url": "https://raw.githubusercontent.com/vmheaven/VMHeaven-Free-Proxy-Updated/refs/heads/main",
        "types": {"http": "/http.txt", "https": "/https.txt", "socks4": "/socks4.txt", "socks5": "/socks5.txt"}
    },
    "databay": {
        "name": "databay-labs",
        "base_url": "https://cdn.jsdelivr.net/gh/databay-labs/free-proxy-list",
        "types": {"http": "/http.txt", "https": "/https.txt", "socks5": "/socks5.txt"}
    },
    "dinozorg_scraped": {
        "name": "dinoz0rg (Scraped)",
        "base_url": "https://raw.githubusercontent.com/dinoz0rg/proxy-list/main/scraped_proxies",
        "types": {"http": "/http.txt", "socks4": "/socks4.txt", "socks5": "/socks5.txt"}
    },
    "dinozorg_checked": {
        "name": "dinoz0rg (Checked)",
        "base_url": "https://raw.githubusercontent.com/dinoz0rg/proxy-list/main/checked_proxies",
        "types": {"http": "/http.txt", "socks4": "/socks4.txt", "socks5": "/socks5.txt"}
    },
    "proxyscraper": {
        "name": "ProxyScraper",
        "base_url": "https://raw.githubusercontent.com/ProxyScraper/ProxyScraper/refs/heads/main",
        "types": {"http": "/http.txt", "socks4": "/socks4.txt", "socks5": "/socks5.txt"}
    },
    "iplocate": {
        "name": "iplocate",
        "base_url": "https://raw.githubusercontent.com/iplocate/free-proxy-list/main",
        "types": {"all": "/all-proxies.txt", "http": "/protocols/http.txt", "https": "/protocols/https.txt", "socks4": "/protocols/socks4.txt", "socks5": "/protocols/socks5.txt"}
    },
    "mtproto_solispirit": {
        "name": "MTProto (SoliSpirit)",
        "base_url": "https://raw.githubusercontent.com/SoliSpirit/mtproto/master",
        "types": {"all": "/all_proxies.txt"}
    },
    "mtproto_alt": {
        "name": "MTProto (Альтернативный)",
        "base_url": "https://raw.githubusercontent.com/hookzof/socks5_list/master",
        "types": {"mtproto": "/mtproto.txt"}
    }
}



VERSION = "1.9.066"
API_ID = 12345678 # и апи хэш
API_HASH = 'TYPE_YOU_API_HASH' # тута апи хеш который вы получили на my.telegram.org 
SESSION_FILE = 'linuxgram.session'
DOWNLOADS_DIR = "downloads"
CONFIG_FILE = "config.json"
FOLDERS_FILE = "folders.json"
PROXY_CACHE_FILE = "proxy_cache.json"  # Новый файл для кеширования прокси

client = None
proxy_cache = {}
current_proxy = None


client = TelegramClient(SESSION_FILE, API_ID, API_HASH)

# Создаем папку для загрузок
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

colorama_init(autoreset=True)

# Определение цветовых тем
THEMES = {
    "default": {
        "header": Fore.GREEN + Style.BRIGHT,
        "primary": Fore.WHITE,
        "secondary": Fore.LIGHTBLACK_EX,
        "success": Fore.GREEN,
        "warning": Fore.YELLOW,
        "error": Fore.RED,
        "info": Fore.CYAN,
        "highlight": Fore.MAGENTA + Style.BRIGHT,
        "background": ""
    },
    "dark": {
        "header": Fore.CYAN + Style.BRIGHT,
        "primary": Fore.WHITE,
        "secondary": Fore.LIGHTBLACK_EX,
        "success": Fore.GREEN,
        "warning": Fore.YELLOW,
        "error": Fore.RED,
        "info": Fore.BLUE,
        "highlight": Fore.MAGENTA + Style.BRIGHT,
        "background": ""
    },
    "light": {
        "header": Fore.BLUE + Style.BRIGHT,
        "primary": Fore.BLACK,
        "secondary": Fore.LIGHTBLACK_EX,
        "success": Fore.GREEN,
        "warning": Fore.YELLOW,
        "error": Fore.RED,
        "info": Fore.BLUE,
        "highlight": Fore.MAGENTA + Style.BRIGHT,
        "background": ""
    },
    "blue": {
        "header": Fore.BLUE + Style.BRIGHT,
        "primary": Fore.CYAN,
        "secondary": Fore.LIGHTBLUE_EX,
        "success": Fore.GREEN,
        "warning": Fore.YELLOW,
        "error": Fore.RED,
        "info": Fore.WHITE,
        "highlight": Fore.MAGENTA + Style.BRIGHT,
        "background": ""
    },
    "purple": {
        "header": Fore.MAGENTA + Style.BRIGHT,
        "primary": Fore.LIGHTMAGENTA_EX,
        "secondary": Fore.LIGHTBLACK_EX,
        "success": Fore.GREEN,
        "warning": Fore.YELLOW,
        "error": Fore.RED,
        "info": Fore.CYAN,
        "highlight": Fore.YELLOW + Style.BRIGHT,
        "background": ""
    },
    "matrix": {
        "header": Fore.GREEN + Style.BRIGHT,
        "primary": Fore.GREEN,
        "secondary": Fore.LIGHTGREEN_EX,
        "success": Fore.GREEN,
        "warning": Fore.YELLOW,
        "error": Fore.RED,
        "info": Fore.WHITE,
        "highlight": Fore.WHITE + Style.BRIGHT,
        "background": ""
    }
}

def ensure_config_dir():
    """Создает конфигурационную директорию если её нет"""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    # Устанавливаем безопасные права доступа
    os.chmod(CONFIG_DIR, 0o700)

def setup_signal_handlers():
    """Устанавливает обработчики сигналов для корректного завершения"""
    def signal_handler(sig, frame):
        cprint("\n\n⚠️ Загрузка прервана пользователем", "warning")
        download_progress.finish()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)

def generate_key():
    """Генерирует ключ шифрования"""
    return Fernet.generate_key()

def load_or_create_key():
    """Загружает существующий ключ или создает новый"""
    ensure_config_dir()
    
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, 'rb') as f:
            return f.read()
    else:
        key = generate_key()
        with open(KEY_FILE, 'wb') as f:
            f.write(key)
        # Устанавливаем безопасные права доступа
        os.chmod(KEY_FILE, 0o600)
        return key

def encrypt_data(data, key):
    """Шифрует данные"""
    fernet = Fernet(key)
    return fernet.encrypt(data.encode())

def decrypt_data(encrypted_data, key):
    """Дешифрует данные"""
    fernet = Fernet(key)
    return fernet.decrypt(encrypted_data).decode()

def save_api_credentials(api_id, api_hash):
    """Безопасно сохраняет API credentials"""
    key = load_or_create_key()
    
    data = {
        'api_id': api_id,
        'api_hash': api_hash,
        'hash': hashlib.sha256(f"{api_id}{api_hash}".encode()).hexdigest()  # Для проверки целостности
    }
    
    encrypted_data = encrypt_data(json.dumps(data), key)
    
    with open(SECRET_FILE, 'wb') as f:
        f.write(encrypted_data)
    
    # Устанавливаем безопасные права доступа
    os.chmod(SECRET_FILE, 0o600)

def load_api_credentials():
    """Загружает API credentials"""
    if not os.path.exists(SECRET_FILE):
        return None, None
    
    try:
        key = load_or_create_key()
        
        with open(SECRET_FILE, 'rb') as f:
            encrypted_data = f.read()
        
        decrypted_data = json.loads(decrypt_data(encrypted_data, key))
        
        # Проверяем целостность данных
        expected_hash = hashlib.sha256(
            f"{decrypted_data['api_id']}{decrypted_data['api_hash']}".encode()
        ).hexdigest()
        
        if decrypted_data['hash'] == expected_hash:
            return decrypted_data['api_id'], decrypted_data['api_hash']
        else:
            print("⚠️ Обнаружена поврежденная конфигурация API")
            return None, None
            
    except Exception as e:
        print(f"❌ Ошибка при загрузке API данных: {e}")
        return None, None

def validate_api_id(api_id):
    """Проверяет валидность API ID"""
    try:
        api_id_int = int(api_id)
        return api_id_int > 0 and len(api_id) >= 5
    except ValueError:
        return False

def validate_api_hash(api_hash):
    """Проверяет валидность API Hash"""
    return isinstance(api_hash, str) and len(api_hash) == 32 and api_hash.isalnum()

def secure_input(prompt, password=False):
    """Безопасный ввод данных"""
    if password:
        return getpass.getpass(prompt)
    else:
        return input(prompt)

def setup_api_credentials_interactive():
    """Интерактивная настройка API credentials с валидацией"""
    print("\n🔐 Настройка API Telegram")
    print("=" * 50)
    
    while True:
        api_id = secure_input("Введите ваш API ID: ").strip()
        
        if not validate_api_id(api_id):
            print("❌ Неверный API ID. Должен быть числом (например: 1234567)")
            continue
            
        api_hash = secure_input("Введите ваш API Hash: ").strip()
        
        if not validate_api_hash(api_hash):
            print("❌ Неверный API Hash. Должен быть 32-символьной строкой")
            continue
        
        # Подтверждение
        print(f"\nПроверьте введенные данные:")
        print(f"API ID: {api_id}")
        print(f"API Hash: {api_hash[:8]}...{api_hash[-8:]}")
        
        confirm = secure_input("\nСохранить эти данные? (y/n): ").lower().strip()
        
        if confirm in ['y', 'yes', 'д', 'да']:
            save_api_credentials(int(api_id), api_hash)
            print("✅ API данные успешно сохранены!")
            return int(api_id), api_hash
        else:
            retry = secure_input("Попробовать снова? (y/n): ").lower().strip()
            if retry not in ['y', 'yes', 'д', 'да']:
                return None, None

def reset_api_credentials():
    """Сбрасывает сохраненные API credentials"""
    if os.path.exists(SECRET_FILE):
        os.remove(SECRET_FILE)
        print("✅ API данные удалены")
    if os.path.exists(KEY_FILE):
        os.remove(KEY_FILE)
        print("✅ Ключ шифрования удален")

def get_theme_color(element):
    """Возвращает цвет элемента для текущей темы"""
    theme_name = config.get("appearance", {}).get("theme", "default")
    theme = THEMES.get(theme_name, THEMES["default"])
    return theme.get(element, "")


def fix_missing_config_keys():
    """Добавляет отсутствующие ключи в конфигурацию"""
    global config
    
    # Добавляем use_colors если его нет
    if "use_colors" not in config.get("appearance", {}):
        if "appearance" not in config:
            config["appearance"] = {}
        config["appearance"]["use_colors"] = True
        save_config(config)
        cprint("✅ Добавлен отсутствующий ключ 'use_colors' в конфигурацию", "success")

def load_config():
    default_config = {
        "privacy": {
            "last_seen": "everybody",
            "profile_photo": "everybody",
            "forwarded_messages": "everybody",
            "calls": "everybody",
            "groups": "everybody",
            "read_receipts": True
        },
        "notifications": {
            "private_chats": True,
            "groups": True,
            "channels": False,
            "sound": True,
            "preview": True
        },
        "appearance": {
            "theme": "default",
            "message_text_size": "medium",
            "animate_emojis": True,
            "show_media_previews": True,
            "use_colors": True  # Добавляем этот ключ
        },
        "data": {
            "auto_download": {
                "photos": True,
                "videos": False,
                "files": False,
                "voice_messages": True,
                "stories": False,
                "stickers": True
            },
            "save_to_gallery": True,
            "data_usage": "medium"
        },
        "language": "Russian",
        "auto_night_mode": False,
        "proxy": {
            "enabled": False,
            "type": "socks5",
            "host": "",
            "port": "",
            "username": "",
            "password": ""
        }
    }
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            loaded_config = json.load(f)
            # Обновляем конфиг, добавляя отсутствующие ключи
            updated_config = update_config(loaded_config, default_config)
            
            # Гарантируем, что use_colors присутствует
            if "appearance" not in updated_config:
                updated_config["appearance"] = {}
            if "use_colors" not in updated_config["appearance"]:
                updated_config["appearance"]["use_colors"] = True
                
            return updated_config
    except FileNotFoundError:
        return default_config
         
      

def safe_get_config(key_path, default_value):
    """Безопасно получает значение из конфига по пути ключей"""
    keys = key_path.split('.')
    value = config
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default_value
    return value

def cprint(text, color_element="primary"):
    """Безопасный цветной вывод текста"""
    use_colors = safe_get_config("appearance.use_colors", True)
    if not use_colors:
        print(text)
        return

    theme_name = safe_get_config("appearance.theme", "default")
    theme = THEMES.get(theme_name, THEMES["default"])
    color = theme.get(color_element, "")
    print(color + text + Style.RESET_ALL)

def cinput(prompt, color_element="primary"):
    """Безопасный цветной ввод"""
    use_colors = safe_get_config("appearance.use_colors", True)
    if not use_colors:
        return input(prompt)

    theme_name = safe_get_config("appearance.theme", "default")
    theme = THEMES.get(theme_name, THEMES["default"])
    color = theme.get(color_element, "")
    user_input = input(color + prompt + Style.RESET_ALL)
    return user_input

def print_colored_header(title):
    """Безопасный цветной заголовок"""
    clear_console()
    
    use_colors = safe_get_config("appearance.use_colors", True)
    theme_name = safe_get_config("appearance.theme", "default")
    
    if not use_colors:
        print("=" * 80)
        print(f"LinuxGram, версия: {VERSION}. - {title}")
        print("=" * 80)
        return

    theme = THEMES.get(theme_name, THEMES["default"])
    header_color = theme.get("header", "")
    line = "=" * 80
    
    print(header_color + line + Style.RESET_ALL)
    print(header_color + f"LinuxGram, версия: {VERSION}. - {title}" + Style.RESET_ALL)
    print(header_color + line + Style.RESET_ALL)


def update_config(loaded_config, default_config):
    """Рекурсивно обновляет конфиг, добавляя отсутствующие ключи"""
    for key, value in default_config.items():
        if key not in loaded_config:
            loaded_config[key] = value
        elif isinstance(value, dict) and isinstance(loaded_config[key], dict):
            loaded_config[key] = update_config(loaded_config[key], value)
    return loaded_config

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def load_folders():
    default_folders = {
        "Все чаты": [],  # Все чаты по умолчанию
        "Новые чаты": [],  # Специальная папка для новых чатов
        "Архив": []  # Папка архива
    }
    
    try:
        with open(FOLDERS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return default_folders

def save_folders(folders):
    with open(FOLDERS_FILE, 'w') as f:
        json.dump(folders, f, indent=4)

config = load_config()
folders = load_folders()

# Функции для работы с папками
def load_folders():
    default_folders = {
        "Все чаты": [],  # Все чаты по умолчанию
        "Новые чаты": [],  # Специальная папка для новых чатов
        "Архив": []  # Папка архива
    }
    
    try:
        with open(FOLDERS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return default_folders

def save_folders(folders):
    with open(FOLDERS_FILE, 'w') as f:
        json.dump(folders, f, indent=4)

folders = load_folders()  # Загружаем информацию о папках 

# Переменные для хранения состояния
current_dialog = None
current_messages = []
reply_to_message = None
selected_message_for_reaction = None
search_results = []
displayed_messages = []  # Сообщения, которые сейчас отображаются
cached_chat_info = {}  # Кеш информации о чатах
show_archived = False  # Флаг показа архивных чатов
search_contacts_results = []  # Результаты поиска контактов
current_folder = "Все чаты"  # Текущая выбранная папка

# Эмодзи для представления медиа-файлов
MEDIA_EMOJIS = {
    'sticker': ['🏷️', '🎨', '🖼️', '✨'],
    'photo': ['🖼️', '📸', '🌄', '🏞️'],
    'video': ['🎥', '📹', '🎬', '📽️'],
    'gif': ['🎬', '🔄', '🌀', '💫'],
    'voice': ['🎵', '🎤', '🔊', '🎶'],
    'audio': ['🎵', '🎧', '🎼', '🎶'],
    'document': ['📄', '📑', '📎', '📋'],
    'location': ['📍', '🌍', '🗺️', '🚩'],
    'contact': ['👤', '📱', '📞', '👤'],
    'poll': ['📊', '🗳️', '📈', '🔢']
}

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title):
    print_colored_header(title)

async def check_for_updates():
    """Проверяет наличие обновлений на GitHub через прямой запрос к файлу"""
    try:
        async with aiohttp.ClientSession() as session:
            # Прямой запрос к raw-файлу с версией в репозитории
            version_url = "https://raw.githubusercontent.com/hairpin01/LinuxGram/main/version.txt"
            
            # Добавляем случайный параметр для избежания кеширования
            timestamp = int(time.time())
            full_url = f"{version_url}?t={timestamp}"
            
            async with session.get(full_url, timeout=10) as response:
                if response.status == 200:
                    latest_version = (await response.text()).strip()
                    
                    # Удаляем все нечисловые символы, кроме точек
                    # Это уберет кавычки и другие возможные лишние символы
                    import re
                    latest_version_clean = re.sub(r'[^\d.]', '', latest_version)
                    current_version_clean = re.sub(r'[^\d.]', '', VERSION)
                    
                    # Функция для сравнения версий
                    def version_tuple(version_str):
                        # Обрабатываем версии с разным количеством компонентов
                        parts = version_str.split('.')
                        # Заполняем нулями недостающие компоненты
                        while len(parts) < 3:
                            parts.append('0')
                        return tuple(map(int, parts))
                    
                    # Сравниваем версии
                    current_tuple = version_tuple(current_version_clean)
                    latest_tuple = version_tuple(latest_version_clean)
                    
                    if latest_tuple > current_tuple:
                        cprint(f"\n⚠️ Доступно обновление {latest_version_clean}! Текущая версия: {VERSION}", "warning")
                        cprint("Скачать можно по ссылке: https://github.com/hairpin01/LinuxGram/", "warning")
                        cprint("Рекомендуется обновиться для получения новых функций и исправлений ошибок.\n", "warning")
                        return True
                    else:
                        cprint(f"✅ У вас актуальная версия {VERSION}", "success")
                        return False
                else:
                    print(f"Не удалось проверить обновления (ошибка сервера: {response.status})")
                    return False
    except asyncio.TimeoutError:
        print("Таймаут при проверке обновлений")
        return False
    except Exception as e:
        print(f"Ошибка при проверке обновлений: {e}")
        return False

# Создадим также функцию для создания файла версии (для разработчика)
def create_version_file():
    """Создает файл VERSION с текущей версией (для разработчика)"""
    with open("VERSION", "w") as f:
        f.write(VERSION)
    cprint(f"Файл VERSION создан с версией {VERSION}", "success")

async def get_chat_info(dialog):
    """Получает информацию о чате/канале"""
    global cached_chat_info
    
    if dialog.id in cached_chat_info:
        return cached_chat_info[dialog.id]
    
    try:
        if isinstance(dialog.entity, types.Channel):
            full_chat = await client(functions.channels.GetFullChannelRequest(channel=dialog.entity))
        else:
            full_chat = await client(functions.messages.GetFullChatRequest(chat_id=dialog.entity.id))
        
        cached_chat_info[dialog.id] = full_chat
        return full_chat
    except Exception as e:
        print(f"Ошибка при получении информации о чате: {e}")
        return None

async def get_user_status(user):
    """Получает статус пользователя"""
    if not user or not hasattr(user, 'status'):
        return "неизвестно"
    
    if isinstance(user.status, types.UserStatusOnline):
        return "🟢 онлайн"
    elif isinstance(user.status, types.UserStatusOffline):
        return f"⚫ не в сети (был(а) {user.status.was_online.strftime('%d.%m.%Y %H:%M')})"
    elif isinstance(user.status, types.UserStatusRecently):
        return "🟡 был(а) недавно"
    elif isinstance(user.status, types.UserStatusLastWeek):
        return "🟡 был(а) на прошлой неделе"
    elif isinstance(user.status, types.UserStatusLastMonth):
        return "🟡 был(а) в прошлом месяце"
    else:
        return "неизвестно"

async def show_dialogs():
    global show_archived, current_folder, folders
    
    dialogs = await client.get_dialogs()
    print_header(f"Ваши диалоги - Папка: {current_folder}")
    
    # Показываем доступные папки
    cprint("Папки:", "info")
    for i, folder_name in enumerate(folders.keys()):
        folder_icon = "📁"
        if folder_name == "Архив":
            folder_icon = "📦"
        elif folder_name == "Новые чаты":
            folder_icon = "🆕"
        
        # Подсчитываем количество чатов в папке
        chat_count = len(folders[folder_name])
        unread_count = 0
        
        # Считаем непрочитанные сообщения в папке
        for dialog_id in folders[folder_name]:
            for dialog in dialogs:
                if str(dialog.id) == str(dialog_id):
                    unread_count += dialog.unread_count
        
        unread_info = f" ({unread_count} непр.)" if unread_count > 0 else ""
        cprint(f"{i+1}. {folder_icon} {folder_name} [{chat_count} чатов]{unread_info}", "primary")
    
    cprint("-" * 80, "secondary")
    
    # Фильтруем диалоги в зависимости от текущей папки
    filtered_dialogs = []
    for dialog in dialogs:
        # Для папки "Все чаты" показываем все диалоги
        if current_folder == "Все чаты":
            if not show_archived or str(dialog.id) not in folders["Архив"]:
                filtered_dialogs.append(dialog)
        else:
            # Для других папок проверяем наличие диалога в папке
            if str(dialog.id) in folders[current_folder]:
                filtered_dialogs.append(dialog)
    
    # Собираем все задачи для статусов пользователей
    status_tasks = []
    for dialog in filtered_dialogs:
        if isinstance(dialog.entity, types.User):
            status_tasks.append(get_user_status(dialog.entity))
        else:
            status_tasks.append(None)
    
    # Выполняем все задачи параллельно
    status_results = []
    for task in status_tasks:
        if task is not None:
            try:
                status_results.append(await task)
            except Exception as e:
                status_results.append(f"ошибка: {e}")
        else:
            status_results.append(None)
    
    # Выводим диалоги
    for i, dialog in enumerate(filtered_dialogs):
        # Определяем тип диалога
        dialog_type = ""
        if isinstance(dialog.entity, types.Channel):
            if getattr(dialog.entity, 'megagroup', False):
                dialog_type = " [Группа]"
            else:
                dialog_type = " [Канал]"
        elif isinstance(dialog.entity, types.Chat):
            dialog_type = " [Группа]"
        else:
            dialog_type = " [Личный]"
        
        # Для личных чатов получаем статус пользователя
        status_info = ""
        if isinstance(dialog.entity, types.User):
            status = status_results[i]
            status_info = f" - {status}"
        
        # Для групп и каналов получаем информацию об участниках (только общее количество)
        members_info = ""
        if isinstance(dialog.entity, (types.Channel, types.Chat)):
            chat_info = await get_chat_info(dialog)
            if chat_info:
                participants_count = getattr(chat_info.full_chat, 'participants_count', 0)
                members_info = f" ({participants_count} участников)"
        
        unread = f" ({dialog.unread_count} непр.)" if dialog.unread_count > 0 else ""
        archived = " [АРХИВ]" if str(dialog.id) in folders["Архив"] else ""
        cprint(f"{i+1:2d}. {dialog.name}{dialog_type}{members_info}{unread}{archived}{status_info}", "primary")
    
    # Меню действий
    cprint("\n0. Выход", "error")
    cprint("s. Настройки", "highlight")
    cprint("i. Итоги", "highlight")
    
    if show_archived:
        cprint("a. Показать обычные чаты", "highlight")
    else:
        cprint("a. Показать архив", "highlight")
    
    cprint("p. Поиск контактов", "highlight")
    cprint("c. Создать группу/канал", "highlight")
    cprint("m. Управление папками", "highlight")
    cprint("f. Сменить папку", "highlight")
    
    return filtered_dialogs

class DownloadProgress:
    """Класс для отображения прогресса загрузки файлов"""
    
    def __init__(self):
        self.current_bar = None
        self.start_time = None
        
    def create_progress_bar(self, filename, total_size):
        """Создает новый прогресс-бар"""
        # Очищаем предыдущий прогресс-бар
        if self.current_bar:
            self.current_bar.close()
            
        self.start_time = time.time()
        self.current_bar = tqdm(
            desc=filename,
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
            ncols=80,
            bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'
        )
        return self.current_bar
    
    def update_progress(self, current, total):
        """Обновляет прогресс-бар"""
        if self.current_bar and total > 0:
            if self.current_bar.total != total:
                self.current_bar.total = total
            self.current_bar.update(current - self.current_bar.n)
    
    def finish(self):
        """Завершает и закрывает прогресс-бар"""
        if self.current_bar:
            self.current_bar.close()
            self.current_bar = None

# Глобальный экземпляр для управления прогресс-барами
download_progress = DownloadProgress()

async def get_sender_name(sender):
    """Получаем имя отправителя с учетом типа (User, Channel, Chat)"""
    if isinstance(sender, types.User):
        name = sender.first_name or ""
        if sender.last_name:
            name += f" {sender.last_name}"
        return name.strip() or "Unknown User"
    elif isinstance(sender, (types.Channel, types.Chat)):
        return sender.title or "Unknown Channel/Chat"
    else:
        return "Unknown"

async def get_replied_message_text(message, dialog):
    """Получаем текст сообщения, на которое дан ответ"""
    if not message.reply_to_msg_id:
        return None
    
    try:
        # Пытаемся найти сообщение, на которое ответили
        replied_msg = await client.get_messages(dialog.entity, ids=message.reply_to_msg_id)
        if replied_msg and replied_msg.text:
            # Обрезаем длинный текст
            text = replied_msg.text
            return text[:50] + "..." if len(text) > 50 else text
        elif replied_msg and replied_msg.media:
            return "[медиа-сообщение]"
        else:
            return "[сообщение]"
    except Exception:
        return "[сообщение]"

async def get_media_info(msg):
    """Получаем информацию о медиа-файле"""
    if not msg.media:
        return None, None
    
    # Для стикеров
    if isinstance(msg.media, types.MessageMediaDocument):
        if msg.document:
            for attr in msg.document.attributes:
                if isinstance(attr, types.DocumentAttributeSticker):
                    emoji = attr.alt if attr.alt else "🎨"
                    return "sticker", f"Стикер {emoji}"
                elif isinstance(attr, types.DocumentAttributeVideo):
                    if hasattr(attr, 'round_message') and attr.round_message:
                        return "video", "Круговое видео"
                    else:
                        duration = f" ({attr.duration}s)" if hasattr(attr, 'duration') else ""
                        return "video", f"Видео{duration}"
                elif isinstance(attr, types.DocumentAttributeAudio):
                    if hasattr(attr, 'voice') and attr.voice:
                        return "voice", "Голосовое сообщение"
                    else:
                        duration = f" ({attr.duration}s)" if hasattr(attr, 'duration') else ""
                        title = f" {attr.title}" if hasattr(attr, 'title') and attr.title else ""
                        return "audio", f"Аудио{title}{duration}"
                elif isinstance(attr, types.DocumentAttributeAnimated):
                    return "gif", "GIF"
    
    # Для фото
    if isinstance(msg.media, types.MessageMediaPhoto):
        return "photo", "Фото"
    
    # Для геолокации
    if isinstance(msg.media, types.MessageMediaGeo):
        return "location", "Геолокация"
    
    # Для контактов
    if isinstance(msg.media, types.MessageMediaContact):
        return "contact", "Контакт"
    
    # Для опросов
    if isinstance(msg.media, types.MessageMediaPoll):
        return "poll", f"Опрос: {msg.media.poll.question}"
    
    # Для веб-страниц
    if isinstance(msg.media, types.MessageMediaWebPage):
        if isinstance(msg.media.webpage, types.WebPage):
            return "webpage", f"Веб-страница: {msg.media.webpage.title or msg.media.webpage.url}"
    
    # Общий случай для документов
    if msg.file:
        file_name = msg.file.name or "файл"
        return "document", f"Документ: {file_name}"
    
    return None, "Медиа-файл"

async def show_messages(dialog, messages=None, title=None):
    global current_messages, reply_to_message, displayed_messages
    
    if messages is None:
        messages = await client.get_messages(dialog.entity, limit=20)
        current_messages = messages
    
    displayed_messages = list(reversed(messages))  # Сохраняем отображаемые сообщения
    
    # Для личных чатов добавляем статус пользователя в заголовок
    if isinstance(dialog.entity, types.User) and title is None:
        status = await get_user_status(dialog.entity)
        title = f"Диалог с {dialog.name} ({status})"
    elif title is None:
        title = f"Диалог с {dialog.name}"
    
    print_header(title)
    
    # Для групп и каналов показываем информацию об участниках (включая онлайн)
    if isinstance(dialog.entity, (types.Channel, types.Chat)):
        chat_info = await get_chat_info(dialog)
        if chat_info:
            participants_count = getattr(chat_info.full_chat, 'participants_count', 0)
            online_count = getattr(chat_info.full_chat, 'online_count', 0)
            print(f"Участников: {participants_count}, онлайн: {online_count}")
            print("-" * 80)
    
    # Выводим сообщения
    for i, msg in enumerate(displayed_messages):
        # Определяем отsenderтеля
        sender = await msg.get_sender()
        sender_name = await get_sender_name(sender) if sender else "Unknown"
        
        # Форматируем дату
        date = msg.date.strftime("%d.%m %H:%M")
        
        # Определяем тип сообщения и информацию о медиа
        msg_type = "📝 Текст"
        media_info = ""
        file_info = ""
        
        if msg.media:
            media_type, media_desc = await get_media_info(msg)
            if media_type:
                emoji = random.choice(MEDIA_EMOJIS.get(media_type, ["📎"]))
                msg_type = f"{emoji} {media_desc}"
        
        # Показываем, есть ли ответ на другое сообщение
        reply_info = ""
        if msg.reply_to_msg_id:
            # Получаем текст сообщения, на которое ответили
            replied_text = await get_replied_message_text(msg, dialog)
            reply_info = f" ↩️ (ответ на: {replied_text})"
        
        # Показываем, ответили ли на это сообщение
        replied_to_info = ""
        # Проверяем, есть ли ответы на это сообщение
        for other_msg in messages:
            if other_msg.reply_to_msg_id == msg.id:
                replied_to_info = " 💬 (есть ответы)"
                break
        
        # Показываем реакции
        reactions = ""
        if msg.reactions:
            reactions = " " + " ".join([f"{r.reaction.emoticon}" if hasattr(r.reaction, 'emoticon') else "❓" 
                                      for r in msg.reactions.results])
        
        # Показываем информацию о файле, если есть
        if msg.file:
            file_size = msg.file.size
            if file_size:
                file_size_kb = file_size / 1024
                if file_size_kb < 1024:
                    file_info = f" [{file_size_kb:.1f} KB]"
                else:
                    file_info = f" [{file_size_kb/1024:.1f} MB]"
        
        # Определяем, наше ли это сообщение
        me = await client.get_me()
        is_my_message = msg.sender_id == me.id
        
        # Показываем статус прочтения для наших сообщений
        read_status = ""
        if is_my_message and hasattr(msg, 'read') and msg.read:
            read_status = " ✓✓"  # Двойная галочка для прочитанных сообщений
        elif is_my_message:
            read_status = " ✓"   # Одинарная галочка для отправленных
        
        message_indicator = "➤ " if is_my_message else ""
        
        print(f"{i+1:2d}. {message_indicator}[{date}] {sender_name}: {msg_type}{file_info}{reply_info}{reactions}{read_status}")
        
        # Показываем текст сообщения или подпись к медиа
        if msg.text:
            print(f"      {msg.text[:100]}{'...' if len(msg.text) > 100 else ''}")
        elif hasattr(msg, 'message') and msg.message:
            print(f"      {msg.message[:100]}{'...' if len(msg.message) > 100 else ''}")
        
        print()
    
    # Показываем меню
    print("\nДействия:")
    print("1. Отправить сообщение")
    print("2. Ответить на сообщение")
    print("3. Отправить файл")
    print("4. Поставить реакцию")
    print("5. Поиск по сообщениям")
    print("6. Скачать файл/медиа")
    print("7. Редактировать сообщение")
    print("8. Просмотреть медиа")
    print("9. Показать полное сообщение")
    
    # Для групп и каналов добавляем пункт просмотра участников
    if isinstance(dialog.entity, (types.Channel, types.Chat)):
        print("10. Список участников")
    
    # Добавляем пункт архивации/разархивации
    if str(dialog.id) in folders["Архив"]:
        print("11. Разархивировать чат")
    else:
        print("11. Архивировать чат")
    
    # Для личных чатов добавляем просмотр профиля
    if isinstance(dialog.entity, types.User):
        print("12. Просмотр профиля")
    
    if isinstance(dialog.entity, (types.Channel, types.Chat)):
        # Проверяем, является ли чат группой (мегагруппой) для добавления участников
        if getattr(dialog.entity, 'megagroup', False):
            print("13. Добавить участников")
        print("14. Изменить аватарку")

    cprint("0. Назад", "secondary")
    
    if reply_to_message:
        # Находим номер сообщения в отображаемом списке
        reply_index = None
        for i, msg in enumerate(displayed_messages):
            if msg.id == reply_to_message.id:
                reply_index = i + 1
                break
        if reply_index:
            cprint(f"↩️ Ответ на сообщение {reply_index} (x для отмены)", "highlight")

async def show_user_profile(user, dialog=None):
    """Показывает профиль пользователя"""
    print_header(f"Профиль: {await get_sender_name(user)}")
    
    # Получаем полную информацию о пользователе
    try:
        full_user = await client(functions.users.GetFullUserRequest(user.id))
        
        # Основная информация
        print(f"Имя: {user.first_name or 'Не указано'}")
        print(f"Фамилия: {user.last_name or 'Не указана'}")
        print(f"Username: @{user.username or 'Не указан'}")
        
        # Статус
        status = await get_user_status(user)
        print(f"Статус: {status}")
        
        # Био
        if full_user.full_user.about:
            cprint(f"Био: {full_user.full_user.about}", "secondary")
        else:
            cprint("Био: Не указано", "warning")
        
        # Номер телефона (если доступен)
        if user.phone:
            print(f"Телефон: {user.phone}")
        else:
            print("Телефон: Не указан")
        
        # Бот или человек
        if user.bot:
            cprint("Тип: 🤖 Бот", "warning")
        else:
            cprint("Тип: 👤 Пользователь", "info")
        
        # Закрепленный канал (если есть)
        if hasattr(full_user.full_user, 'pinned_msg_id') and full_user.full_user.pinned_msg_id:
            try:
                # Пытаемся получить закрепленное сообщение
                pinned_msg = await client.get_messages(user.id, ids=full_user.full_user.pinned_msg_id)
                if pinned_msg and pinned_msg.text:
                    print(f"Закрепленное сообщение: {pinned_msg.text[:50]}{'...' if len(pinned_msg.text) > 50 else ''}")
            except:
                print("Закрепленное сообщение: (не удалось получить)")
        
        cprint("\nДействия:", "info")
        print("1. Написать сообщение")
        if not user.bot:
            print("2. Позвонить")
            print("3. Добавить в контакты")
        cprint("0. Назад", "secondary")
        
        choice = cinput("\nВыберите действие: ", "info")
        
        if choice == '1':
            if dialog:
                # Возвращаемся в диалог для отправки сообщения
                return "message"
            else:
                # Создаем новый диалог
                await client.send_message(user.id, "Привет!")
                cprint("Сообщение отправлено!", "success")
                cinput("\nНажмите Enter для продолжения...", "secondary")
        
        elif choice == '2' and not user.bot:
            print("Звонки пока не поддерживаются в LinuxGram.")
            cinput("\nНажмите Enter для продолжения...", "secondary")
        
        elif choice == '3' and not user.bot:
            print("Добавление в контакты пока не поддерживается в LinuxGram.")
            cinput("\nНажмите Enter для продолжения...", "secondary")
        
        elif choice == '0':
            return "back"
        
        else:
            print("Неверный выбор!")
            cinput("\nНажмите Enter для продолжения...", "secondary")
            
    except Exception as e:
        print(f"Ошибка при получении информации о пользователе: {e}")
        cinput("\nНажмите Enter для возврата...", "secondary")
    
    return "back"

async def show_participants(dialog):
    """Показывает список участников группы/канала с возможностью просмотра профиля"""
    print_header(f"Участники {dialog.name}")
    
    try:
        # Получаем информацию о чате
        chat_info = await get_chat_info(dialog)
        if chat_info:
            participants_count = getattr(chat_info.full_chat, 'participants_count', 0)
            online_count = getattr(chat_info.full_chat, 'online_count', 0)
            print(f"Всего участников: {participants_count}, онлайн: {online_count}")
            print("-" * 80)
        
        # Получаем список участников
        participants = await client.get_participants(dialog.entity)
        
        if not participants:
            print("Не удалось получить список участников.")
            cinput("\nНажмиte Enter для возврата...", "secondary")
            return
        
        # Сортируем участников: сначала онлайн, потом по имени
        online_users = []
        offline_users = []
        
        for user in participants:
            if isinstance(user.status, types.UserStatusOnline):
                online_users.append(user)
            else:
                offline_users.append(user)
        
        # Сортируем по имени
        def get_user_name(user):
            first_name = user.first_name or ""
            last_name = user.last_name or ""
            return f"{first_name} {last_name}".strip()
        
        online_users.sort(key=lambda u: get_user_name(u))
        offline_users.sort(key=lambda u: get_user_name(u))
        
        all_users = online_users + offline_users
        
        # Выводим онлайн-участников
        print("🟢 Онлайн:")
        for i, user in enumerate(online_users):
            user_name = await get_sender_name(user)
            user_type = "🤖" if user.bot else "👤"
            print(f"  {i+1:3d}. {user_type} {user_name}")
        
        # Выводим оффлайн-участников
        print("\n⚫ Не в сети:")
        for i, user in enumerate(offline_users, start=len(online_users)+1):
            user_name = await get_sender_name(user)
            user_type = "🤖" if user.bot else "👤"
            
            # Определяем статус
            status = "не в сети"
            if isinstance(user.status, types.UserStatusOffline):
                last_online = user.status.was_online
                if last_online:
                    status = f"был(а) {last_online.strftime('%d.%m.%Y %H:%M')}"
            
            print(f"  {i:3d}. {user_type} {user_name} ({status})")
        
        print(f"\nВсего: {len(participants)} участников")
        
        # Предлагаем просмотреть профиль участника
        print("\nВведите номер участника для просмотра профиля или 0 для возврата:")
        choice = cinput("Ваш выбор: ", "info")
        
        try:
            choice_idx = int(choice)
            if choice_idx == 0:
                return
            elif 1 <= choice_idx <= len(all_users):
                user = all_users[choice_idx - 1]
                result = await show_user_profile(user, dialog)
                # Если выбрано "Написать сообщение", возвращаемся в диалог
                if result == "message":
                    return
                # Иначе продолжаем просмотр участников
                await show_participants(dialog)
            else:
                print("Неверный номер участника!")
                input("\nНажмите Enter для возврата...")
        except ValueError:
            print("Введите число!")
            input("\nНажмите Enter для возврата...")
        
    except Exception as e:
        print(f"Ошибка при получении списка участников: {e}")
        cinput("\nНажмите Enter для возврата...", "secondary")

async def search_contacts():
    """Поиск контактов по username, номеру телефона или имени"""
    global search_contacts_results
    
    print_header("Поиск контактов")
    print("1. Поиск по username")
    print("2. Поиск по номеру телефона")
    print("3. Поиск по имени")
    cprint("0. Назад", "secondary")
    
    choice = input("\nВыберите тип поиска: ")
    
    if choice == '0':
        return
    
    query = input("Введите запрос для поиска: ")
    if not query:
        print("Запрос не может быть пустым!")
        input("\nНажмите Enter для возврата...")
        return
    
    search_contacts_results = []
    
    try:
        if choice == '1':  # Поиск по username
            # Убираем @ если пользователь его ввел
            if query.startswith('@'):
                query = query[1:]
            
            try:
                result = await client(functions.contacts.ResolveUsernameRequest(username=query))
                if result.users:
                    search_contacts_results = result.users
                elif result.chats:
                    search_contacts_results = result.chats
                else:
                    print("Пользователь или канал не найден!")
                    cinput("\nНажмите Enter для возврата...", "secondary")
                    return
            except Exception as e:
                print(f"Ошибка при поиске по username: {e}")
                cinput("\nНажмите Enter для возврата...", "secondary")
                return
        
        elif choice == '2':  # Поиск по номеру телефона
            # Очищаем номер от лишних символов
            phone = re.sub(r'[^0-9+]', '', query)
            
            try:
                # Импортируем контакт для поиска
                result = await client(functions.contacts.ImportContactsRequest(
                    contacts=[types.InputPhoneContact(
                        client_id=random.randrange(2**31),
                        phone=phone,
                        first_name="Поиск",
                        last_name=""
                    )]
                ))
                
                if result.users:
                    search_contacts_results = result.users
                    
                    # Удаляем импортированный контакт
                    await client(functions.contacts.DeleteContactsRequest(id=result.users))
                else:
                    print("Пользователь не найден!")
                    cinput("\nНажмите Enter для возврата...", "secondary")
                    return
            except Exception as e:
                print(f"Ошибка при поиске по номеру телефона: {e}")
                cinput("\nНажмите Enter для возврата...", "secondary")
                return
        
        elif choice == '3':  # Поиск по имени
            # Ищем в своих контактах
            try:
                contacts = await client(functions.contacts.GetContactsRequest(hash=0))
                if contacts and hasattr(contacts, 'users'):
                    for user in contacts.users:
                        name = f"{user.first_name or ''} {user.last_name or ''}".strip().lower()
                        if query.lower() in name:
                            search_contacts_results.append(user)
                else:
                    print("Контакты не найдены!")
                    cinput("\nНажмите Enter для возврата...", "secondary")
                    return
            except Exception as e:
                print(f"Ошибка при получении контактов: {e}")
                cinput("\nНажмите Enter для возврата...", "secondary")
                return
            
            if not search_contacts_results:
                print("Контакты не найдены!")
                cinput("\nНажмите Enter для возврата...", "secondary")
                return
        
        else:
            print("Неверный выбор!")
            cinput("\nНажмите Enter для возврата...", "secondary")
            return
        
        # Показываем результаты поиска
        print_header("Результаты поиска")
        
        if not search_contacts_results:
            print("Ничего не найдено!")
            cinput("\nНажмите Enter для возврата...", "secondary")
            return
        
        for i, entity in enumerate(search_contacts_results):
            if isinstance(entity, types.User):
                user_type = "🤖 Бот" if entity.bot else "👤 Пользователь"
                status = await get_user_status(entity)
                print(f"{i+1:2d}. {user_type}: {await get_sender_name(entity)} - {status}")
            elif isinstance(entity, types.Channel):
                if getattr(entity, 'megagroup', False):
                    print(f"{i+1:2d}. 👥 Группа: {entity.title}")
                else:
                    print(f"{i+1:2d}. 📢 Канал: {entity.title}")
            elif isinstance(entity, types.Chat):
                print(f"{i+1:2d}. 👥 Группа: {entity.title}")
        
        print("\nВведите номер для просмотра профиля или 0 для возврата:")
        choice = cinput("Ваш выбор: ", "info")
        
        try:
            choice_idx = int(choice)
            if choice_idx == 0:
                return
            elif 1 <= choice_idx <= len(search_contacts_results):
                entity = search_contacts_results[choice_idx - 1]
                if isinstance(entity, types.User):
                    await show_user_profile(entity)
                elif isinstance(entity, (types.Channel, types.Chat)):
                    # Для каналов и групп создаем временный диалог
                    temp_dialog = types.Dialog(
                        id=entity.id,
                        name=entity.title,
                        entity=entity,
                        unread_count=0,
                        unread_mentions_count=0,
                        draft=None
                    )
                    await show_messages(temp_dialog, title=f"Информация о {entity.title}")
                # После просмотра возвращаемся к результатам поиска
                await search_contacts()
            else:
                print("Неверный номер!")
                cinput("\nНажмите Enter для возврата...", "secondary")
        except ValueError:
            print("Введите число!")
            cinput("\nНажмите Enter для возврата...", "secondary")
            
    except Exception as e:
        print(f"Ошибка при поиске: {e}")
        cinput("\nНажмите Enter для возврата...", "secondary")

async def search_messages(dialog, query):
    global search_results
    print_header(f"Поиск в диалоге с {dialog.name}")
    
    # Выполняем поиск
    search_results = await client.get_messages(dialog.entity, search=query, limit=20)
    
    if not search_results:
        print("Сообщения не найдены.")
        input("\nНажмите Enter для возврата...")
        return False
    
    await show_messages(dialog, search_results, f"Результаты поиска: '{query}'")
    return True

async def send_text_message(dialog, text):
    global reply_to_message
    
    try:
        if reply_to_message:
            await client.send_message(dialog.entity, text, reply_to=reply_to_message.id)
            reply_to_message = None
        else:
            await client.send_message(dialog.entity, text)
        return True
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")
        return False

async def send_file(dialog, file_path, compress=False):
    global reply_to_message
    
    try:
        # Определяем тип файла по расширению для правильных атрибутов
        ext = os.path.splitext(file_path)[1].lower()
        attributes = []
        
        # Для видеофайлов добавляем правильные атрибуты
        if ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
            # Получаем информацию о видео (размеры и длительность)
            # В реальном приложении здесь нужно использовать библиотеку для извлечения метаданных
            # Для простоты используем стандартные значения
            attributes = [DocumentAttributeVideo(
                duration=0,  # Длительность в секундах
                w=1280,      # Ширина
                h=720,       # Высота
                round_message=False,
                supports_streaming=True
            )]
        # Для аудиофайлов
        elif ext in ['.mp3', '.wav', '.ogg', '.flac']:
            attributes = [DocumentAttributeAudio(
                duration=0,  # Длительность в секундах
                voice=False,
                title=os.path.basename(file_path),
                performer=""
            )]
        
        if reply_to_message:
            await client.send_file(
                dialog.entity, 
                file_path, 
                caption="", 
                reply_to=reply_to_message.id,
                attributes=attributes,
                force_document=not compress  # force_document=True для отправки без сжатия
            )
            reply_to_message = None
        else:
            await client.send_file(
                dialog.entity, 
                file_path, 
                caption="", 
                attributes=attributes,
                force_document=not compress  # force_document=True для отправки без сжатия
            )
        return True
    except Exception as e:
        print(f"Ошибка при отправке файла: {e}")
        return False

async def send_sticker(dialog, file_path):
    try:
        await client.send_file(dialog.entity, file_path, 
                              attributes=[types.DocumentAttributeSticker(alt="sticker")])
        return True
    except Exception as e:
        print(f"Ошибка при отправке стикера: {e}")
        return False

async def set_reaction(dialog, message_id, reaction):
    try:
        await client(functions.messages.SendReactionRequest(
            peer=dialog.entity,
            msg_id=message_id,
            reaction=[types.ReactionEmoji(emoticon=reaction)] if reaction else None
        ))
        return True
    except Exception as e:
        print(f"Ошибка при установке реакции: {e}")
        return False

async def edit_message(message, new_text):
    try:
        await client.edit_message(message.chat_id, message.id, new_text)
        return True
    except Exception as e:
        print(f"Ошибка при редактировании сообщения: {e}")
        return False

async def download_file(message, dialog_name):
    """Скачивает файл из сообщения с отображением прогресса"""
    try:
        # Создаем папку для диалога, если ее нет
        dialog_dir = os.path.join(DOWNLOADS_DIR, dialog_name.replace("/", "_"))
        os.makedirs(dialog_dir, exist_ok=True)
        
        # Определяем имя файла
        if message.file and message.file.name:
            file_name = message.file.name
        else:
            # Генерируем имя файла на основе типа и даты
            media_type, _ = await get_media_info(message)
            ext = ""
            if media_type == "photo":
                ext = ".jpg"
            elif media_type == "video":
                ext = ".mp4"
            elif media_type == "voice":
                ext = ".ogg"
            elif media_type == "sticker":
                ext = ".webp"
            elif media_type == "gif":
                ext = ".mp4"
            else:
                ext = ".bin"
            
            date_str = message.date.strftime("%Y%m%d_%H%M%S")
            file_name = f"{media_type}_{date_str}{ext}"
        
        file_path = os.path.join(dialog_dir, file_name)
        
        # Получаем размер файла
        file_size = message.file.size if message.file else 0
        
        # Создаем прогресс-бар
        progress_bar = download_progress.create_progress_bar(
            os.path.basename(file_name), 
            file_size
        )
        
        # Функция callback для обновления прогресса
        def progress_callback(current, total):
            download_progress.update_progress(current, total)
        
        cprint(f"📥 Начинаем загрузку: {file_name}", "info")
        cprint(f"💾 Размер: {format_file_size(file_size)}", "secondary")
        
        # Скачиваем файл
        download_path = await message.download_media(
            file=file_path,
            progress_callback=progress_callback
        )
        
        # Завершаем прогресс-бар
        download_progress.finish()
        
        if download_path:
            cprint(f"✅ Файл успешно сохранен: {download_path}", "success")
            return True
        else:
            cprint("❌ Ошибка при скачивании файла", "error")
            download_progress.finish()
            return False
            
    except Exception as e:
        cprint(f"❌ Ошибка при скачивании файла: {e}", "error")
        download_progress.finish()
        return False

def format_file_size(size_bytes):
    """Форматирует размер файла в читаемый вид"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.2f} {size_names[i]}"

async def view_media(message, dialog_name):
    """Просмотр медиа-файла (если возможно) с отображением прогресса загрузки"""
    try:
        media_type, media_desc = await get_media_info(message)
        
        # Создаем временную папку для предпросмотра
        temp_dir = os.path.join(DOWNLOADS_DIR, "temp_preview")
        os.makedirs(temp_dir, exist_ok=True)
        
        # Генерируем временное имя файла
        timestamp = int(time.time())
        temp_filename = f"preview_{timestamp}"
        
        if media_type == "photo":
            temp_filename += ".jpg"
        elif media_type == "video":
            temp_filename += ".mp4"
        elif media_type == "sticker":
            temp_filename += ".webp"
        elif media_type == "voice":
            temp_filename += ".ogg"
        else:
            temp_filename += ".tmp"
        
        temp_path = os.path.join(temp_dir, temp_filename)
        
        # Получаем размер файла
        file_size = message.file.size if message.file else 0
        
        # Создаем прогресс-бар
        progress_bar = download_progress.create_progress_bar(
            f"Превью {media_desc}", 
            file_size
        )
        
        # Функция callback для обновления прогресса
        def progress_callback(current, total):
            download_progress.update_progress(current, total)
        
        cprint(f"👀 Загружаем для предпросмотра: {media_desc}", "info")
        
        # Скачиваем файл
        download_path = await message.download_media(
            file=temp_path,
            progress_callback=progress_callback
        )
        
        # Завершаем прогресс-бар
        download_progress.finish()
        
        if not download_path:
            cprint("❌ Не удалось загрузить файл для предпросмотра", "error")
            return False
        
        cprint(f"✅ Файл загружен: {download_path}", "success")
        
        # Показываем медиа в зависимости от типа
        if media_type == "photo":
            return await preview_image(download_path)
        elif media_type == "video":
            return await preview_video(download_path)
        elif media_type == "sticker":
            return await preview_image(download_path)
        else:
            cprint(f"📄 Просмотр {media_desc} не поддерживается в консоли", "warning")
            cprint(f"💾 Файл сохранен: {download_path}", "info")
            return True
            
    except Exception as e:
        cprint(f"❌ Ошибка при просмотре медиа: {e}", "error")
        download_progress.finish()
        return False

async def preview_image(file_path):
    """Пытается открыть изображение в просмотрщике системы"""
    try:
        if os.path.exists(file_path):
            cprint(f"🖼️ Изображение сохранено: {file_path}", "success")
            
            # Попытка открыть фото
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(file_path)
                elif os.name == 'posix':  # macOS, Linux
                    os.system(f'xdg-open "{file_path}" 2>/dev/null || open "{file_path}" 2>/dev/null')
                cprint("👀 Изображение открыто в просмотрщике системы", "success")
            except Exception as e:
                cprint(f"⚠️ Не удалось открыть изображение автоматически: {e}", "warning")
                cprint("📁 Файл сохранен, откройте его вручную", "info")
            
            return True
    except Exception as e:
        cprint(f"❌ Ошибка при предпросмотре изображения: {e}", "error")
        return False

async def preview_video(file_path):
    """Показывает информацию о видеофайле"""
    try:
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            cprint(f"🎥 Видео сохранено: {file_path}", "success")
            cprint(f"💾 Размер: {format_file_size(file_size)}", "info")
            cprint("📺 Для просмотра откройте файл в видеоплеере", "info")
            return True
    except Exception as e:
        cprint(f"❌ Ошибка при предпросмотре видео: {e}", "error")
        return False

async def show_full_message(message, dialog):
    """Показывает полное содержимое сообщения"""
    print_header("Полное сообщение")
    
    # Определяем отправителя
    sender = await message.get_sender()
    sender_name = await get_sender_name(sender) if sender else "Unknown"
    
    # Форматируем дату
    date = message.date.strftime("%d.%m.%Y %H:%M:%S")
    
    # Определяем тип сообщения и информацию о медиа
    msg_type = "📝 Текст"
    media_info = ""
    
    if message.media:
        media_type, media_desc = await get_media_info(message)
        if media_type:
            emoji = random.choice(MEDIA_EMOJIS.get(media_type, ["📎"]))
            msg_type = f"{emoji} {media_desc}"
    
    # Показываем, есть ли ответ на другое сообщение
    reply_info = ""
    if message.reply_to_msg_id:
        # Получаем текст сообщения, на которое ответили
        replied_text = await get_replied_message_text(message, dialog)
        reply_info = f" ↩️ (ответ на: {replied_text})"
    
    # Показываем реакции
    reactions = ""
    if message.reactions:
        reactions = " " + " ".join([f"{r.reaction.emoticon}" if hasattr(r.reaction, 'emoticon') else "❓" 
                                  for r in message.reactions.results])
    
    # Показываем информацию о файле, если есть
    file_info = ""
    if message.file:
        file_size = message.file.size
        if file_size:
            file_size_kb = file_size / 1024
            if file_size_kb < 1024:
                file_info = f" [{file_size_kb:.1f} KB]"
            else:
                file_info = f" [{file_size_kb/1024:.1f} MB]"
    
    # Определяем, наше ли это сообщение
    me = await client.get_me()
    is_my_message = message.sender_id == me.id
    
    # Показываем статус прочтения для наших сообщений
    read_status = ""
    if is_my_message and hasattr(message, 'read') and message.read:
        read_status = " ✓✓"  # Двойная галочка для прочитанных сообщений
    elif is_my_message:
        read_status = " ✓"   # Одинарная галочка для отправленных
    
    message_indicator = "➤ " if is_my_message else ""
    
    print(f"{message_indicator}[{date}] {sender_name}: {msg_type}{file_info}{reply_info}{reactions}{read_status}")
    print("-" * 80)
    
    # Показываем полный текст сообщения
    if message.text:
        print(message.text)
    elif hasattr(message, 'message') and message.message:
        print(message.message)
    else:
        print("(сообщение не содержит текста)")
    
    print("\n" + "=" * 80)
    input("\nНажмите Enter для возврата...")

async def get_account_info():
    me = await client.get_me()
    # Получаем полную информацию о пользователе, включая био
    full_user = await client(functions.users.GetFullUserRequest(me.id))
    return me, full_user

async def update_profile(first_name=None, last_name=None, bio=None):
    try:
        await client(functions.account.UpdateProfileRequest(
            first_name=first_name,
            last_name=last_name,
            about=bio
        ))
        return True
    except Exception as e:
        print(f"Ошибка при обновлении профиля: {e}")
        return False

async def update_username(username):
    try:
        await client(functions.account.UpdateUsernameRequest(username=username))
        return True
    except Exception as e:
        print(f"Ошибка при обновлении username: {e}")
        return False

async def change_profile_photo(file_path):
    """Изменяет аватарку профиля"""
    try:
        await client(functions.photos.UploadProfilePhotoRequest(
            file=await client.upload_file(file_path)
        ))
        return True
    except Exception as e:
        print(f"Ошибка при изменении аватарки: {e}")
        return False

async def change_chat_photo(chat, file_path):
    """Изменяет аватарку чата (группы или канала)"""
    try:
        await client(functions.photos.UploadProfilePhotoRequest(
            file=await client.upload_file(file_path),
            bot=chat.bot if hasattr(chat, 'bot') else None
        ))
        return True
    except Exception as e:
        print(f"Ошибка при изменении аватарки чата: {e}")
        return False

async def set_chat_photo(chat, file_path):
    """Устанавливает аватарку для чата (группы или канала)"""
    try:
        # Загружаем файл
        uploaded_file = await client.upload_file(file_path)
        
        if isinstance(chat, types.Channel):
            # Для каналов и супергрупп
            await client(functions.channels.EditPhotoRequest(
                channel=chat,
                photo=types.InputChatUploadedPhoto(file=uploaded_file)
            ))
        else:
            # Для обычных групп
            await client(functions.messages.EditChatPhotoRequest(
                chat_id=chat.id,
                photo=types.InputChatUploadedPhoto(file=uploaded_file)
            ))
        return True
    except Exception as e:
        print(f"Ошибка при установке аватарки чата: {e}")
        return False

async def show_privacy_settings():
    global config
    
    privacy_options = {
        "last_seen": {
            "name": "Время последнего посещения",
            "options": ["все", "контакты", "никто"]
        },
        "profile_photo": {
            "name": "Фото профиля",
            "options": ["все", "контакты", " никто"]
        },
        "forwarded_messages": {
            "name": "Пересылка сообщений",
            "options": ["все", "контакты", "никто"]
        },
        "calls": {
            "name": "Звонки",
            "options": ["все", "контакты", "никто"]
        },
        "groups": {
            "name": "Группы и каналы",
            "options": ["все", "контакты", "никто"]
        },
        "read_receipts": {
            "name": "Отчеты о прочтении",
            "type": "bool"
        }
    }
    
    while True:
        print_header("Настройки конфиденциальности")
        
        for i, (key, setting) in enumerate(privacy_options.items()):
            if "options" in setting:
                current_value = config["privacy"][key]
                print(f"{i+1}. {setting['name']}: {current_value}")
            else:
                current_value = "вкл" if config["privacy"][key] else "выкл"
                print(f"{i+1}. {setting['name']}: {current_value}")
        
        print("\n0. Назад")
        
        choice = cinput("\nВыберите настройку для изменения: ", "info")
        
        if choice == '0':
            break
        
        try:
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(privacy_options):
                key = list(privacy_options.keys())[choice_idx]
                setting = privacy_options[key]
                
                if "options" in setting:
                    print(f"\n{setting['name']}:")
                    for i, option in enumerate(setting["options"]):
                        print(f"{i+1}. {option}")
                    
                    option_choice = input("Выберите вариант: ")
                    
                    try:
                        option_idx = int(option_choice) - 1
                        if 0 <= option_idx < len(setting["options"]):
                            config["privacy"][key] = setting["options"][option_idx]
                            save_config(config)
                            print("Настройка сохранена!")
                        else:
                            print("Неверный выбор!")
                    except ValueError:
                        print("Введите число!")
                else:
                    config["privacy"][key] = not config["privacy"][key]
                    save_config(config)
                    print(f"{setting['name']} {'включены' if config['privacy'][key] else 'выключены'}!")
            else:
                print("Неверный выбор!")
        except ValueError:
            print("Введите число!")

async def show_notification_settings():
    global config
    
    notification_options = {
        "private_chats": {
            "name": "Личные чаты",
            "type": "bool"
        },
        "groups": {
            "name": "Группы",
            "type": "bool"
        },
        "channels": {
            "name": "Каналы",
            "type": "bool"
        },
        "sound": {
            "name": "Звук",
            "type": "bool"
        },
        "preview": {
            "name": "Превью сообщений",
            "type": "bool"
        }
    }
    
    while True:
        print_header("Настройки уведомлений")
        
        for i, (key, setting) in enumerate(notification_options.items()):
            current_value = "вкл" if config["notifications"][key] else "выкл"
            print(f"{i+1}. {setting['name']}: {current_value}")
        
        cprint("\n0. Назад", "secondary")
        
        choice = cinput("\nВыберите настройку для изменения: ", "info")
        
        if choice == '0':
            break
        
        try:
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(notification_options):
                key = list(notification_options.keys())[choice_idx]
                setting = notification_options[key]
                
                if setting["type"] == "bool":
                    config["notifications"][key] = not config["notifications"][key]
                    save_config(config)
                    print(f"{setting['name']} {'включены' if config['notifications'][key] else 'выключены'}!")
            else:
                print("Неверный выбор!")
        except ValueError:
            cprint("Введите число!", "warning")

async def show_appearance_settings():
    global config
    
    appearance_options = {
        "theme": {
            "name": "Цветовая тема",
            "options": ["default", "dark", "light", "blue", "purple", "matrix"]
        },
        "message_text_size": {
            "name": "Размер текста",
            "options": ["маленький", "средний", "большой"]
        },
        "animate_emojis": {
            "name": "Анимированные эмодзи",
            "type": "bool"
        },
        "show_media_previews": {
            "name": "Превью медиа",
            "type": "bool"
        },
        "use_colors": {
            "name": "Цветной интерфейс",
            "type": "bool"
        }
    }
    
    while True:
        print_header("Настройки внешнего вида")
        
        for i, (key, setting) in enumerate(appearance_options.items()):
            if "options" in setting:
                current_value = config["appearance"][key]
                # Для темы показываем понятные названия
                if key == "theme":
                    theme_names = {
                        "default": "Стандартная (зеленая)",
                        "dark": "Темная (синяя)",
                        "light": "Светлая (голубая, не рекомендую ставить)",
                        "blue": "Синяя",
                        "purple": "Фиолетовая",
                        "matrix": "Матрица"
                    }
                    display_value = theme_names.get(current_value, current_value)
                else:
                    display_value = current_value
                cprint(f"{i+1}. {setting['name']}: {display_value}", "primary")
            else:
                current_value = "вкл" if config["appearance"][key] else "выкл"
                cprint(f"{i+1}. {setting['name']}: {current_value}", "primary")
        
        cprint("\n0. Назад", "secondary")
        
        choice = cinput("\nВыберите настройку для изменения: ", "info")
        
        if choice == '0':
            break
        
        try:
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(appearance_options):
                key = list(appearance_options.keys())[choice_idx]
                setting = appearance_options[key]
                
                if "options" in setting:
                    cprint(f"\n{setting['name']}:", "header")
                    for i, option in enumerate(setting["options"]):
                        # Для темы показываем понятные названия
                        if key == "theme":
                            theme_names = {
                                "default": "Стандартная (зеленая)",
                                "dark": "Темная (синяя)",
                                "light": "Светлая (голубая, не рекомендую ставить)",
                                "blue": "Синяя",
                                "purple": "Фиолетовая",
                                "matrix": "Матрица (зеленая)"
                            }
                            display_option = theme_names.get(option, option)
                        else:
                            display_option = option
                        cprint(f"{i+1}. {display_option}", "primary")
                    
                    option_choice = cinput("Выберите вариант: ", "info")
                    
                    try:
                        option_idx = int(option_choice) - 1
                        if 0 <= option_idx < len(setting["options"]):
                            config["appearance"][key] = setting["options"][option_idx]
                            save_config(config)
                            cprint("Настройка сохранена!", "success")
                        else:
                            cprint("Неверный выбор!", "error")
                    except ValueError:
                        cprint("Введите число!", "error")
                else:
                    config["appearance"][key] = not config["appearance"][key]
                    save_config(config)
                    status = "включено" if config["appearance"][key] else "выключено"
                    cprint(f"{setting['name']} {status}!", "success")
            else:
                cprint("Неверный выбор!", "error")
        except ValueError:
            cprint("Введите число!", "error")

async def preview_theme(theme_name):
    """Показывает предпросмотр темы"""
    print_header(f"Предпросмотр темы: {theme_name}")
    
    # Сохраняем текущую тему
    current_theme = config["appearance"]["theme"]
    
    # Временно устанавливаем новую тему
    config["appearance"]["theme"] = theme_name
    
    # Показываем пример интерфейса
    cprint("Это пример текста в выбранной теме", "primary")
    cprint("Заголовок раздела", "header")
    cprint("Информационное сообщение", "info")
    cprint("Успешная операция", "success")
    cprint("Предупреждение", "warning")
    cprint("Ошибка", "error")
    cprint("Второстепенная информация", "secondary")
    cprint("Выделенный текст", "highlight")
    
    # Восстанавливаем тему
    config["appearance"]["theme"] = current_theme
    
    cinput("\nНажмите Enter для возврата...", "secondary")

async def show_data_settings():
    global config
    
    # Убедимся, что все необходимые ключи существуют
    if "stickers" not in config["data"]["auto_download"]:
        config["data"]["auto_download"]["stickers"] = True
        save_config(config)
    
    data_options = {
        "photos": {
            "name": "Фотографии",
            "type": "bool"
        },
        "videos": {
            "name": "Видео",
            "type": "bool"
        },
        "files": {
            "name": "Файлы",
            "type": "bool"
        },
        "voice_messages": {
            "name": "Голосовые сообщения",
            "type": "bool"
        },
        "stories": {
            "name": "Истории",
            "type": "bool"
        },
        "stickers": {
            "name": "Стикеры",
            "type": "bool"
        }
    }
    
    while True:
        print_header("Настройки данных и хранилища")
        
        print("Автоскачивание:")
        for i, (key, setting) in enumerate(data_options.items()):
            # Безопасное получение значения с fallback на True
            current_value = config["data"]["auto_download"].get(key, True)
            status = "вкл" if current_value else "выкл"
            print(f"{i+1}. {setting['name']}: {status}")
        
        save_to_gallery = "вкл" if config["data"].get("save_to_gallery", True) else "выкл"
        print(f"7. Сохранять в галерею: {save_to_gallery}")
        
        data_usage = config["data"].get("data_usage", "medium")
        print(f"8. Использование данных: {data_usage}")
        
        cprint("\n0. Назад", "secondary")
        
        choice = cinput("\nВыберите настройку для изменения: ", "info")
        
        if choice == '0':
            break
        
        try:
            choice_idx = int(choice)
            if 1 <= choice_idx <= len(data_options):
                key = list(data_options.keys())[choice_idx - 1]
                setting = data_options[key]
                
                # Безопасное изменение значения
                current_val = config["data"]["auto_download"].get(key, True)
                config["data"]["auto_download"][key] = not current_val
                save_config(config)
                new_status = "включено" if config["data"]["auto_download"][key] else "выключено"
                print(f"Автоскачивание {setting['name']} {new_status}!")
            
            elif choice_idx == 7:
                current_val = config["data"].get("save_to_gallery", True)
                config["data"]["save_to_gallery"] = not current_val
                save_config(config)
                new_status = "включено" if config["data"]["save_to_gallery"] else "выключено"
                print(f"Сохранение в галерею {new_status}!")
            
            elif choice_idx == 8:
                cprint("\nИспользование данных:", "info")
                cprint("1. Низкое", "secondary")
                cprint("2. Среднее", "warning")
                cprint("3. Высокое", "error")
                
                usage_choice = input("Выберите вариант: ")
                
                try:
                    usage_idx = int(usage_choice)
                    if usage_idx == 1:
                        config["data"]["data_usage"] = "низкое"
                    elif usage_idx == 2:
                        config["data"]["data_usage"] = "среднее"
                    elif usage_idx == 3:
                        config["data"]["data_usage"] = "высокое"
                    else:
                        print("Неверный выбор!")
                        continue
                    
                    save_config(config)
                    cprint("Настройка сохранена!", "success")
                except ValueError:
                    cprint("Введите число!", "warning")
            
            else:
                print("Неверный выбор!")
        except ValueError:
            print("Введите число!")

async def show_language_settings():
    global config
    
    languages = ["Русский", "English", "Español", 'Deutsch', 'Français', '中文']
    
    while True:
        print_header("Настройки языка")
        
        cprint(f"Текущий язык: {config['language']}", "info")
        cprint("\nДоступные языки:", "info")
        for i, lang in enumerate(languages):
            print(f"{i+1}. {lang}")
        
        cprint("\n0. Назад", "secondary")
        
        choice = cinput("\nВыберите язык: ", "info")
        
        if choice == '0':
            break
        
        try:
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(languages):
                config["language"] = languages[choice_idx]
                save_config(config)
                print(f"Язык изменен на {languages[choice_idx]}!")
            else:
                print("Неверный выбор!")
        except ValueError:
            print("Введите число!")

async def show_account_settings():
    me, full_user = await get_account_info()
    
    while True:
        print_header("Настройки аккаунта")
        print(f"Имя: {me.first_name}")
        print(f"Фамилия: {me.last_name}")
        print(f"Username: @{me.username}")
        print(f"Био: {full_user.full_user.about}")
        print("\n1. Изменить имя")
        print("2. Изменить фамилию")
        print("3. Изменить username")
        print("4. Изменить био")
        print("5. Изменить аватарку")  
        cprint("6. Назад", "secondary")  
        
        choice = input("\nВыберите действие: ")
        
        if choice == '1':
            new_first_name = cinput("Новое имя: ", "info")
            if new_first_name and await update_profile(first_name=new_first_name):
                print("Имя успешно изменено!")
                me, full_user = await get_account_info()
        
        elif choice == '2':
            new_last_name = cinput("Новая фамилию: ", "info")
            if await update_profile(last_name=new_last_name):
                print("Фамилия успешно изменена!")
                me, full_user = await get_account_info()
        
        elif choice == '3':
            new_username = cinput("Новый username (без @): ", "info")
            if new_username and await update_username(new_username):
                print("Username успешно изменен!")
                me, full_user = await get_account_info()
        
        elif choice == '4':
            new_bio = cinput("Новое био: ", "info")
            if await update_profile(bio=new_bio):
                print("Био успешно изменено!")
                me, full_user = await get_account_info()
        
        elif choice == '5':  # Новый функционал
            file_path = file_explorer()
            if file_path and os.path.exists(file_path):
                # Проверяем, что файл является изображением
                mime_type, _ = mimetypes.guess_type(file_path)
                if mime_type and mime_type.startswith('image/'):
                    success = await change_profile_photo(file_path)
                    if success:
                        cprint("Аватарка успешно изменена!", "success")
                    else:
                        print("Не удалось изменить аватарку!", "error")
                else:
                    cprint("Файл должен быть изображением!", "warning")
        
        elif choice == '6':  # Теперь "Назад" на позиции 6
            break
        
        else:
            cprint("Неверный выбор!", "secondary")

async def show_proxy_settings():
    """Настройки прокси с автоматической проверкой"""
    global config, client
    
    # Список поддерживаемых типов прокси
    supported_proxy_types = ['socks5', 'http', 'socks4']
    
    while True:
        print_header("Настройки прокси")
        
        status = "🟢 Включен" if config["proxy"]["enabled"] else "🔴 Выключен"
        print(f"Статус: {status}")
        print(f"Тип: {config['proxy']['type']}")
        print(f"Адрес: {config['proxy']['host']}:{config['proxy']['port']}")
        
        # Проверяем и показываем задержку текущего прокси
        if config["proxy"]["enabled"] and config["proxy"]["host"] and config["proxy"]["port"]:
            print("Проверяем задержку текущего прокси...")
            proxy_config = config["proxy"].copy()
            is_working, delay = await check_proxy(f"{proxy_config['type']}://{proxy_config['host']}:{proxy_config['port']}")
            if is_working:
                cprint(f"Задержка: {delay}мс", "info")
            else:
                cprint("❌ Прокси не работает!", "warning")
        
        if config["proxy"]["username"]:
            print(f"Логин: {config['proxy']['username']}")
        if config["proxy"]["password"]:
            print(f"Пароль: {'*' * len(config['proxy']['password'])}")
        
        print("\nДействия:")
        cprint("1. Включить/выключить прокси", "primary")
        print("2. Изменить настройки прокси")
        print("3. Получить прокси из онлайн-источников")
        print("4. Протестировать текущий прокси")
        cprint("0. Назад", "secondary")
        
        choice = cinput("\nВыберите действие: ", "info")
        
        if choice == '1':
            config["proxy"]["enabled"] = not config["proxy"]["enabled"]
            save_config(config)
            status = "включен" if config["proxy"]["enabled"] else "выключен"
            print(f"Прокси {status}!")
            
            # Если включили прокси, проверяем его
            if config["proxy"]["enabled"]:
                if not await test_proxy_connection():
                    cprint("⚠️ Внимание: прокси не работает!", "warning")
            
        elif choice == '2':
            print("\nВведите новые настройки прокси:")
            new_type = input(f"Тип ({'/'.join(supported_proxy_types)}): ") or config["proxy"]["type"]
            if new_type not in supported_proxy_types:
                print(f"Неверный тип прокси! Используйте один из: {', '.join(supported_proxy_types)}")
                input("\nНажмите Enter для продолжения...")
                continue
                
            config["proxy"]["type"] = new_type
            config["proxy"]["host"] = input("Хост: ") or config["proxy"]["host"]
            config["proxy"]["port"] = input("Порт: ") or config["proxy"]["port"]
            config["proxy"]["username"] = input("Логин (если есть): ") or config["proxy"]["username"]
            config["proxy"]["password"] = input("Пароль (если есть): ") or config["proxy"]["password"]
            
            save_config(config)
            print("Настройки прокси сохранены!")
            
            # Проверяем новый прокси
            if config["proxy"]["enabled"]:
                if await test_proxy_connection():
                    print("✅ Прокси работает нормально!")
                else:
                    print("❌ Прокси не работает!")
                    disable = input("Отключить прокси? (y/n) [n]: ").strip().lower()
                    if disable == 'y':
                        config["proxy"]["enabled"] = False
                        save_config(config)
                        print("Прокси отключен.")
            
        elif choice == '3':
            await fetch_online_proxies()
            
        elif choice == '4':
            if await test_proxy_connection():
                print("✅ Прокси работает нормально!")
            else:
                print("❌ Прокси не работает!")
            
        elif choice == '0':
            break
            
        else:
            print("Неверный выбор!")
        
        input("\nНажмите Enter для продолжения...")

async def fetch_online_proxies():
    """Получение прокси из онлайн-источников с улучшенной обработкой ошибок"""
    global proxy_cache
    
    print_header("Получение прокси из онлайн-источников")
    
    cprint("Доступные источники:", "info")
    sources = list(PROXY_CONFIG.keys())
    for i, source in enumerate(sources):
        print(f"{i+1}. {PROXY_CONFIG[source]['name']}")
    
    cprint("0. Назад", "secondary")
    
    try:
        choice = int(input("\nВыберите источник: "))
        if choice == 0:
            return
            
        source_key = sources[choice-1]
        source_config = PROXY_CONFIG[source_key]
        
        print(f"\nПолучение прокси из {source_config['name']}...")
        
        # Получаем список прокси
        proxies = await fetch_proxies_from_source(source_config)
        
        if not proxies:
            cprint(f"Не удалось получить прокси из {source_config['name']}!", "warning")
            print("Возможные причины:")
            print("1. Нет интернет-подключения")
            print("2. Источник временно недоступен")
            print("3. Файл перемещен или удален")
            
            # Для MTProto источников предлагаем альтернативный вариант
            if source_key == "mtproto_solispirit":
                print("\nВы можете ввести MTProto прокси вручную:")
                proxy_input = input("Введите прокси в формате server:port:secret: ")
                if proxy_input:
                    proxies = [proxy_input]
                else:
                    input("\nНажмите Enter для продолжения...")
                    return
        
        if not proxies:
            input("\nНажмите Enter для продолжения...")
            return
        
        # Для MTProto источников используем специальную проверку
        if source_key == "mtproto_solispirit":
            print("Проверка MTProto прокси... Это может занять некоторое время.")
            working_proxies = []
            
            # Проверяем прокси по одному, пока не наберем 10 рабочих
            for i, proxy in enumerate(proxies):
                print(f"Проверка прокси {i+1}/{len(proxies)}...")
                is_working, delay = await check_proxy(proxy, timeout=8)
                if is_working:
                    working_proxies.append((proxy, delay))
                    print(f"Найдено рабочих прокси: {len(working_proxies)}/10")
                    
                    if len(working_proxies) >= 10:
                        break
                else:
                    print("Прокси не работает, пропускаем...")
        else:
            # Для обычных прокси используем стандартную проверку
            working_proxies = await get_working_proxies(proxies, max_working=10, timeout=5)
        
        if not working_proxies:
            print("Не найдено рабочих прокси!")
            input("\nНажмите Enter для продолжения...")
            return
        
        # Сохраняем в кеш
        proxy_cache[source_key] = [proxy for proxy, delay in working_proxies]
        save_proxy_cache()
        
        # Показываем рабочие прокси
        print_header(f"Рабочие прокси от {source_config['name']}")
        for i, (proxy, delay) in enumerate(working_proxies):
            print(f"{i+1}. {proxy} [задержка: {delay}мс]")
                
        # Предлагаем выбрать прокси для использования
        use_proxy = input("\nИспользовать один из этих прокси? (y/n): ").lower()
        if use_proxy == 'y':
            try:
                proxy_num = int(input("Номер прокси: "))
                if 1 <= proxy_num <= len(working_proxies):
                    proxy_str, delay = working_proxies[proxy_num-1]
                    
                    # Парсим строку прокси
                    proxy_config = parse_proxy_string(proxy_str)
                    
                    if not proxy_config:
                        print("Не удалось распарсить прокси!")
                        input("\nНажмите Enter для продолжения...")
                        return
                    
                    # Обновляем конфиг
                    config["proxy"].update(proxy_config)
                    config["proxy"]["enabled"] = True
                    save_config(config)
                    print(f"Прокси настроен и включен! Задержка: {delay}мс")
                    
                    # Переподключаем клиент
                    await safe_disconnect()
                    await initialize_client()
                else:
                    print("Неверный номер прокси!")
            except ValueError:
                print("Введите число!")
        else:
            print("Прокси не был выбран.")
            
    except (ValueError, IndexError):
        print("Неверный выбор!")
    
    cinput("\nНажмите Enter для продолжения...", "secondary")

async def check_mtproto_proxy(proxy_str, timeout=10):
    """
    Проверяет работоспособность MTProto прокси и возвращает задержку
    """
    try:
        # Парсим MTProxy строку
        # Формат: server:port:secret или tg://proxy?server=...&port=...&secret=...
        if proxy_str.startswith('tg://'):
            # Это ссылка, используем urllib для парсинга
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(proxy_str)
            query = parse_qs(parsed.query)
            server = query.get('server', [None])[0]
            port = int(query.get('port', [0])[0])
            secret = query.get('secret', [None])[0]
        else:
            # Предполагаем формат server:port:secret
            parts = proxy_str.split(':')
            if len(parts) < 3:
                return False, None
            server = parts[0]
            port = int(parts[1])
            secret = parts[2]

        # Создаем временный клиент с этим прокси
        proxy = (server, port, secret)
        temp_client = TelegramClient(
            None,  # Без сессии
            API_ID,
            API_HASH,
            proxy=proxy
        )

        start_time = time.time()
        await temp_client.connect()
        
        # Проверяем подключение, отправив запрос на получение текущего пользователя
        # Но мы не авторизованы, поэтому просто проверяем, что соединение установлено
        try:
            # Попробуем получить конфигурацию
            await temp_client(functions.help.GetConfigRequest())
            end_time = time.time()
            delay = round((end_time - start_time) * 1000)
            await temp_client.disconnect()
            return True, delay
        except:
            await temp_client.disconnect()
            return False, None

    except Exception as e:
        return False, None

def parse_proxy_string(proxy_str):
    """Парсит строку прокси в формат конфига"""
    proxy_config = {
        "enabled": True,
        "type": "socks5",  # по умолчанию
        "host": "",
        "port": "",
        "username": "",
        "password": "",
        "secret": ""  # для MTProto
    }
    
    try:
        # Обрабатываем MTProto прокси
        if proxy_str.startswith('tg://') or (len(proxy_str.split(':')) >= 3 and not proxy_str.startswith(('http://', 'socks5://', 'socks4://'))):
            # Это MTProto прокси
            if proxy_str.startswith('tg://'):
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(proxy_str)
                query = parse_qs(parsed.query)
                proxy_config["host"] = query.get('server', [None])[0]
                proxy_config["port"] = query.get('port', [0])[0]
                proxy_config["secret"] = query.get('secret', [None])[0]
                proxy_config["type"] = "mtproto"
            else:
                parts = proxy_str.split(':')
                proxy_config["host"] = parts[0]
                proxy_config["port"] = parts[1]
                if len(parts) > 2:
                    proxy_config["secret"] = parts[2]
                proxy_config["type"] = "mtproto"
        else:
            # Обрабатываем HTTP/SOCKS прокси
            if "://" in proxy_str:
                proxy_type, rest = proxy_str.split("://", 1)
                proxy_config["type"] = proxy_type
            else:
                rest = proxy_str
            
            if "@" in rest:
                auth, hostport = rest.split("@", 1)
                if ":" in auth:
                    username, password = auth.split(":", 1)
                    proxy_config["username"] = username
                    proxy_config["password"] = password
                host, port = hostport.split(":", 1)
            else:
                host, port = rest.split(":", 1)
                
            proxy_config["host"] = host
            proxy_config["port"] = port
        
    except Exception as e:
        print(f"Не удалось распарсить прокси {proxy_str}: {e}")
        return None
    
    return proxy_config

async def safe_disconnect():
    """Безопасное отключение клиента"""
    global client
    if client:
        try:
            await client.disconnect()
        except:
            pass
        client = None

async def test_proxy_connection(proxy_config=None):
    """Тестирует подключение через прокси"""
    if proxy_config is None:
        proxy_config = config["proxy"]
    
    if not proxy_config["enabled"] or not proxy_config["host"] or not proxy_config["port"]:
        return False
    
    print("Тестирование подключения через прокси...")
    
    try:
        # Создаем временного клиента для тестирования
        test_client = await create_telegram_client_with_config(proxy_config)
        await test_client.connect()
        
        # Проверяем авторизацию
        if not await test_client.is_user_authorized():
            print("Клиент не авторизован!")
            await test_client.disconnect()
            return False
        
        # Получаем информацию о себе
        me = await test_client.get_me()
        print(f"Успешное подключение как: {me.first_name}")
        
        await test_client.disconnect()
        return True
        
    except Exception as e:
        print(f"Ошибка подключения через прокси: {e}")
        return False

async def create_telegram_client_with_config(proxy_config):
    """Создает клиента с указанной конфигурацией прокси"""
    if proxy_config["enabled"] and proxy_config["host"] and proxy_config["port"]:
        proxy_type = proxy_config["type"]
        proxy_host = proxy_config["host"]
        proxy_port = int(proxy_config["port"])
        proxy_username = proxy_config.get("username") or None
        proxy_password = proxy_config.get("password") or None
        proxy_secret = proxy_config.get("secret") or None

        # Формируем кортеж для прокси в правильном формате
        if proxy_type == "mtproto":
            proxy = (proxy_host, proxy_port, proxy_secret)
        else:
            proxy = (proxy_type, proxy_host, proxy_port, proxy_username, proxy_password)
    else:
        proxy = None
    
    return TelegramClient(SESSION_FILE, API_ID, API_HASH, proxy=proxy)
    

async def fetch_proxies_from_source(source_config):
    """Получает прокси из указанного источника с улучшенной обработкой ошибок"""
    try:
        async with aiohttp.ClientSession() as session:
            proxies = []
            for proxy_type, url_suffix in source_config["types"].items():
                url = f"{source_config['base_url']}{url_suffix}"
                try:
                    # Добавляем заголовки чтобы избежать блокировки
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    }
                    
                    async with session.get(url, headers=headers, timeout=30) as response:
                        if response.status == 200:
                            text = await response.text()
                            # Обрабатываем разные форматы прокси
                            lines = []
                            for line in text.split('\n'):
                                line = line.strip()
                                if line and not line.startswith('#'):  # Пропускаем пустые строки и комментарии
                                    lines.append(line)
                            proxies.extend(lines)
                            print(f"Получено {len(lines)} прокси из {url}")
                        else:
                            print(f"Ошибка HTTP {response.status} при получении {url}")
                except asyncio.TimeoutError:
                    print(f"Таймаут при запросе к {url}")
                except Exception as e:
                    print(f"Ошибка при запросе к {url}: {e}")
            return proxies
    except Exception as e:
        cprint(f"Общая ошибка при получении прокси из {source_config['name']}: {e}", "error")
        return None

def save_proxy_cache():
    """Сохраняет кеш прокси в файл"""
    with open(PROXY_CACHE_FILE, 'w') as f:
        json.dump(proxy_cache, f, indent=4)

def load_proxy_cache():
    """Загружает кеш прокси из файла"""
    global proxy_cache
    try:
        with open(PROXY_CACHE_FILE, 'r') as f:
            proxy_cache = json.load(f)
    except FileNotFoundError:
        proxy_cache = {}

async def test_connection():
    """Тестирует подключение через текущий прокси"""
    print("Тестирование подключения...")
    
    try:
        # Создаем временного клиента для тестирования
        test_client = await create_telegram_client()
        await test_client.connect()
        
        # Проверяем авторизацию
        if not await test_client.is_user_authorized():
            print("Клиент не авторизован!")
            await test_client.disconnect()
            return False
        
        # Получаем информацию о себе
        me = await test_client.get_me()
        print(f"Успешное подключение как: {me.first_name}")
        
        await test_client.disconnect()
        return True
        
    except Exception as e:
        print(f"Ошибка подключения: {e}")
        return False

async def create_telegram_client():
    """Создает экземпляр TelegramClient с учетом настроек прокси"""
    global config
    
    if config["proxy"]["enabled"] and config["proxy"]["host"] and config["proxy"]["port"]:
        proxy_type = config["proxy"]["type"]
        proxy_host = config["proxy"]["host"]
        proxy_port = int(config["proxy"]["port"])
        proxy_username = config["proxy"].get("username") or None
        proxy_password = config["proxy"].get("password") or None
        proxy_secret = config["proxy"].get("secret") or None

        # Формируем кортеж для прокси в правильном формате
        if proxy_type == "mtproto":
            # Для MTProto прокси используем специальный формат
            proxy = (proxy_host, proxy_port, proxy_secret)
        else:
            proxy = (proxy_type, proxy_host, proxy_port, proxy_username, proxy_password)
    else:
        proxy = None
    
    return TelegramClient(SESSION_FILE, API_ID, API_HASH, proxy=proxy)

async def initialize_client():
    """Инициализирует клиента Telegram с проверкой прокси"""
    global client
    
    # Спрашиваем, использовать ли прокси
    use_proxy = cinput("Хотите использовать прокси? (y/n) [y]: ", "info").strip().lower()
    if use_proxy == '' or use_proxy == 'y':
        config["proxy"]["enabled"] = True
        print("Использование прокси включено.")
        
        # Проверяем, настроен ли прокси
        if not config["proxy"]["host"] or not config["proxy"]["port"]:
            print("Прокси не настроен. Переходим к настройке...")
            await show_proxy_settings()
        else:
            # Проверяем работоспособность прокси
            if not await test_proxy_connection():
                print("Текущий прокси не работает.")
                choice = input("Хотите настроить новый прокси? (y/n) [y]: ").strip().lower()
                if choice == '' or choice == 'y':
                    await show_proxy_settings()
                else:
                    cprint("Продолжаем без прокси.", "secondary")
                    config["proxy"]["enabled"] = False
    else:
        config["proxy"]["enabled"] = False
        print("Использование прокси отключено.")
    
    save_config(config)
    
    # Создаем клиента с текущими настройками
    client = await create_telegram_client()
    await client.start()

async def check_proxy(proxy_str, timeout=10):
    """
    Проверяет работоспособность прокси и возвращает задержку
    """
    # Определяем тип прокси по строке
    if proxy_str.startswith('tg://') or (len(proxy_str.split(':')) >= 3 and not proxy_str.startswith(('http://', 'socks5://', 'socks4://'))):
        # Это MTProto прокси
        return await check_mtproto_proxy(proxy_str, timeout)
    else:
        # Это HTTP/SOCKS прокси
        try:
            # Парсим прокси строку
            if "://" in proxy_str:
                proxy_type, rest = proxy_str.split("://", 1)
            else:
                proxy_type = "http"
                rest = proxy_str
            
            # Формируем URL для проверки
            test_url = "http://www.google.com"
            
            # Создаем сессию с прокси
            connector = aiohttp.TCPConnector(ssl=False)
            proxy_url = f"http://{rest}" if proxy_type == "http" else f"socks5://{rest}"
            
            start_time = time.time()
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(test_url, proxy=proxy_url, timeout=timeout) as response:
                    if response.status == 200:
                        end_time = time.time()
                        delay = round((end_time - start_time) * 1000)
                        return True, delay
            return False, None
        except:
            return False, None

async def get_working_proxies(proxies, max_working=10, timeout=5):
    """
    Проверяет список прокси и возвращает рабочие с задержкой
    """
    working_proxies = []
    
    print(f"Проверяем {len(proxies)} прокси...")
    
    # Создаем задачи для проверки всех прокси
    tasks = []
    for proxy in proxies:
        tasks.append(check_proxy(proxy, timeout))
    
    # Запускаем все задачи параллельно
    results = await asyncio.gather(*tasks)
    
    # Собираем рабочие прокси
    for i, (is_working, delay) in enumerate(results):
        if is_working and delay:
            working_proxies.append((proxies[i], delay))
            
            # Останавливаемся, когда набрали нужное количество
            if len(working_proxies) >= max_working:
                break
    
    # Сортируем по задержке (от меньшей к большей)
    working_proxies.sort(key=lambda x: x[1])
    
    return working_proxies

# настройке, на стройке на какой стройке? 👷
async def show_settings():
    while True:
        print_header("Настройки")
        print("1. Конфиденциальность и безопасность")
        print("2. Уведомления и звуки")
        cprint("3. Внешний вид", "primary")
        print("4. Данные и хранилище")
        print("5. Язык")
        print("6. Настройки аккаунта")
        print("7. Ночной режим")
        print("8. Настройки прокси")
        print("9. Проверить обновления")  # Новый пункт
        cprint("0. Назад", "secondary")
        
        choice = cinput("\nВыберите раздел настроек: ", "info")
        
        if choice == '1':
            await show_privacy_settings()
        elif choice == '2':
            await show_notification_settings()
        elif choice == '3':
            await show_appearance_settings()
        elif choice == '4':
            await show_data_settings()
        elif choice == '5':
            await show_language_settings()
        elif choice == '6':
            await show_account_settings()
        elif choice == '7':
            config["auto_night_mode"] = not config["auto_night_mode"]
            save_config(config)
            status = "включен" if config["auto_night_mode"] else "выключен"
            print(f"Автономный ночной режим {status}!")
        elif choice == '8':
            await show_proxy_settings()
        elif choice == '9':  # Новый пункт для проверки обновлений
            await check_for_updates()
            cinput("\nНажмите Enter для продолжения...", "secondary")
        elif choice == '0':
            break
        else:
            print("Неверный выбор!")

async def show_summary():
    """Показывает итоговую информацию о клиенте"""
    print_header("Итоги")
    
    # Получаем информацию об аккаунте
    me, full_user = await get_account_info()
    
    # Получаем диалоги
    dialogs = await client.get_dialogs()
    
    # Считаем статистику
    total_dialogs = len(dialogs)
    private_chats = sum(1 for d in dialogs if isinstance(d.entity, types.User))
    groups = sum(1 for d in dialogs if isinstance(d.entity, types.Chat))
    channels = sum(1 for d in dialogs if isinstance(d.entity, types.Channel))
    
    total_unread = sum(d.unread_count for d in dialogs)
    
    print(f"👨‍💻 Версия LinuxGram: {VERSION}")
    print(f"👤 Пользователь: {me.first_name} {me.last_name or ''} (@{me.username})")
    print(f"📊 Всего диалогов: {total_dialogs}")
    print(f"   👥 Личные чаты: {private_chats}")
    print(f"   👥 Группы: {groups}")
    print(f"   📢 Каналы: {channels}")
    print(f"📨 Непрочитанных сообщений: {total_unread}")
    print(f"📁 Архивных чатов: {len(folders["Архив"])}")
    print(f"🌐 Язык интерфейса: {config['language']}")
    print(f"🎨 Тема: {config['appearance']['theme']}")
    print(f"💾 Автоскачивание: {'включено' if any(config['data']['auto_download'].values()) else 'выключено'}")
    
    # Показываем последние действия
    print("\n📋 Доступные функции:")
    print("  • Отправка и получение сообщений")
    print("  • Поддержка стикеров и медиафайлов")
    print("  • Ответы на сообщения и реакции")
    print("  • Поиск по сообщениям")
    print("  • Редактирование сообщений")
    print("  • Скачивание файлов")
    print("  • Просмотр участников групп/каналов")
    print("  • Настройки конфиденциальности")
    print("  • Настройки уведомлений")
    print("  • Настройки внешнего вида")
    print("  • Настройки данных и хранилища")
    print("  • Смена языка интерфейса")
    print("  • Архивирование чатов")
    print("  • Поиск контактов")
    print("  • Просмотр профилей пользователей")
    
    print("\n" + "=" * 80)
    input("\nНажмите Enter для возврата...")

async def toggle_chat_archive(dialog):
    """Архивирует или разархивирует чат"""
    dialog_id = str(dialog.id)
    
    # Удаляем чат из всех папок (кроме Архива)
    for folder_name in folders:
        if folder_name != "Архив" and dialog_id in folders[folder_name]:
            folders[folder_name].remove(dialog_id)
    
    # Добавляем или удаляем из архива
    if dialog_id in folders["Архив"]:
        folders["Архив"].remove(dialog_id)
        action = "разархивирован"
        # Возвращаем в папку "Все чаты"
        if dialog_id not in folders["Все чаты"]:
            folders["Все чаты"].append(dialog_id)
    else:
        folders["Архив"].append(dialog_id)
        action = "архивирован"
    
    save_folders(folders)
    print(f"Чат {action}!")
    await asyncio.sleep(1)  # Небольшая пауза для отображения сообщения
    
def file_explorer(start_path="."):
    """Простой файловый проводник"""
    current_path = os.path.abspath(start_path)
    
    while True:
        print_header(f"Проводник: {current_path}")
        
        # Получаем список файлов и папок
        items = []
        try:
            # Добавляем ссылку на родительскую директорию (кроме корневой)
            if current_path != os.path.abspath(".") and os.path.dirname(current_path) != current_path:
                items.append(("📁", "..", "родительская папка"))
            
            for item in os.listdir(current_path):
                item_path = os.path.join(current_path, item)
                if os.path.isdir(item_path):
                    items.append(("📁", item, "папка"))
                else:
                    # Определяем тип файла по расширению
                    ext = os.path.splitext(item)[1].lower()
                    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                        icon = "🖼️"
                    elif ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
                        icon = "🎥"
                    elif ext in ['.mp3', '.wav', '.ogg', '.flac']:
                        icon = "🎵"
                    elif ext in ['.txt', '.doc', '.docx', '.pdf', '.rtf']:
                        icon = "📄"
                    elif ext in ['.zip', '.rar', '.7z', '.tar', '.gz']:
                        icon = "📦"
                    else:
                        icon = "📎"
                    try:
                        size = os.path.getsize(item_path)
                        size_str = f"{size/1024:.1f} KB" if size < 1024*1024 else f"{size/(1024*1024):.1f} MB"
                    except OSError:
                        size_str = "недоступен"
                    items.append((icon, item, size_str))
        except PermissionError:
            print("Нет доступа к этой папке!")
            input("\nНажмите Enter для возврата...")
            return None
        
        if not items:
            print("Папка пуста!")
            input("\nНажмите Enter для возврата...")
            return None
        
        # Выводим список
        print("Содержимое:")
        for i, (icon, name, desc) in enumerate(items):
            if desc == "родительская папка":
                print(f"{i+1:2d}. {icon} {name} ({desc})")
            elif desc == "папка":
                print(f"{i+1:2d}. {icon} {name}/ ({desc})")
            else:
                print(f"{i+1:2d}. {icon} {name} ({desc})")
        
        cprint("\nДействия:", "info")
        print("0. Назад к чату")
        if current_path != os.path.abspath("."):
            print("h. Домой (текущая директория скрипта)")
        print("u. На уровень вверх")
        print("Введите номер элемента для выбора или путь для перехода")
        
        choice = input("\nВаш выбор: ").strip()
        
        if choice == '0':
            return None
        elif choice.lower() == 'u':
            # Подняться на уровень вверх
            parent_path = os.path.dirname(current_path)
            if os.path.exists(parent_path) and parent_path != current_path:
                current_path = parent_path
            else:
                print("Невозможно подняться выше!")
                cinput("\nНажмите Enter для продолжения...", "secondary")
        elif choice.lower() == 'h':
            # Вернуться в домашнюю директорию
            current_path = os.path.abspath(".")
        elif choice.isdigit():
            # Выбор элемента по номеру
            index = int(choice) - 1
            if 0 <= index < len(items):
                selected_item = items[index]
                item_name = selected_item[1]
                
                # Обработка специальных случаев
                if item_name == "..":
                    # Переход в родительскую директорию
                    parent_path = os.path.dirname(current_path)
                    if os.path.exists(parent_path):
                        current_path = parent_path
                    continue
                
                item_path = os.path.join(current_path, item_name)
                
                if selected_item[2] == "папка" or selected_item[2] == "родительская папка":
                    # Переходим в папку
                    if os.path.isdir(item_path):
                        current_path = item_path
                    else:
                        print("Это не папка!")
                        cinput("\nНажмите Enter для продолжения...", "secondary")
                else:
                    # Возвращаем путь к файлу
                    if os.path.isfile(item_path):
                        return item_path
                    else:
                        print("Это не файл!")
                        cinput("\nНажмите Enter для продолжения...", "secondary")
            else:
                print("Неверный номер!")
                cinput("\nНажмите Enter для продолжения...", "secondary")
        else:
            # Попытка перейти по указанному пути
            if os.path.exists(choice):
                if os.path.isdir(choice):
                    current_path = os.path.abspath(choice)
                else:
                    return os.path.abspath(choice)
            else:
                print("Путь не существует!")
                cinput("\nНажмите Enter для продолжения...", "secondary")

async def create_group_or_channel():
    """Создает новую группу или канал"""
    print_header("Создание группы/канала")
    
    print("1. Создать группу")
    print("2. Создать канал")
    cprint("0. Назад", "secondary")
    
    choice = cinput("\nВыберите тип: ", "info")
    
    if choice == '0':
        return
    
    title = input("Введите название: ")
    if not title:
        print("Название не может быть пустым!")
        cinput("\nНажмите Enter для возврата...", "secondary")
        return
    
    description = input("Введите описание (необязательно): ")
    
    # Переменная для хранения пути к файлу аватарки
    avatar_path = None
    
    # Спросим об аватарке до создания чата
    set_avatar = input("Хотите установить аватарку? (y/n): ").lower()
    if set_avatar == 'y':
        avatar_path = file_explorer()
        if avatar_path and os.path.exists(avatar_path):
            # Проверяем, что файл является изображением
            mime_type, _ = mimetypes.guess_type(avatar_path)
            if not (mime_type and mime_type.startswith('image/')):
                print("Файл должен быть изображением!")
                avatar_path = None
        else:
            avatar_path = None
    
    try:
        if choice == '1':  # Создать группу
            result = await client(functions.channels.CreateChannelRequest(
                title=title,
                about=description,
                megagroup=True  # Это группа, а не канал
            ))
            print("Группа создана успешно!")
            
        elif choice == '2':  # Создать канал
            result = await client(functions.channels.CreateChannelRequest(
                title=title,
                about=description,
                megagroup=False  # Это канал
            ))
            print("Канал создан успешно!")
        
        else:
            print("Неверный выбор!")
            cinput("\nНажмите Enter для возврата...", "secondary")
            return
        
        # Устанавливаем аватарку, если была выбрана
        if avatar_path:
            success = await set_chat_photo(result.chats[0], avatar_path)
            if success:
                print("Аватарка успешно установлена!")
            else:
                cprint("Не удалось установить аватарку!", "error")
        
        # Предложим добавить участников (только для групп)
        if choice == '1':  # Только для групп
            add_members = input("Хотите добавить участников в группу? (y/n): ").lower()
            if add_members == 'y':
                await add_participants_to_group(result.chats[0])
        
        # Добавляем новый чат в папку "Новые чаты"
        new_chat_id = str(result.chats[0].id)
        if new_chat_id not in folders["Новые чаты"]:
            folders["Новые чаты"].append(new_chat_id)
            save_folders(folders)
        
        cinput("\nНажмите Enter для возврата...", "secondary")
        
    except Exception as e:
        cprint(f"Ошибка при создании: {e}", "error")
        input("\nНажмите Enter для возврата...")

async def add_participants_to_group(group):
    """Добавляет участников в группу"""
    print_header("Добавление участников в группу")
    
    while True:
        print("1. Добавить по username")
        print("2. Добавить из контактов")
        cprint("0. Завершить добавление", "success")
        
        choice = input("\nВыберите действие: ")
        
        if choice == '0':
            break
        
        elif choice == '1':  # Добавить по username
            username = input("Введите username (без @): ")
            if username:
                try:
                    # Получаем пользователя по username
                    user = await client.get_entity(username)
                    await client(functions.channels.InviteToChannelRequest(
                        channel=group,
                        users=[user]
                    ))
                    print(f"Пользователь @{username} добавлен в группу!")
                except Exception as e:
                    print(f"Ошибка при добавлении пользователя: {e}")
        
        elif choice == '2':  # Добавить из контактов
            try:
                # Получаем контакты пользователя
                contacts = await client(functions.contacts.GetContactsRequest(hash=0))
                
                if contacts and hasattr(contacts, 'users'):
                    print("Ваши контакты:")
                    for i, user in enumerate(contacts.users):
                        name = f"{user.first_name or ''} {user.last_name or ''}".strip()
                        username = f"@{user.username}" if user.username else "без username"
                        print(f"{i+1}. {name} ({username})")
                    
                    try:
                        contact_num = int(input("Номер контакта для добавления: "))
                        if 1 <= contact_num <= len(contacts.users):
                            user = contacts.users[contact_num - 1]
                            await client(functions.channels.InviteToChannelRequest(
                                channel=group,
                                users=[user]
                            ))
                            print(f"Контакт {user.first_name} добавлен в группу!")
                        else:
                            print("Неверный номер контакта!")
                    except ValueError:
                        print("Введите число!")
                else:
                    print("У вас нет контактов!")
            except Exception as e:
                print(f"Ошибка при получении контактов: {e}")
        
        else:
            print("Неверный выбор!")
    
    print("Добавление участников завершено!")


async def manage_folders():
    """Управление папками"""
    global folders
    
    while True:
        print_header("Управление папками")
        
        print("Существующие папки:")
        for i, folder_name in enumerate(folders.keys()):
            if folder_name in ["Все чаты", "Новые чаты", "Архив"]:
                # Системные папки нельзя удалять
                print(f"{i+1:2d}. {folder_name} [системная]")
            else:
                print(f"{i+1:2d}. {folder_name}")
        
        print("\nДействия:")
        cprint("1. Создать папку", "success")
        cprint("2. Удалить папку", "error")
        cprint("3. Переименовать папку", "warning")
        cprint("4. Переместить чат в папку", "highlight")
        cprint("0. Назад", "secondary")
        
        choice = input("\nВыберите действие: ")
        
        if choice == '0':
            break
        
        elif choice == '1':  # Создать папку
            folder_name = input("Введите название новой папки: ")
            if folder_name and folder_name not in folders:
                folders[folder_name] = []
                save_folders(folders)
                print(f"Папка '{folder_name}' создана!")
            else:
                print("Недопустимое имя папки или папка уже существует!")
            input("\nНажмите Enter для продолжения...")
        
        elif choice == '2':  # Удалить папку
            try:
                folder_num = int(input("Номер папки для удаления: "))
                folder_names = list(folders.keys())
                if 1 <= folder_num <= len(folder_names):
                    folder_name = folder_names[folder_num - 1]
                    
                    if folder_name in ["Все чаты", "Новые чаты", "Архив"]:
                        print("Нельзя удалить системную папку!")
                    else:
                        # Перемещаем чаты в папку "Все чаты" перед удалением
                        for chat_id in folders[folder_name]:
                            if chat_id not in folders["Все чаты"]:
                                folders["Все чаты"].append(chat_id)
                        
                        del folders[folder_name]
                        save_folders(folders)
                        cprint(f"Папка '{folder_name}' удалена!", "success")
                else:
                    print("Неверный номер папки!")
            except ValueError:
                print("Введите число!")
            input("\nНажмите Enter для продолжения...")
        
        elif choice == '3':  # Переименовать папку
            try:
                folder_num = int(input("Номер папки для переименования: "))
                folder_names = list(folders.keys())
                if 1 <= folder_num <= len(folder_names):
                    folder_name = folder_names[folder_num - 1]
                    
                    if folder_name in ["Все чаты", "Новые чаты", "Архив"]:
                        print("Нельзя переименовать системную папку!")
                    else:
                        new_name = input("Новое название папки: ")
                        if new_name and new_name not in folders:
                            folders[new_name] = folders.pop(folder_name)
                            save_folders(folders)
                            print(f"Папка переименована в '{new_name}'!")
                        else:
                            print("Недопустимое имя папки или папка уже существует!")
                else:
                    print("Неверный номер папки!")
            except ValueError:
                print("Введите число!")
            input("\nНажмите Enter для продолжения...")
        
        elif choice == '4':  # Переместить чат в папку
            try:
                # Получаем список всех диалогов
                dialogs = await client.get_dialogs()
                
                print("Доступные чаты:")
                for i, dialog in enumerate(dialogs):
                    print(f"{i+1:2d}. {dialog.name}")
                
                chat_num = int(input("Номер чата для перемещения: "))
                if 1 <= chat_num <= len(dialogs):
                    chat_id = str(dialogs[chat_num - 1].id)
                    
                    print("Доступные папки:")
                    folder_names = list(folders.keys())
                    for i, folder_name in enumerate(folder_names):
                        print(f"{i+1:2d}. {folder_name}")
                    
                    folder_num = int(input("Номер папки для перемещения: "))
                    if 1 <= folder_num <= len(folder_names):
                        target_folder = folder_names[folder_num - 1]
                        
                        # Удаляем чат из всех текущих папок (кроме системных)
                        for folder_name in folders:
                            if folder_name not in ["Все чаты", "Новые чаты", "Архив"] and chat_id in folders[folder_name]:
                                folders[folder_name].remove(chat_id)
                        
                        # Добавляем чат в целевую папку
                        if chat_id not in folders[target_folder]:
                            folders[target_folder].append(chat_id)
                        
                        save_folders(folders)
                        print(f"Чат перемещен в папку '{target_folder}'!")
                    else:
                        print("Неверный номер папки!")
                else:
                    print("Неверный номер чата!")
            except ValueError:
                print("Введите число!")
            input("\nНажмиte Enter для продолжения...")
        
        else:
            print("Неверный выбор!")
            input("\nНажмите Enter для продолжения...")

async def change_folder():
    """Смена текущей папки"""
    global current_folder
    
    print_header("Смена папки")
    
    cprint("Доступные папки:", "info")
    for i, folder_name in enumerate(folders.keys()):
        print(f"{i+1:2d}. {folder_name}")
    
    try:
        choice = int(input("\nВыберите папку: "))
        folder_names = list(folders.keys())
        
        if 1 <= choice <= len(folder_names):
            current_folder = folder_names[choice - 1]
            print(f"Переключено на папку: {current_folder}")
        else:
            print("Неверный выбор!")
    except ValueError:
        print("Введите число!")
    
    cinput("\nНажмите Enter для продолжения...", "secondary")

async def main_improved():
    global API_ID, API_HASH, config, folders, current_folder  
    
    # Исправляем отсутствующие ключи конфигурации
    fix_missing_config_keys()
    
    # Загружаем конфиг
    config = load_config()
    folders = load_folders()
    
    # Улучшенная обработка API данных
    print_header("🔐 Проверка аутентификации")
    
    # Пытаемся загрузить сохраненные credentials
    saved_api_id, saved_api_hash = load_api_credentials()
    
    if saved_api_id and saved_api_hash:
        API_ID = saved_api_id
        API_HASH = saved_api_hash
        cprint("✅ Загружены сохраненные API данные", "success")
    else:
        cprint("⚠️ API данные не найдены или повреждены", "warning")
        
        # Проверяем значения по умолчанию
        if API_ID == 12345678 or API_HASH == 'TYPE_YOU_API_HASH':
            cprint("❌ Обнаружены значения API по умолчанию!", "error")
            print("\nДля работы с Telegram необходимо получить свои API ID и API Hash")
            print("Инструкция:")
            print("1. Перейдите на https://my.telegram.org")
            print("2. Войдите в свой аккаунт")
            print("3. Перейдите в раздел 'API Development Tools'")
            print("4. Создайте новое приложение и получите API ID и API Hash")
            print()
            
            setup_choice = input("Хотите настроить API данные сейчас? (y/n/r - сброс): ").strip().lower()
            
            if setup_choice in ['y', 'yes', 'д', 'да']:
                new_api_id, new_api_hash = setup_api_credentials_interactive()
                if new_api_id and new_api_hash:
                    API_ID = new_api_id
                    API_HASH = new_api_hash
                else:
                    cprint("❌ Настройка API отменена. Программа завершена.", "error")
                    return
            elif setup_choice == 'r':
                reset_api_credentials()
                cprint("✅ Данные сброшены. Перезапустите программу.", "success")
                return
            else:
                cprint("⚠️ Используются значения по умолчанию (возможны ограничения)", "warning")
        else:
            # Пользователь вручную изменил API данные в коде
            cprint("⚠️ Обнаружены API данные в коде", "warning")
            save_choice = input("Хотите сохранить их в безопасном хранилище? (y/n): ").strip().lower()
            if save_choice in ['y', 'yes', 'д', 'да']:
                save_api_credentials(API_ID, API_HASH)
                cprint("✅ API данные сохранены в безопасное хранилище", "success")
    
    # Меню управления API данными
    while True:
        print_header("Управление API данными")
        cprint(f"Текущий API ID: {API_ID}", "info")
        cprint(f"Текущий API Hash: {API_HASH[:8]}...{API_HASH[-8:]}", "info")
        print("\n1. Продолжить работу")
        print("2. Изменить API данные")
        print("3. Удалить сохраненные данные")
        print("4. Проверить подключение")
        cprint("0. Выход", "secondary")
        
        choice = input("\nВыберите действие: ").strip()
        
        if choice == '1':
            break
        elif choice == '2':
            new_api_id, new_api_hash = setup_api_credentials_interactive()
            if new_api_id and new_api_hash:
                API_ID = new_api_id
                API_HASH = new_api_hash
                cprint("✅ API данные обновлены!", "success")
        elif choice == '3':
            reset_api_credentials()
            cprint("✅ Данные удалены. Перезапустите программу.", "success")
            return
        elif choice == '4':
            # Тест подключения с текущими credentials
            cprint("🔍 Тестирование подключения...", "info")
            try:
                test_client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
                await test_client.connect()
                if await test_client.is_user_authorized():
                    me = await test_client.get_me()
                    cprint(f"✅ Успешное подключение как: {me.first_name}", "success")
                else:
                    cprint("❌ Клиент не авторизован", "error")
                await test_client.disconnect()
            except Exception as e:
                cprint(f"❌ Ошибка подключения: {e}", "error")
        elif choice == '0':
            return
        else:
            cprint("❌ Неверный выбор!", "error")
    
    # Проверка обновлений при запуске (только если не в режиме разработки)
    if not os.path.exists("DEV_MODE"):
        cprint("Проверка обновлений...", "primary")
        try:
            await check_for_updates()
        except Exception as e:
            cprint(f"Ошибка при проверке обновлений: {e}", "error")
    
    # Инициализируем клиента с проверкой прокси
    await initialize_client()
    
    while True:
        dialogs = await show_dialogs()
        choice = cinput("\nВыберите диалог: ", "info")
    
        
        if choice == '0':
            break
        
        if choice.lower() == 's':
            await show_settings()
            continue
        
        if choice.lower() == 'i':
            await show_summary()
            continue
        
        if choice.lower() == 'a':
          if current_folder == "Архив":
            current_folder = "Все чаты"
          else:
            current_folder = "Архив"
          continue
        
        if choice.lower() == 'p':
            await search_contacts()
            continue
        
        if choice.lower() == 'c':
          await create_group_or_channel()
          continue

        if choice.lower() == 'm':
          await manage_folders()
          continue

        if choice.lower() == 'f':
          await change_folder()
          continue

        try:
            selected_dialog = dialogs[int(choice)-1]
            current_dialog = selected_dialog
            
            while True:
                await show_messages(selected_dialog)
                action = input("\nВыберите действие: ")
                
                if action == '1':  # Отправить сообщение
                    message = input("Введите сообщение: ")
                    if message:
                        success = await send_text_message(selected_dialog, message)
                        if success:
                            cprint("Сообщение отправлено!", "success")
                
                elif action == '2':  # Ответить на сообщение
                    try:
                        msg_num = int(input("Номер сообщения для ответа: "))
                        if 1 <= msg_num <= len(displayed_messages):
                            # Правильный индекс сообщения
                            reply_to_message = displayed_messages[msg_num - 1]
                            print(f"Ответ на сообщение {msg_num}. Введите сообщение.")
                        else:
                            print("Неверный номер сообщения!")
                    except ValueError:
                        print("Введите число!")
                
                elif action == '3':  # Отправить файл
                    # Используем проводник для выбора файла
                    file_path = file_explorer()
                    
                    if file_path is None:
                        # Пользователь выбрал "Назад"
                        continue
                        
                    if os.path.exists(file_path):
                        # Спросим о сжатии
                        compress_choice = input("Сжимать файл? (y/n, по умолчанию n): ").lower()
                        compress = compress_choice == 'y'
                        
                        success = await send_file(selected_dialog, file_path, compress)
                        if success:
                            cprint("Файл отправлен!", "success")
                    else:
                        print("Файл не найден!")
                
                elif action == '4':  # Поставить реакцию
                    try:
                        msg_num = int(input("Номер сообщения для реакции: "))
                        if 1 <= msg_num <= len(displayed_messages):
                            reaction = input("Реакция (эмодзи): ")
                            # Правильный индекс сообщения
                            message_to_react = displayed_messages[msg_num - 1]
                            success = await set_reaction(selected_dialog, message_to_react.id, reaction)
                            if success:
                                cprint("Реакция добавлена!", "success")
                        else:
                            print("Неверный номер сообщения!")
                    except ValueError:
                        print("Введите число!")
                
                elif action == '5':  # Поиск по сообщениям
                    query = input("Поисковый запрос: ")
                    if query:
                        if await search_messages(selected_dialog, query):
                            # После поиска остаемся в режиме просмотра результатов
                            continue
                
                elif action == '6':  # Скачать файл/медиа
                    try:
                        msg_num = int(input("Номер сообщения с файлом: "))
                        if 1 <= msg_num <= len(displayed_messages):
                            # Правильный индекс сообщения
                            message_with_file = displayed_messages[msg_num - 1]
                            
                            if message_with_file.media or message_with_file.file:
                                success = await download_file(message_with_file, selected_dialog.name)
                                if success:
                                    print("Файл успешно скачан!")
                            else:
                                print("В этом сообщении нет медиа-файла!")
                        else:
                            print("Неверный номер сообщения!")
                    except ValueError:
                        print("Введите число!")
                
                elif action == '7':  # Редактировать сообщение
                    try:
                        msg_num = int(input("Номер сообщения для редактирования: "))
                        if 1 <= msg_num <= len(displayed_messages):
                            message_to_edit = displayed_messages[msg_num - 1]
                            
                            # Проверяем, что это наше сообщение
                            me = await client.get_me()
                            if message_to_edit.sender_id != me.id:
                                print("Вы можете редактировать только свои сообщения!")
                                continue
                                
                            new_text = input("Новый текст сообщения: ")
                            if new_text:
                                success = await edit_message(message_to_edit, new_text)
                                if success:
                                    print("Сообщение отредактировано!")
                            else:
                                print("Текст не может быть пустым!")
                        else:
                            print("Неверный номер сообщения!")
                    except ValueError:
                        print("Введите число!")
                
                elif action == '8':  # Просмотреть медиа
                    try:
                        msg_num = int(input("Номер сообщения с медиа: "))
                        if 1 <= msg_num <= len(displayed_messages):
                            # Правильный индекс сообщения
                            message_with_media = displayed_messages[msg_num - 1]
                            
                            if message_with_media.media:
                                success = await view_media(message_with_media, selected_dialog.name)
                                if not success:
                                    print("Не удалось просмотреть медиа. Попробуйте скачать файл.")
                            else:
                                print("В этом сообщении нет медиа-файла!")
                        else:
                            print("Неверный номер сообщения!")
                    except ValueError:
                        print("Введите число!")
                
                elif action == '9':  # Показать полное сообщение
                    try:
                        msg_num = int(input("Номер сообщения для просмотра: "))
                        if 1 <= msg_num <= len(displayed_messages):
                            # Правильный индекс сообщения
                            message_to_view = displayed_messages[msg_num - 1]
                            await show_full_message(message_to_view, selected_dialog)
                        else:
                            print("Неверный номер сообщения!")
                    except ValueError:
                        print("Введите число!")
                
                elif action == '10' and isinstance(selected_dialog.entity, (types.Channel, types.Chat)):  # Список участников
                    await show_participants(selected_dialog)
                
                elif action == '11':  # Архивировать/разархивировать чат
                    await toggle_chat_archive(selected_dialog)
                    break  # Выходим из текущего диалога после архивации
                
                elif action == '12' and isinstance(selected_dialog.entity, types.User):  # Просмотр профиля
                    result = await show_user_profile(selected_dialog.entity, selected_dialog)
                    # Если выбрано "Написать сообщение", остаемся в диалоге
                    if result == "message":
                        continue
                
                elif action == '13' and isinstance(selected_dialog.entity, (types.Channel, types.Chat)) and getattr(selected_dialog.entity, 'megagroup', False):
                  await add_participants_to_group(selected_dialog.entity)

                elif action == '14' and isinstance(selected_dialog.entity, (types.Channel, types.Chat)):
                  file_path = file_explorer()
                  if file_path and os.path.exists(file_path):
                    # Проверяем, что файл является изображением
                    mime_type, _ = mimetypes.guess_type(file_path)
                    if mime_type and mime_type.startswith('image/'):
                      success = await set_chat_photo(selected_dialog.entity, file_path)
                      if success:
                        print("Аватарка успешно изменена!")
                      else:
                        print("Не удалось изменить аватарку!")
                    else:
                      print("Файл должен быть изображением!")

                elif action == '0':  # Назад
                    reply_to_message = None
                    search_results = []
                    break
                
                elif action.lower() == 'x' and reply_to_message:  # Отменить ответ
                    reply_to_message = None
                    print("Режим ответа отменен")
                
                else:
                    print("Неверный выбор!")
        
        except (IndexError, ValueError):
            print("Неверный выбор диалога!")

    await client.disconnect()


# Обработка новых сообщений
@client.on(events.NewMessage)
async def handler_new_message(event):
    # Если это новый чат, добавляем его в папку "Новые чаты"
    if event.is_private and not event.message.out:  # Входящее личное сообщение
        chat_id = str(event.chat_id)
        
        # Проверяем, есть ли этот чат уже в каких-либо папках (кроме Архива)
        found_in_folder = False
        for folder_name, chat_list in folders.items():
            if folder_name != "Архив" and chat_id in chat_list:
                found_in_folder = True
                break
        
        # Если чат не найден ни в одной папке, добавляем его в "Новые чаты"
        if not found_in_folder and chat_id not in folders["Новые чаты"]:
            folders["Новые чаты"].append(chat_id)
            save_folders(folders)
    
    # Остальная логика обработки новых сообщений
    if current_dialog and event.chat_id == current_dialog.entity.id:
        sender = await event.get_sender()
        sender_name = await get_sender_name(sender) if sender else "Unknown"
        
        # Получаем информацию о сообщении, на которое ответили
        reply_info = ""
        if event.message.reply_to_msg_id:
            replied_text = await get_replied_message_text(event.message, current_dialog)
            reply_info = f" (ответ на: {replied_text})"
        
        # Получаем информацию о медиа
        media_info = ""
        if event.message.media:
            media_type, media_desc = await get_media_info(event.message)
            if media_type:
                emoji = random.choice(MEDIA_EMOJIS.get(media_type, ["📎"]))
                media_info = f" [{emoji} {media_desc}]"
        
        # Проверяем настройки уведомлений
        if config["notifications"]["private_chats"] and isinstance(event.chat, types.User):
            print(f"\nНовое сообщение от {sender_name}{reply_info}{media_info}: {event.message.text or media_desc}")
        elif config["notifications"]["groups"] and (isinstance(event.chat, types.Chat) or (isinstance(event.chat, types.Channel) and getattr(event.chat, 'megagroup', False))):
            print(f"\nНовое сообщение в группе от {sender_name}{reply_info}{media_info}: {event.message.text or media_desc}")
        elif config["notifications"]["channels"] and isinstance(event.chat, types.Channel) and not getattr(event.chat, 'megagroup', False):
            print(f"\nНовое сообщение в канале {sender_name}{reply_info}{media_info}: {event.message.text or media_desc}")

if __name__ == '__main__':
    # Настраиваем обработчики сигналов
    setup_signal_handlers()
    
    # Загружаем конфигурацию
    config = load_config()
    folders = load_folders()
    
    # Запускаем основное приложение
    asyncio.run(main_improved())
