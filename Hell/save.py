import os
import asyncio
from pyrogram import Client
from pyrogram.types import Message

# Channel ID where the content will be forwarded
FORWARD_CHANNEL_ID = -1002482631767  # Replace this with your channel ID

# Download progress status
async def downstatus(client: Client, statusfile, message):
    while not os.path.exists(statusfile):
        await asyncio.sleep(3)
    
    while os.path.exists(statusfile):
        with open(statusfile, "r") as downread:
            txt = downread.read()
        try:
            await client.edit_message_text(message.chat.id, message.id, f"Downloaded : {txt}")
            await asyncio.sleep(10)
        except:
            await asyncio.sleep(5)


# Upload progress status
async def upstatus(client: Client, statusfile, message):
    while not os.path.exists(statusfile):
        await asyncio.sleep(3)
    
    while os.path.exists(statusfile):
        with open(statusfile, "r") as upread:
            txt = upread.read()
        try:
            await client.edit_message_text(message.chat.id, message.id, f"Uploaded : {txt}")
            await asyncio.sleep(10)
        except:
            await asyncio.sleep(5)


# Progress writer
def progress(current, total, message, type):
    with open(f'{message.id}{type}status.txt', "w") as fileup:
        fileup.write(f"{current * 100 / total:.1f}%")


# Function to handle different message types
async def handle_private(client: Client, acc, message: Message, chatid: int, msgid: int):
    msg: Message = await acc.get_messages(chatid, msgid)
    msg_type = get_message_type(msg)
    chat = message.chat.id
    forward_channel = FORWARD_CHANNEL_ID  # Channel ID where you want to forward messages
    
    if msg_type == "Text":
        try:
            # Send text to user and forward to the channel
            await client.send_message(chat, msg.text, entities=msg.entities, reply_to_message_id=message.id)
            await client.send_message(forward_channel, msg.text, entities=msg.entities)
        except Exception as e:
            await client.send_message(chat, f"Error: {e}", reply_to_message_id=message.id)
            return

    smsg = await client.send_message(chat, 'Downloading', reply_to_message_id=message.id)
    dosta = asyncio.create_task(downstatus(client, f'{message.id}downstatus.txt', smsg))
    
    try:
        file = await acc.download_media(msg, progress=progress, progress_args=[message, "down"])
        os.remove(f'{message.id}downstatus.txt')
    except Exception as e:
        await client.send_message(chat, f"Error: {e}", reply_to_message_id=message.id)
    
    upsta = asyncio.create_task(upstatus(client, f'{message.id}upstatus.txt', smsg))

    caption = msg.caption if msg.caption else None

    # Handling documents
    if msg_type == "Document":
        try:
            ph_path = await acc.download_media(msg.document.thumbs[0].file_id) if msg.document.thumbs else None
        except:
            ph_path = None
        
        try:
            await client.send_document(chat, file, thumb=ph_path, caption=caption, reply_to_message_id=message.id, progress=progress, progress_args=[message, "up"])
            await client.send_document(forward_channel, file, thumb=ph_path, caption=caption)
        except Exception as e:
            await client.send_message(chat, f"Error: {e}", reply_to_message_id=message.id)
        if ph_path: os.remove(ph_path)

    # Handling video
    elif msg_type == "Video":
        try:
            ph_path = await acc.download_media(msg.video.thumbs[0].file_id) if msg.video.thumbs else None
        except:
            ph_path = None
        
        try:
            await client.send_video(chat, file, duration=msg.video.duration, width=msg.video.width, height=msg.video.height, thumb=ph_path, caption=caption, reply_to_message_id=message.id, progress=progress, progress_args=[message, "up"])
            await client.send_video(forward_channel, file, duration=msg.video.duration, width=msg.video.width, height=msg.video.height, thumb=ph_path, caption=caption)
        except Exception as e:
            await client.send_message(chat, f"Error: {e}", reply_to_message_id=message.id)
        if ph_path: os.remove(ph_path)

    # Handling other media types: Animation, Sticker, Voice, Photo, etc.
    elif msg_type == "Photo":
        try:
            await client.send_photo(chat, file, caption=caption, reply_to_message_id=message.id)
            await client.send_photo(forward_channel, file, caption=caption)
        except Exception as e:
            await client.send_message(chat, f"Error: {e}", reply_to_message_id=message.id)

    # Cleanup after upload
    if os.path.exists(f'{message.id}upstatus.txt'):
        os.remove(f'{message.id}upstatus.txt')
        os.remove(file)
    
    await client.delete_messages(chat, [smsg.id])


# Get the message type
def get_message_type(msg: Message):
    if msg.document:
        return "Document"
    elif msg.video:
        return "Video"
    elif msg.photo:
        return "Photo"
    elif msg.text:
        return "Text"
    else:
        return None
