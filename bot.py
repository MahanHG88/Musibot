"""Musibot — a Telegram bot that converts voice messages into downloadable MP3 files."""

from __future__ import annotations

import asyncio
import logging
import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("musibot")

# The Telegram Bot API caps getFile downloads at 20 MB.
MAX_FILE_SIZE = 20 * 1024 * 1024


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Greet the user and explain what the bot does."""
    await update.message.reply_text(
        "👋 Hi! Send me a voice message and I'll send it back as an MP3 file.\n\n"
        "Audio files and video notes work too."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show usage instructions."""
    await update.message.reply_text(
        "🎙 *How to use Musibot*\n\n"
        "1. Record or forward a voice message.\n"
        "2. I convert it to MP3.\n"
        "3. You get the MP3 back, ready to download.\n\n"
        "Audio files and video notes are supported as well.",
        parse_mode="Markdown",
    )


async def convert_to_mp3(source: Path, destination: Path) -> None:
    """Transcode an audio/video file to MP3 with ffmpeg.

    Raises FileNotFoundError if ffmpeg is missing, or RuntimeError on failure.
    """
    process = await asyncio.create_subprocess_exec(
        "ffmpeg",
        "-y",
        "-i", str(source),
        "-vn",               # drop any video stream (e.g. from video notes)
        "-acodec", "libmp3lame",
        "-q:a", "2",         # ~190 kbps VBR — good quality, small size
        str(destination),
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await process.communicate()
    if process.returncode != 0:
        tail = stderr.decode(errors="replace")[-500:]
        raise RuntimeError(f"ffmpeg failed (exit {process.returncode}): {tail}")


async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Download an incoming voice/audio message, convert it, and send back the MP3."""
    message = update.message
    media = message.voice or message.audio or message.video_note
    if media is None:
        return

    if media.file_size and media.file_size > MAX_FILE_SIZE:
        await message.reply_text(
            "⚠️ That file is larger than 20 MB, which is the maximum I can download."
        )
        return

    await context.bot.send_chat_action(message.chat_id, ChatAction.UPLOAD_DOCUMENT)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        source = tmp_dir / "input"
        output = tmp_dir / "audio.mp3"

        try:
            tg_file = await media.get_file()
            await tg_file.download_to_drive(custom_path=source)
        except Exception:
            logger.exception("Failed to download file")
            await message.reply_text("❌ Sorry, I couldn't download that message.")
            return

        try:
            await convert_to_mp3(source, output)
        except FileNotFoundError:
            logger.error("ffmpeg is not installed or not on PATH")
            await message.reply_text(
                "❌ The conversion tool (ffmpeg) isn't available on the server."
            )
            return
        except Exception:
            logger.exception("Conversion failed")
            await message.reply_text("❌ Sorry, I couldn't convert that audio.")
            return

        base_name = getattr(media, "file_name", None) or "voice-message"
        filename = Path(base_name).stem + ".mp3"

        with output.open("rb") as fh:
            await message.reply_audio(
                audio=fh,
                filename=filename,
                title=filename,
                caption="🎵 Here's your MP3!",
            )


def build_application() -> Application:
    """Create and configure the Telegram application."""
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise SystemExit(
            "BOT_TOKEN is not set. Copy .env.example to .env and add your token, "
            "or export BOT_TOKEN in the environment."
        )

    application = ApplicationBuilder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(
        MessageHandler(
            filters.VOICE | filters.AUDIO | filters.VIDEO_NOTE,
            handle_audio,
        )
    )
    return application


def main() -> None:
    application = build_application()
    logger.info("Musibot is running. Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
