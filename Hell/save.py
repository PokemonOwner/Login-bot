import asyncio
import os
import time
import logging
from pyrogram import Client, filters
from pyrogram.errors import (FloodWait, UserIsBlocked, InputUserDeactivated,
                              UserAlreadyParticipant, InviteHashExpired, 
                              UsernameNotOccupied)
from pyrogram.types import (InlineKeyboardMarkup, InlineKeyboardButton, Message)
from config import API_ID, API_HASH
from database.db import database
from Hell.strings import strings, HELP_TXT

# Set up logging
logging.basicConfig(level=logging.INFO)

# Rate limiting storage
last_command_time = {}

# Helper function to get data from dictionary
def get(obj, key, default=None):
    return obj.get(key, default)

# Status updater for download progress
async def downstatus(client: Client, statusfile, message):
    while not os.path.exists(statusfile):
        await asyncio.sleep(3)

    while os.path.exists(statusfile):
        with open(statusfile, "r") as downread:
            txt = downread.read()
        try:
            await client.edit_message_text(message.chat.id, message.id, f"Downloaded: {txt}")
            await asyncio.sleep(10)
        except Exception as e:
            logging.error(f"Error updating download status: {e}")
            await asyncio.sleep(5)

# Status updater for upload progress
async def upstatus(client: Client, statusfile, message):
    while not os.path.exists(statusfile):
        await asyncio.sleep(3)

    while os.path.exists(statusfile):
        with open(statusfile, "r") as upread:
            txt = upread.read()
        try:
            await client.edit_message_text(message.chat.id, message.id, f"Uploaded: {txt}")
            await asyncio.sleep(10)
        except Exception as e:
            logging.error(f"Error updating upload status: {e}")
            await asyncio.sleep(5)

# Progress writer
def progress(current, total, message, type):
    with open(f'{message.id}{type}status.txt', "w") as fileup:
        fileup.write(f"{current * 100 / total:.1f}%")

# Decorator for command debouncing
def debounce_command(func):
    async def wrapper(client, message):
        user_id = message.from_user.id
        current_time = time.time()

        if user_id in last_command_time and (current_time - last_command_time[user_id]) < 1:
            return  # Ignore command if sent too quickly

        last_command_time[user_id] = current_time
        return await func(client, message)
    return wrapper

# Start command
@Client.on_message(filters.command(["start"]) & filters.private)
@debounce_command
async def send_start(client: Client, message: Message):
    logging.info(f"Received /start command from {message.from_user.mention}")
    buttons = [
        [InlineKeyboardButton("❣️ Developer", url="https://t.me/king_of_hell_botz")],
        [InlineKeyboardButton('🔍 Support Group', url='https://t.me/king_of_hell_botz'),
         InlineKeyboardButton('🤖 Update Channel', url='https://t.me/king_of_hell_botz')]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await client.send_message(
        message.chat.id, 
        f"<b>👋 Hi {message.from_user.mention}, I am Save Restricted Content Bot, "
        f"I can send you restricted content by its post link.\n\n"
        f"For downloading restricted content, /login first.\n\n"
        f"Know how to use the bot by - /help</b>", 
        reply_markup=reply_markup, 
        reply_to_message_id=message.id
    )

# Help command
@Client.on_message(filters.command(["help"]) & filters.private)
@debounce_command
async def send_help(client: Client, message: Message):
    logging.info(f"Received /help command from {message.from_user.mention}")
    await client.send_message(message.chat.id, f"{HELP_TXT}")

# Save command
@Client.on_message(filters.text & filters.private)
@debounce_command
async def save(client: Client, message: Message):
    if "https://t.me/" in message.text:
        datas = message.text.split("/")
        temp = datas[-1].replace("?single", "").split("-")
        fromID = int(temp[0].strip())
        toID = int(temp[1].strip()) if len(temp) > 1 else fromID

        for msgid in range(fromID, toID + 1):
            user_data = database.find_one({'chat_id': message.chat.id})
            if not get(user_data, 'logged_in', False) or user_data['session'] is None:
                await client.send_message(message.chat.id, strings['need_login'])
                return

            acc = Client("saverestricted", session_string=user_data['session'], api_hash=API_HASH, api_id=API_ID)
            await acc.connect()

            if "https://t.me/c/" in message.text:
                chatid = int("-100" + datas[4])
                await handle_private(client, acc, message, chatid, msgid)
            elif "https://t.me/b/" in message.text:
                username = datas[4]
                await handle_private(client, acc, message, username, msgid)
            else:
                username = datas[3]
                await handle_public(client, acc, message, username, msgid)

            await asyncio.sleep(3)  # wait time between messages

# Handle private messages
async def handle_private(client: Client, acc, message: Message, chatid: int, msgid: int):
    msg: Message = await acc.get_messages(chatid, msgid)
    msg_type = get_message_type(msg)
    chat = message.chat.id

    if msg_type == "Text":
        try:
            await client.send_message(chat, msg.text, entities=msg.entities, reply_to_message_id=message.id)
        except Exception as e:
            logging.error(f"Error sending text: {e}")
            await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)
            return

    smsg = await client.send_message(message.chat.id, 'Downloading...', reply_to_message_id=message.id)
    dosta = asyncio.create_task(downstatus(client, f'{message.id}downstatus.txt', smsg))
    
    try:
        file = await acc.download_media(msg, progress=progress, progress_args=[message, "down"])
        os.remove(f'{message.id}downstatus.txt')
    except Exception as e:
        logging.error(f"Error downloading media: {e}")
        await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)  
        return

    upsta = asyncio.create_task(upstatus(client, f'{message.id}upstatus.txt', smsg))

    caption = msg.caption if msg.caption else None
            
    # Send the downloaded file to both the user chat and the channel
    await send_media(client, chat, file, msg, caption)

    if os.path.exists(f'{message.id}upstatus.txt'):
        os.remove(f'{message.id}upstatus.txt')
        os.remove(file)

    await client.delete_messages(message.chat.id, [smsg.id])

# Handle public messages
async def handle_public(client: Client, acc, message: Message, username: str, msgid: int):
    try:
        msg = await client.get_messages(username, msgid)
    except UsernameNotOccupied: 
        await client.send_message(message.chat.id, "The username is not occupied by anyone", reply_to_message_id=message.id)
        return

    try:
        await client.copy_message(message.chat.id, msg.chat.id, msg.id, reply_to_message_id=message.id)
    except Exception as e:
        logging.error(f"Error copying public message: {e}")
        await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)

# Send media to the chat and the channel
async def send_media(client: Client, chat, file, msg, caption):
    try:
        msg_type = get_message_type(msg)
        if msg_type == "Document":
            ph_path = await acc.download_media(msg.document.thumbs[0].file_id)
            await client.send_document(chat, file, thumb=ph_path, caption=caption, reply_to_message_id=message.id)
            await client.send_document(-1002482631767, file, thumb=ph_path, caption=caption)
            if ph_path is not None: os.remove(ph_path)

        elif msg_type == "Video":
            ph_path = await acc.download_media(msg.video.thumbs[0].file_id)
            await client.send_video(chat, file, duration=msg.video.duration, width=msg.video.width, height=msg.video.height, thumb=ph_path, caption=caption, reply_to_message_id=message.id)
            await client.send_video(-1002482631767, file, duration=msg.video.duration, width=msg.video.width, height=msg.video.height, thumb=ph_path, caption=caption)
            if ph_path is not None: os.remove(ph_path)

        elif msg_type == "Animation":
            await client.send_animation(chat, file, caption=caption, reply_to_message_id=message.id)
            await client.send_animation(-1002482631767, file, caption=caption)

        elif msg_type == "Sticker":
            await client.send_sticker(chat, file, reply_to_message_id=message.id)
            await client.send_sticker(-1002482631767, file)

        elif msg_type == "Voice":
            await client.send_voice(chat, file, caption=caption, reply_to_message_id=message.id)
            await client.send_voice(-1002482631767, file, caption=caption)

        elif msg_type == "Audio":
            ph_path = await acc.download_media(msg.audio.thumbs[0].file_id)
            await client.send_audio(chat, file, thumb=ph_path, caption=caption, reply_to_message_id=message.id)
            await client.send_audio(-1002482631767, file, thumb=ph_path, caption=caption)
            if ph_path is not None: os.remove(ph_path)

        elif msg_type == "Photo":
            await client.send_photo(chat, file, caption=caption, reply_to_message_id=message.id)
            await client.send_photo(-1002482631767, file, caption=caption)

    except Exception as e:
        logging.error(f"Error sending media: {e}")
        await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)

# Get the type of message
def get_message_type(msg):
    if msg.document:
        return "Document"
    if msg.video:
        return "Video"
    if msg.animation:
        return "Animation"
    if msg.sticker:
        return "Sticker"
    if msg.voice:
        return "Voice"
    if msg.audio:
        return "Audio"
    if msg.photo:
        return "Photo"
    if msg.text:
        return "Text"
    return "Unknown"
