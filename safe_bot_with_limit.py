
import os
import telebot
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = os.environ.get("API_TOKEN")
bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 Send me a video link (YouTube, TikTok, Instagram, Twitter).")

@bot.message_handler(func=lambda message: True)
def handle_url(message):
    url = message.text.strip()
    if not any(site in url for site in ['youtube', 'youtu.be', 'tiktok', 'instagram', 'twitter']):
        bot.reply_to(message, "❌ Unsupported link.")
        return

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🎥 Video", callback_data=f"video|{url}"),
        InlineKeyboardButton("🎵 Audio (MP3)", callback_data=f"audio|{url}")
    )
    bot.send_message(message.chat.id, "🔽 Choose format:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    action, url = call.data.split("|")
    chat_id = call.message.chat.id
    msg = bot.send_message(chat_id, "⏳ Downloading...")

    try:
        ydl_opts = {
            'outtmpl': 'download.%(ext)s',
            'format': 'bestaudio/best' if action == 'audio' else 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4' if action == 'video' else None,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }] if action == 'audio' else [],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if action == 'audio':
                filename = filename.rsplit('.', 1)[0] + '.mp3'

        max_size_mb = 48
        file_size_mb = os.path.getsize(filename) / (1024 * 1024)

        if file_size_mb > max_size_mb:
            bot.send_message(chat_id, f"❌ File too large to send via Telegram ({int(file_size_mb)} MB). Try a shorter or lower-quality video.")
        else:
            with open(filename, 'rb') as f:
                if action == 'audio':
                    bot.send_audio(chat_id, f)
                else:
                    bot.send_video(chat_id, f)

        os.remove(filename)

    except Exception as e:
        bot.send_message(chat_id, f"❌ Error: {str(e)}")

    bot.delete_message(chat_id, msg.message_id)

bot.polling()
