import asyncio
import os
import mimetypes
import json
import random
import re
from datetime import datetime
from telethon import TelegramClient, events, functions, types
from telethon.tl import functions
from telethon.tl.types import DocumentAttributeFilename, DocumentAttributeVideo, DocumentAttributeAudio

# Configuration
API_ID = 12345678  # Replace with your API ID
API_HASH = 'API_HASH'  # Replace with your API Hash
SESSION_FILE = 'linuxgram.session'
DOWNLOADS_DIR = "downloads"
CONFIG_FILE = "config.json"

client = TelegramClient(SESSION_FILE, API_ID, API_HASH)

# Create downloads directory
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# Load configuration
def load_config():
    default_config = {
        "privacy": {
            "last_seen": "everybody",
            "read_receipts": True
        },
        "notifications": {
            "private_chats": True,
            "groups": True,
            "channels": False
        },
        "data": {
            "auto_download": {
                "photos": True,
                "videos": False,
                "files": False,
                "voice_messages": True
            }
        },
        "language": "English"
    }
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            loaded_config = json.load(f)
            return update_config(loaded_config, default_config)
    except FileNotFoundError:
        return default_config

def update_config(loaded_config, default_config):
    """Recursively update config with missing keys"""
    for key, value in default_config.items():
        if key not in loaded_config:
            loaded_config[key] = value
        elif isinstance(value, dict) and isinstance(loaded_config[key], dict):
            loaded_config[key] = update_config(loaded_config[key], value)
    return loaded_config

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

config = load_config()

# State variables
current_dialog = None
current_messages = []
reply_to_message = None
search_results = []
displayed_messages = []
cached_chat_info = {}

# Media type mapping
MEDIA_TYPES = {
    'sticker': 'Sticker',
    'photo': 'Photo',
    'video': 'Video',
    'gif': 'GIF',
    'voice': 'Voice message',
    'audio': 'Audio',
    'document': 'Document',
    'location': 'Location',
    'contact': 'Contact',
    'poll': 'Poll'
}

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title):
    clear_console()
    print("=" * 80)
    print(f"LinuxGram Flash - {title}")
    print("=" * 80)

async def get_chat_info(dialog):
    """Get chat/channel information"""
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
        print(f"Error getting chat info: {e}")
        return None

async def get_user_status(user):
    """Get user status"""
    if not user or not hasattr(user, 'status'):
        return "unknown"
    
    if isinstance(user.status, types.UserStatusOnline):
        return "online"
    elif isinstance(user.status, types.UserStatusOffline):
        return f"last seen {user.status.was_online.strftime('%d.%m.%Y %H:%M')}"
    elif isinstance(user.status, types.UserStatusRecently):
        return "recently"
    elif isinstance(user.status, types.UserStatusLastWeek):
        return "last week"
    elif isinstance(user.status, types.UserStatusLastMonth):
        return "last month"
    else:
        return "unknown"

async def show_dialogs():
    dialogs = await client.get_dialogs()
    print_header("Your Dialogs")
    
    # Collect status tasks for users
    status_tasks = []
    for dialog in dialogs:
        if isinstance(dialog.entity, types.User):
            status_tasks.append(get_user_status(dialog.entity))
        else:
            status_tasks.append(None)
    
    # Execute all tasks in parallel
    status_results = []
    for task in status_tasks:
        if task is not None:
            try:
                status_results.append(await task)
            except Exception as e:
                status_results.append(f"error: {e}")
        else:
            status_results.append(None)
    
    # Display dialogs
    for i, dialog in enumerate(dialogs):
        # Determine dialog type
        dialog_type = ""
        if isinstance(dialog.entity, types.Channel):
            if getattr(dialog.entity, 'megagroup', False):
                dialog_type = " [Group]"
            else:
                dialog_type = " [Channel]"
        elif isinstance(dialog.entity, types.Chat):
            dialog_type = " [Group]"
        else:
            dialog_type = " [Private]"
        
        # For private chats, show user status
        status_info = ""
        if isinstance(dialog.entity, types.User):
            status = status_results[i]
            status_info = f" - {status}"
        
        # For groups and channels, show participant count
        members_info = ""
        if isinstance(dialog.entity, (types.Channel, types.Chat)):
            chat_info = await get_chat_info(dialog)
            if chat_info:
                participants_count = getattr(chat_info.full_chat, 'participants_count', 0)
                members_info = f" ({participants_count} members)"
        
        unread = f" ({dialog.unread_count} unread)" if dialog.unread_count > 0 else ""
        print(f"{i+1:2d}. {dialog.name}{dialog_type}{members_info}{unread}{status_info}")
    
    print("\n0. Exit")
    print("s. Settings")
    print("p. Search contacts")
    return dialogs

async def get_sender_name(sender):
    """Get sender name considering type (User, Channel, Chat)"""
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
    """Get text of the replied message"""
    if not message.reply_to_msg_id:
        return None
    
    try:
        # Try to find the message being replied to
        replied_msg = await client.get_messages(dialog.entity, ids=message.reply_to_msg_id)
        if replied_msg and replied_msg.text:
            # Trim long text
            text = replied_msg.text
            return text[:50] + "..." if len(text) > 50 else text
        elif replied_msg and replied_msg.media:
            return "[media message]"
        else:
            return "[message]"
    except Exception:
        return "[message]"

async def get_media_info(msg):
    """Get media file information"""
    if not msg.media:
        return None, None
    
    # For stickers
    if isinstance(msg.media, types.MessageMediaDocument):
        if msg.document:
            for attr in msg.document.attributes:
                if isinstance(attr, types.DocumentAttributeSticker):
                    return "sticker", "Sticker"
                elif isinstance(attr, types.DocumentAttributeVideo):
                    if hasattr(attr, 'round_message') and attr.round_message:
                        return "video", "Round video"
                    else:
                        duration = f" ({attr.duration}s)" if hasattr(attr, 'duration') else ""
                        return "video", f"Video{duration}"
                elif isinstance(attr, types.DocumentAttributeAudio):
                    if hasattr(attr, 'voice') and attr.voice:
                        return "voice", "Voice message"
                    else:
                        duration = f" ({attr.duration}s)" if hasattr(attr, 'duration') else ""
                        title = f" {attr.title}" if hasattr(attr, 'title') and attr.title else ""
                        return "audio", f"Audio{title}{duration}"
                elif isinstance(attr, types.DocumentAttributeAnimated):
                    return "gif", "GIF"
    
    # For photos
    if isinstance(msg.media, types.MessageMediaPhoto):
        return "photo", "Photo"
    
    # For geolocation
    if isinstance(msg.media, types.MessageMediaGeo):
        return "location", "Location"
    
    # For contacts
    if isinstance(msg.media, types.MessageMediaContact):
        return "contact", "Contact"
    
    # For polls
    if isinstance(msg.media, types.MessageMediaPoll):
        return "poll", f"Poll: {msg.media.poll.question}"
    
    # For web pages
    if isinstance(msg.media, types.MessageMediaWebPage):
        if isinstance(msg.media.webpage, types.WebPage):
            return "webpage", f"Web page: {msg.media.webpage.title or msg.media.webpage.url}"
    
    # General case for documents
    if msg.file:
        file_name = msg.file.name or "file"
        return "document", f"Document: {file_name}"
    
    return None, "Media file"

async def show_messages(dialog, messages=None, title=None):
    global current_messages, reply_to_message, displayed_messages
    
    if messages is None:
        messages = await client.get_messages(dialog.entity, limit=20)
        current_messages = messages
    
    displayed_messages = list(reversed(messages))  # Save displayed messages
    
    # For private chats add user status to title
    if isinstance(dialog.entity, types.User) and title is None:
        status = await get_user_status(dialog.entity)
        title = f"Chat with {dialog.name} ({status})"
    elif title is None:
        title = f"Chat with {dialog.name}"
    
    print_header(title)
    
    # For groups and channels show participant info
    if isinstance(dialog.entity, (types.Channel, types.Chat)):
        chat_info = await get_chat_info(dialog)
        if chat_info:
            participants_count = getattr(chat_info.full_chat, 'participants_count', 0)
            online_count = getattr(chat_info.full_chat, 'online_count', 0)
            print(f"Members: {participants_count}, online: {online_count}")
            print("-" * 80)
    
    # Display messages
    for i, msg in enumerate(displayed_messages):
        # Determine sender
        sender = await msg.get_sender()
        sender_name = await get_sender_name(sender) if sender else "Unknown"
        
        # Format date
        date = msg.date.strftime("%d.%m %H:%M")
        
        # Determine message type and media info
        msg_type = "Text"
        media_info = ""
        file_info = ""
        
        if msg.media:
            media_type, media_desc = await get_media_info(msg)
            if media_type:
                msg_type = media_desc
        
        # Show if there's a reply to another message
        reply_info = ""
        if msg.reply_to_msg_id:
            # Get text of the message being replied to
            replied_text = await get_replied_message_text(msg, dialog)
            reply_info = f" (reply to: {replied_text})"
        
        # Show if this message has replies
        replied_to_info = ""
        # Check if there are replies to this message
        for other_msg in messages:
            if other_msg.reply_to_msg_id == msg.id:
                replied_to_info = " (has replies)"
                break
        
        # Show file info if available
        if msg.file:
            file_size = msg.file.size
            if file_size:
                file_size_kb = file_size / 1024
                if file_size_kb < 1024:
                    file_info = f" [{file_size_kb:.1f} KB]"
                else:
                    file_info = f" [{file_size_kb/1024:.1f} MB]"
        
        # Determine if it's our message
        me = await client.get_me()
        is_my_message = msg.sender_id == me.id
        
        # Show read status for our messages
        read_status = ""
        if is_my_message and hasattr(msg, 'read') and msg.read:
            read_status = " (read)"
        elif is_my_message:
            read_status = " (sent)"
        
        message_indicator = "> " if is_my_message else ""
        
        print(f"{i+1:2d}. {message_indicator}[{date}] {sender_name}: {msg_type}{file_info}{reply_info}{read_status}")
        
        # Show message text or media caption
        if msg.text:
            print(f"      {msg.text[:100]}{'...' if len(msg.text) > 100 else ''}")
        elif hasattr(msg, 'message') and msg.message:
            print(f"      {msg.message[:100]}{'...' if len(msg.message) > 100 else ''}")
        
        print()
    
    # Show menu
    print("\nActions:")
    print("1. Send message")
    print("2. Reply to message")
    print("3. Send file")
    print("4. Search messages")
    print("5. Download file/media")
    print("6. Edit message")
    print("0. Back")
    
    if reply_to_message:
        # Find message number in displayed list
        reply_index = None
        for i, msg in enumerate(displayed_messages):
            if msg.id == reply_to_message.id:
                reply_index = i + 1
                break
        if reply_index:
            print(f"Reply to message {reply_index} (x to cancel)")

async def search_messages(dialog, query):
    global search_results
    print_header(f"Search in chat with {dialog.name}")
    
    # Perform search
    search_results = await client.get_messages(dialog.entity, search=query, limit=20)
    
    if not search_results:
        print("No messages found.")
        input("\nPress Enter to return...")
        return False
    
    await show_messages(dialog, search_results, f"Search results: '{query}'")
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
        print(f"Error sending message: {e}")
        return False

async def send_file(dialog, file_path, compress=False):
    global reply_to_message
    
    try:
        # Determine file type by extension for proper attributes
        ext = os.path.splitext(file_path)[1].lower()
        attributes = []
        
        # For video files add proper attributes
        if ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
            # Get video info (dimensions and duration)
            attributes = [DocumentAttributeVideo(
                duration=0,  # Duration in seconds
                w=1280,      # Width
                h=720,       # Height
                round_message=False,
                supports_streaming=True
            )]
        # For audio files
        elif ext in ['.mp3', '.wav', '.ogg', '.flac']:
            attributes = [DocumentAttributeAudio(
                duration=0,  # Duration in seconds
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
                force_document=not compress  # force_document=True for sending without compression
            )
            reply_to_message = None
        else:
            await client.send_file(
                dialog.entity, 
                file_path, 
                caption="", 
                attributes=attributes,
                force_document=not compress  # force_document=True for sending without compression
            )
        return True
    except Exception as e:
        print(f"Error sending file: {e}")
        return False

async def edit_message(message, new_text):
    try:
        await client.edit_message(message.chat_id, message.id, new_text)
        return True
    except Exception as e:
        print(f"Error editing message: {e}")
        return False

async def download_file(message, dialog_name):
    """Download file from message"""
    try:
        # Create folder for dialog if it doesn't exist
        dialog_dir = os.path.join(DOWNLOADS_DIR, dialog_name.replace("/", "_"))
        os.makedirs(dialog_dir, exist_ok=True)
        
        # Determine file name
        if message.file and message.file.name:
            file_name = message.file.name
        else:
            # Generate file name based on type and date
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
        
        # Download file
        print(f"Downloading file: {file_name}")
        download_path = await message.download_media(file=file_path)
        
        if download_path:
            print(f"File saved: {download_path}")
            return True
        else:
            print("Error downloading file")
            return False
            
    except Exception as e:
        print(f"Error downloading file: {e}")
        return False

async def search_contacts():
    """Search contacts by username, phone number or name"""
    print_header("Search Contacts")
    print("1. Search by username")
    print("2. Search by phone number")
    print("3. Search by name")
    print("0. Back")
    
    choice = input("\nSelect search type: ")
    
    if choice == '0':
        return
    
    query = input("Enter search query: ")
    if not query:
        print("Query cannot be empty!")
        input("\nPress Enter to return...")
        return
    
    results = []
    
    try:
        if choice == '1':  # Search by username
            # Remove @ if user entered it
            if query.startswith('@'):
                query = query[1:]
            
            try:
                result = await client(functions.contacts.ResolveUsernameRequest(username=query))
                if result.users:
                    results = result.users
                elif result.chats:
                    results = result.chats
                else:
                    print("User or channel not found!")
                    input("\nPress Enter to return...")
                    return
            except Exception as e:
                print(f"Error searching by username: {e}")
                input("\nPress Enter to return...")
                return
        
        elif choice == '2':  # Search by phone number
            # Clean number from extra characters
            phone = re.sub(r'[^0-9+]', '', query)
            
            try:
                # Import contact for search
                result = await client(functions.contacts.ImportContactsRequest(
                    contacts=[types.InputPhoneContact(
                        client_id=random.randrange(2**31),
                        phone=phone,
                        first_name="Search",
                        last_name=""
                    )]
                ))
                
                if result.users:
                    results = result.users
                    
                    # Delete imported contact
                    await client(functions.contacts.DeleteContactsRequest(id=result.users))
                else:
                    print("User not found!")
                    input("\nPress Enter to return...")
                    return
            except Exception as e:
                print(f"Error searching by phone number: {e}")
                input("\nPress Enter to return...")
                return
        
        elif choice == '3':  # Search by name
            # Search in contacts
            try:
                contacts = await client(functions.contacts.GetContactsRequest(hash=0))
                if contacts and hasattr(contacts, 'users'):
                    for user in contacts.users:
                        name = f"{user.first_name or ''} {user.last_name or ''}".strip().lower()
                        if query.lower() in name:
                            results.append(user)
                else:
                    print("Contacts not found!")
                    input("\nPress Enter to return...")
                    return
            except Exception as e:
                print(f"Error getting contacts: {e}")
                input("\nPress Enter to return...")
                return
            
            if not results:
                print("Contacts not found!")
                input("\nPress Enter to return...")
                return
        
        else:
            print("Invalid choice!")
            input("\nPress Enter to return...")
            return
        
        # Show search results
        print_header("Search Results")
        
        if not results:
            print("Nothing found!")
            input("\nPress Enter to return...")
            return
        
        for i, entity in enumerate(results):
            if isinstance(entity, types.User):
                user_type = "Bot" if entity.bot else "User"
                status = await get_user_status(entity)
                print(f"{i+1:2d}. {user_type}: {await get_sender_name(entity)} - {status}")
            elif isinstance(entity, types.Channel):
                if getattr(entity, 'megagroup', False):
                    print(f"{i+1:2d}. Group: {entity.title}")
                else:
                    print(f"{i+1:2d}. Channel: {entity.title}")
            elif isinstance(entity, types.Chat):
                print(f"{i+1:2d}. Group: {entity.title}")
        
        print("\nEnter number to view profile or 0 to return:")
        choice = input("Your choice: ")
        
        try:
            choice_idx = int(choice)
            if choice_idx == 0:
                return
            elif 1 <= choice_idx <= len(results):
                entity = results[choice_idx - 1]
                if isinstance(entity, types.User):
                    # For users, create a temporary dialog
                    temp_dialog = types.Dialog(
                        id=entity.id,
                        name=await get_sender_name(entity),
                        entity=entity,
                        unread_count=0,
                        unread_mentions_count=0,
                        draft=None
                    )
                    await show_messages(temp_dialog, title=f"Info about {await get_sender_name(entity)}")
                elif isinstance(entity, (types.Channel, types.Chat)):
                    # For channels and groups create a temporary dialog
                    temp_dialog = types.Dialog(
                        id=entity.id,
                        name=entity.title,
                        entity=entity,
                        unread_count=0,
                        unread_mentions_count=0,
                        draft=None
                    )
                    await show_messages(temp_dialog, title=f"Info about {entity.title}")
            else:
                print("Invalid number!")
                input("\nPress Enter to return...")
        except ValueError:
            print("Enter a number!")
            input("\nPress Enter to return...")
            
    except Exception as e:
        print(f"Search error: {e}")
        input("\nPress Enter to return...")

async def show_privacy_settings():
    global config
    
    privacy_options = {
        "last_seen": {
            "name": "Last seen time",
            "options": ["everybody", "contacts", "nobody"]
        },
        "read_receipts": {
            "name": "Read receipts",
            "type": "bool"
        }
    }
    
    while True:
        print_header("Privacy Settings")
        
        for i, (key, setting) in enumerate(privacy_options.items()):
            if "options" in setting:
                current_value = config["privacy"][key]
                print(f"{i+1}. {setting['name']}: {current_value}")
            else:
                current_value = "on" if config["privacy"][key] else "off"
                print(f"{i+1}. {setting['name']}: {current_value}")
        
        print("\n0. Back")
        
        choice = input("\nSelect setting to change: ")
        
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
                    
                    option_choice = input("Select option: ")
                    
                    try:
                        option_idx = int(option_choice) - 1
                        if 0 <= option_idx < len(setting["options"]):
                            config["privacy"][key] = setting["options"][option_idx]
                            save_config(config)
                            print("Setting saved!")
                        else:
                            print("Invalid choice!")
                    except ValueError:
                        print("Enter a number!")
                else:
                    config["privacy"][key] = not config["privacy"][key]
                    save_config(config)
                    print(f"{setting['name']} {'enabled' if config['privacy'][key] else 'disabled'}!")
            else:
                print("Invalid choice!")
        except ValueError:
            print("Enter a number!")

async def show_notification_settings():
    global config
    
    notification_options = {
        "private_chats": {
            "name": "Private chats",
            "type": "bool"
        },
        "groups": {
            "name": "Groups",
            "type": "bool"
        },
        "channels": {
            "name": "Channels",
            "type": "bool"
        }
    }
    
    while True:
        print_header("Notification Settings")
        
        for i, (key, setting) in enumerate(notification_options.items()):
            current_value = "on" if config["notifications"][key] else "off"
            print(f"{i+1}. {setting['name']}: {current_value}")
        
        print("\n0. Back")
        
        choice = input("\nSelect setting to change: ")
        
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
                    print(f"{setting['name']} {'enabled' if config['notifications'][key] else 'disabled'}!")
            else:
                print("Invalid choice!")
        except ValueError:
            print("Enter a number!")

async def show_data_settings():
    global config
    
    data_options = {
        "photos": {
            "name": "Photos",
            "type": "bool"
        },
        "videos": {
            "name": "Videos",
            "type": "bool"
        },
        "files": {
            "name": "Files",
            "type": "bool"
        },
        "voice_messages": {
            "name": "Voice messages",
            "type": "bool"
        }
    }
    
    while True:
        print_header("Data and Storage Settings")
        
        print("Auto-download:")
        for i, (key, setting) in enumerate(data_options.items()):
            current_value = config["data"]["auto_download"].get(key, True)
            status = "on" if current_value else "off"
            print(f"{i+1}. {setting['name']}: {status}")
        
        print("\n0. Back")
        
        choice = input("\nSelect setting to change: ")
        
        if choice == '0':
            break
        
        try:
            choice_idx = int(choice)
            if 1 <= choice_idx <= len(data_options):
                key = list(data_options.keys())[choice_idx - 1]
                setting = data_options[key]
                
                current_val = config["data"]["auto_download"].get(key, True)
                config["data"]["auto_download"][key] = not current_val
                save_config(config)
                new_status = "enabled" if config["data"]["auto_download"][key] else "disabled"
                print(f"Auto-download {setting['name']} {new_status}!")
            else:
                print("Invalid choice!")
        except ValueError:
            print("Enter a number!")

async def show_settings():
    while True:
        print_header("Settings")
        print("1. Privacy and Security")
        print("2. Notifications")
        print("3. Data and Storage")
        print("0. Back")
        
        choice = input("\nSelect settings section: ")
        
        if choice == '1':
            await show_privacy_settings()
        elif choice == '2':
            await show_notification_settings()
        elif choice == '3':
            await show_data_settings()
        elif choice == '0':
            break
        else:
            print("Invalid choice!")

def file_explorer(start_path="."):
    """Simple file explorer"""
    current_path = os.path.abspath(start_path)
    
    while True:
        print_header(f"File Explorer: {current_path}")
        
        # Get list of files and folders
        items = []
        try:
            # Add link to parent directory (except root)
            if current_path != os.path.abspath(".") and os.path.dirname(current_path) != current_path:
                items.append(("DIR", "..", "parent folder"))
            
            for item in os.listdir(current_path):
                item_path = os.path.join(current_path, item)
                if os.path.isdir(item_path):
                    items.append(("DIR", item, "folder"))
                else:
                    # Determine file type by extension
                    ext = os.path.splitext(item)[1].lower()
                    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                        icon = "IMG"
                    elif ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
                        icon = "VID"
                    elif ext in ['.mp3', '.wav', '.ogg', '.flac']:
                        icon = "AUD"
                    elif ext in ['.txt', '.doc', '.docx', '.pdf', '.rtf']:
                        icon = "DOC"
                    elif ext in ['.zip', '.rar', '.7z', '.tar', '.gz']:
                        icon = "ARC"
                    else:
                        icon = "FILE"
                    try:
                        size = os.path.getsize(item_path)
                        size_str = f"{size/1024:.1f} KB" if size < 1024*1024 else f"{size/(1024*1024):.1f} MB"
                    except OSError:
                        size_str = "N/A"
                    items.append((icon, item, size_str))
        except PermissionError:
            print("No access to this folder!")
            input("\nPress Enter to return...")
            return None
        
        if not items:
            print("Folder is empty!")
            input("\nPress Enter to return...")
            return None
        
        # Display list
        print("Contents:")
        for i, (icon, name, desc) in enumerate(items):
            if desc == "parent folder":
                print(f"{i+1:2d}. {icon} {name} ({desc})")
            elif desc == "folder":
                print(f"{i+1:2d}. {icon} {name}/ ({desc})")
            else:
                print(f"{i+1:2d}. {icon} {name} ({desc})")
        
        print("\nActions:")
        print("0. Back to chat")
        if current_path != os.path.abspath("."):
            print("h. Home (script directory)")
        print("u. Up one level")
        print("Enter item number to select or path to navigate")
        
        choice = input("\nYour choice: ").strip()
        
        if choice == '0':
            return None
        elif choice.lower() == 'u':
            # Go up one level
            parent_path = os.path.dirname(current_path)
            if os.path.exists(parent_path) and parent_path != current_path:
                current_path = parent_path
            else:
                print("Cannot go up!")
                input("\nPress Enter to continue...")
        elif choice.lower() == 'h':
            # Return to home directory
            current_path = os.path.abspath(".")
        elif choice.isdigit():
            # Select item by number
            index = int(choice) - 1
            if 0 <= index < len(items):
                selected_item = items[index]
                item_name = selected_item[1]
                
                # Handle special cases
                if item_name == "..":
                    # Go to parent directory
                    parent_path = os.path.dirname(current_path)
                    if os.path.exists(parent_path):
                        current_path = parent_path
                    continue
                
                item_path = os.path.join(current_path, item_name)
                
                if selected_item[2] == "folder" or selected_item[2] == "parent folder":
                    # Go to folder
                    if os.path.isdir(item_path):
                        current_path = item_path
                    else:
                        print("Not a folder!")
                        input("\nPress Enter to continue...")
                else:
                    # Return file path
                    if os.path.isfile(item_path):
                        return item_path
                    else:
                        print("Not a file!")
                        input("\nPress Enter to continue...")
            else:
                print("Invalid number!")
                input("\nPress Enter to continue...")
        else:
            # Try to navigate to specified path
            if os.path.exists(choice):
                if os.path.isdir(choice):
                    current_path = os.path.abspath(choice)
                else:
                    return os.path.abspath(choice)
            else:
                print("Path does not exist!")
                input("\nPress Enter to continue...")

async def main():
    global current_dialog, reply_to_message
    
    await client.start()
    
    while True:
        dialogs = await show_dialogs()
        choice = input("\nSelect dialog: ")
        
        if choice == '0':
            break
        
        if choice.lower() == 's':
            await show_settings()
            continue
        
        if choice.lower() == 'p':
            await search_contacts()
            continue

        try:
            selected_dialog = dialogs[int(choice)-1]
            current_dialog = selected_dialog
            
            while True:
                await show_messages(selected_dialog)
                action = input("\nSelect action: ")
                
                if action == '1':  # Send message
                    message = input("Enter message: ")
                    if message:
                        success = await send_text_message(selected_dialog, message)
                        if success:
                            print("Message sent!")
                
                elif action == '2':  # Reply to message
                    try:
                        msg_num = int(input("Message number to reply to: "))
                        if 1 <= msg_num <= len(displayed_messages):
                            # Correct message index
                            reply_to_message = displayed_messages[msg_num - 1]
                            print(f"Reply to message {msg_num}. Enter message.")
                        else:
                            print("Invalid message number!")
                    except ValueError:
                        print("Enter a number!")
                
                elif action == '3':  # Send file
                    # Use file explorer to select file
                    file_path = file_explorer()
                    
                    if file_path is None:
                        # User selected "Back"
                        continue
                        
                    if os.path.exists(file_path):
                        # Ask about compression
                        compress_choice = input("Compress file? (y/n, default n): ").lower()
                        compress = compress_choice == 'y'
                        
                        success = await send_file(selected_dialog, file_path, compress)
                        if success:
                            print("File sent!")
                    else:
                        print("File not found!")
                
                elif action == '4':  # Search messages
                    query = input("Search query: ")
                    if query:
                        if await search_messages(selected_dialog, query):
                            # Stay in search results view mode
                            continue
                
                elif action == '5':  # Download file/media
                    try:
                        msg_num = int(input("Message number with file: "))
                        if 1 <= msg_num <= len(displayed_messages):
                            # Correct message index
                            message_with_file = displayed_messages[msg_num - 1]
                            
                            if message_with_file.media or message_with_file.file:
                                success = await download_file(message_with_file, selected_dialog.name)
                                if success:
                                    print("File downloaded successfully!")
                            else:
                                print("This message has no media file!")
                        else:
                            print("Invalid message number!")
                    except ValueError:
                        print("Enter a number!")
                
                elif action == '6':  # Edit message
                    try:
                        msg_num = int(input("Message number to edit: "))
                        if 1 <= msg_num <= len(displayed_messages):
                            message_to_edit = displayed_messages[msg_num - 1]
                            
                            # Check if it's our message
                            me = await client.get_me()
                            if message_to_edit.sender_id != me.id:
                                print("You can only edit your own messages!")
                                continue
                                
                            new_text = input("New message text: ")
                            if new_text:
                                success = await edit_message(message_to_edit, new_text)
                                if success:
                                    print("Message edited!")
                            else:
                                print("Text cannot be empty!")
                        else:
                            print("Invalid message number!")
                    except ValueError:
                        print("Enter a number!")
                
                elif action == '0':  # Back
                    reply_to_message = None
                    search_results = []
                    break
                
                elif action.lower() == 'x' and reply_to_message:  # Cancel reply
                    reply_to_message = None
                    print("Reply mode canceled")
                
                else:
                    print("Invalid choice!")
        
        except (IndexError, ValueError):
            print("Invalid dialog selection!")

    await client.disconnect()

# Handle new messages
@client.on(events.NewMessage)
async def handler_new_message(event):
    # If it's a new chat, add it to the "New Chats" folder
    if event.is_private and not event.message.out:  # Incoming private message
        chat_id = str(event.chat_id)
        
        # Check notification settings
        if config["notifications"]["private_chats"] and isinstance(event.chat, types.User):
            sender = await event.get_sender()
            sender_name = await get_sender_name(sender) if sender else "Unknown"
            
            # Get media info
            media_info = ""
            if event.message.media:
                media_type, media_desc = await get_media_info(event.message)
                if media_type:
                    media_info = f" [{media_desc}]"
            
            print(f"\nNew message from {sender_name}{media_info}: {event.message.text or media_desc}")
        elif config["notifications"]["groups"] and (isinstance(event.chat, types.Chat) or (isinstance(event.chat, types.Channel) and getattr(event.chat, 'megagroup', False))):
            sender = await event.get_sender()
            sender_name = await get_sender_name(sender) if sender else "Unknown"
            
            # Get media info
            media_info = ""
            if event.message.media:
                media_type, media_desc = await get_media_info(event.message)
                if media_type:
                    media_info = f" [{media_desc}]"
            
            print(f"\nNew message in group from {sender_name}{media_info}: {event.message.text or media_desc}")
        elif config["notifications"]["channels"] and isinstance(event.chat, types.Channel) and not getattr(event.chat, 'megagroup', False):
            sender = await event.get_sender()
            sender_name = await get_sender_name(sender) if sender else "Unknown"
            
            # Get media info
            media_info = ""
            if event.message.media:
                media_type, media_desc = await get_media_info(event.message)
                if media_type:
                    media_info = f" [{media_desc}]"
            
            print(f"\nNew message in channel {sender_name}{media_info}: {event.message.text or media_desc}")

if __name__ == '__main__':
    asyncio.run(main())
