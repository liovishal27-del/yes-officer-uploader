import os
import asyncio
import logging
from pyrogram import Client, filters, idle
from pyrogram.types import Message

# Logging enable kar diya taaki Railway logs me clear status dikhe
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Telegram Credentials (Environment Variables se fetch honge)
API_ID = int(os.environ.get("API_ID", 26754022))
API_HASH = os.environ.get("API_HASH", "1a0b65e7a4d48e08687c732bdc0f2cc4")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8747409837:AAG5m8BWGAEStaeJG9Ap2JCEQmXD56HSsVM")
SESSION_STRING = os.environ.get(
    "SESSION_STRING", 
    "BQGYO-YAIzfjyhiATdYlWveX_thkH7LYgPn-ThFuP1VKGq3NufR6uMaQ5rv5Pv587lz8xlnj3yk-V_E0dToDmVFuXa3v3EN9dzvHV7Y1Ti0XHP8ovxu7pW8DfmRXeEx8WLuEurD5KRu0nDp19b08a455ZYC1pjFmVGUqoXXDTHqATGUB9YFVEjwixGod_EaHgRVCk4zTlq_3hsbxv0fY_hIl-I-xhAaAOzKbBY1q_VSGZO8k5stpkxvcG-qGuKJveEuA3ufZWqc55qqLOX2OXMEoFuHOx_tSjzuVevG6ms7fjCubbI0sku6LBXKxTy4AAl-TksOStXy38nWjZIUoXhtSU56TTQAAAAHu4zxfAA"
)
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", -1004392101092))

# Clients Setup
bot = Client("bot_instance", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user_app = Client("user_instance", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)


# Fast Downloader using aria2c
async def fast_download(url, output_filename):
    cmd = [
        "aria2c",
        "-x", "16",
        "-s", "16",
        "-k", "1M",
        "-o", output_filename,
        url
    ]
    process = await asyncio.create_subprocess_exec(*cmd)
    await process.communicate()
    return os.path.exists(output_filename)


# /start command handler (Lio Bankers Welcome & Steps)
@bot.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    welcome_text = (
        "👋 **Welcome to Lio Bankers Uploader Bot!**\n\n"
        "Main aapki PDF aur Video links ko high-speed download karke target channel me upload kar sakta hu.\n\n"
        "📌 **Kaise use karein (Steps):**\n"
        "1️⃣ Aap links wali TXT file ya text message ready rakhein.\n"
        "2️⃣ Format aisa hona chahiye:\n"
        "   `Title : https://example.com/video.mp4`\n"
        "3️⃣ Kisi bhi text ya `.txt` file ko reply karte waqt **`/drm`** command likhein.\n\n"
        "⚡ *Powered by Lio Bankers System*"
    )
    await message.reply_text(welcome_text)


# /drm command handler
@bot.on_message(filters.command("drm") & filters.private)
async def handle_drm_command(client: Client, message: Message):
    raw_text = ""

    if message.reply_to_message and message.reply_to_message.text:
        raw_text = message.reply_to_message.text
    elif len(message.command) > 1:
        raw_text = message.text.split(maxsplit=1)[1]
    elif message.reply_to_message and message.reply_to_message.document:
        doc_path = await message.reply_to_message.download()
        with open(doc_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
        os.remove(doc_path)
    else:
        await message.reply_text("❌ Kripya `/drm` command ke sath text/TXT file reply karein.")
        return

    status_msg = await message.reply_text("⚡ Processing batch...")
    lines = [line.strip() for line in raw_text.strip().split("\n") if line.strip()]
    total = len(lines)

    for index, line in enumerate(lines, 1):
        if "http" not in line:
            continue

        try:
            if ":" in line:
                parts = line.split("http", 1)
                title = parts[0].replace(":", "").strip()
                url = "http" + parts[1].strip()
            else:
                title = f"File_{index}"
                url = line.strip()

            clean_title = "".join([c for c in title if c.isalnum() or c in (' ', '_', '-')]).rstrip()

            if ".pdf" in url.lower():
                file_name = f"{clean_title}.pdf"
                is_video = False
            else:
                file_name = f"{clean_title}.mkv"
                is_video = True

            await status_msg.edit_text(f"📥 **Downloading [{index}/{total}]:**\n`{clean_title}`")

            download_success = await fast_download(url, file_name)

            if download_success and os.path.exists(file_name):
                file_size_mb = os.path.getsize(file_name) / (1024 * 1024)
                await status_msg.edit_text(
                    f"📤 **Uploading [{index}/{total}]** ({file_size_mb:.1f} MB):\n`{clean_title}`"
                )

                if is_video:
                    await user_app.send_video(
                        chat_id=CHANNEL_ID,
                        video=file_name,
                        caption=f"🎥 **{clean_title}**",
                        supports_streaming=True
                    )
                else:
                    await user_app.send_document(
                        chat_id=CHANNEL_ID,
                        document=file_name,
                        caption=f"📄 **{clean_title}**"
                    )

                os.remove(file_name)
            else:
                await message.reply_text(f"❌ Download Failed for: `{clean_title}`")

        except Exception as e:
            await message.reply_text(f"⚠️ Error in line {index}: `{str(e)}`")
            if 'file_name' in locals() and os.path.exists(file_name):
                os.remove(file_name)

    await status_msg.edit_text("✅ **Sabhi files successfully upload ho gayi hain!**")


async def start_services():
    await user_app.start()
    await bot.start()
    print("--------------------------------------------------")
    print("🚀 LIO BANKERS BOT IS NOW ONLINE & READY TO USE!")
    print("--------------------------------------------------")
    await idle()
    await bot.stop()
    await user_app.stop()

if __name__ == "__main__":
    asyncio.run(start_services())
