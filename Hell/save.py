# Channel ID where the bot will forward content
CHANNEL_ID = -1002482631767  # replace with your actual channel ID

# handle private
async def handle_private(client: Client, acc, message: Message, chatid: int, msgid: int):
    msg: Message = await acc.get_messages(chatid, msgid)
    msg_type = get_message_type(msg)
    chat = message.chat.id
    if "Text" == msg_type:
        try:
            await client.send_message(chat, msg.text, entities=msg.entities, reply_to_message_id=message.id)
            
            # Forward text to your channel
            await client.send_message(CHANNEL_ID, msg.text, entities=msg.entities)
        except Exception as e:
            await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)
            return

    smsg = await client.send_message(message.chat.id, 'Downloading', reply_to_message_id=message.id)
    dosta = asyncio.create_task(downstatus(client, f'{message.id}downstatus.txt', smsg))
    try:
        file = await acc.download_media(msg, progress=progress, progress_args=[message, "down"])
        os.remove(f'{message.id}downstatus.txt')
        
    except Exception as e:
        await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)  
    
    upsta = asyncio.create_task(upstatus(client, f'{message.id}upstatus.txt', smsg))

    if msg.caption:
        caption = msg.caption
    else:
        caption = None

    # Handling different media types (Document, Video, etc.)
    if "Document" == msg_type:
        try:
            ph_path = await acc.download_media(msg.document.thumbs[0].file_id)
        except:
            ph_path = None
        
        try:
            # Sending document to the user
            await client.send_document(chat, file, thumb=ph_path, caption=caption, reply_to_message_id=message.id, progress=progress, progress_args=[message, "up"])

            # Forwarding document to your channel
            await client.send_document(CHANNEL_ID, file, thumb=ph_path, caption=caption)

        except Exception as e:
            await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)
        if ph_path is not None:
            os.remove(ph_path)

    elif "Video" == msg_type:
        try:
            ph_path = await acc.download_media(msg.video.thumbs[0].file_id)
        except:
            ph_path = None
        
        try:
            # Sending video to the user
            await client.send_video(chat, file, duration=msg.video.duration, width=msg.video.width, height=msg.video.height, thumb=ph_path, caption=caption, reply_to_message_id=message.id, progress=progress, progress_args=[message, "up"])

            # Forwarding video to your channel
            await client.send_video(CHANNEL_ID, file, duration=msg.video.duration, width=msg.video.width, height=msg.video.height, thumb=ph_path, caption=caption)

        except Exception as e:
            await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)
        if ph_path is not None:
            os.remove(ph_path)

    elif "Animation" == msg_type:
        try:
            # Sending animation to the user
            await client.send_animation(chat, file, reply_to_message_id=message.id)

            # Forwarding animation to your channel
            await client.send_animation(CHANNEL_ID, file)

        except Exception as e:
            await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)

    elif "Sticker" == msg_type:
        try:
            # Sending sticker to the user
            await client.send_sticker(chat, file, reply_to_message_id=message.id)

            # Forwarding sticker to your channel
            await client.send_sticker(CHANNEL_ID, file)

        except Exception as e:
            await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)

    elif "Voice" == msg_type:
        try:
            # Sending voice message to the user
            await client.send_voice(chat, file, caption=caption, caption_entities=msg.caption_entities, reply_to_message_id=message.id, progress=progress, progress_args=[message, "up"])

            # Forwarding voice message to your channel
            await client.send_voice(CHANNEL_ID, file, caption=caption, caption_entities=msg.caption_entities)

        except Exception as e:
            await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)

    elif "Audio" == msg_type:
        try:
            ph_path = await acc.download_media(msg.audio.thumbs[0].file_id)
        except:
            ph_path = None

        try:
            # Sending audio to the user
            await client.send_audio(chat, file, thumb=ph_path, caption=caption, reply_to_message_id=message.id, progress=progress, progress_args=[message, "up"])   

            # Forwarding audio to your channel
            await client.send_audio(CHANNEL_ID, file, thumb=ph_path, caption=caption)

        except Exception as e:
            await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)
        if ph_path is not None:
            os.remove(ph_path)

    elif "Photo" == msg_type:
        try:
            # Sending photo to the user
            await client.send_photo(chat, file, caption=caption, reply_to_message_id=message.id)

            # Forwarding photo to your channel
            await client.send_photo(CHANNEL_ID, file, caption=caption)

        except Exception as e:
            await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)

    if os.path.exists(f'{message.id}upstatus.txt'): 
        os.remove(f'{message.id}upstatus.txt')
        os.remove(file)
    await client.delete_messages(message.chat.id, [smsg.id])
