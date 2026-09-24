# Musibot

A Telegram bot that turns **voice messages into downloadable MP3 files**. Send it
a voice note (or an audio file / video note) and it replies with a converted MP3.

## Features

- 🎙 Converts Telegram voice messages to MP3
- 🎵 Also handles audio files and video notes
- ⚡ Async, non-blocking conversion via `ffmpeg`
- 🐳 Ships with a Dockerfile for easy VPS deployment

## How it works

Telegram voice messages are OGG/Opus. Musibot downloads the file, transcodes it
to MP3 with `ffmpeg` (`libmp3lame`, ~190 kbps VBR), and sends it back as a
downloadable audio file.

## Requirements

- Python 3.10+
- [`ffmpeg`](https://ffmpeg.org/) available on `PATH`
- A bot token from [@BotFather](https://t.me/BotFather)

## Local setup

```bash
git clone https://github.com/MahanHG88/Musibot.git
cd Musibot

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env      # then edit .env and paste your BOT_TOKEN
python bot.py
```

Make sure `ffmpeg` is installed:

```bash
# Debian/Ubuntu
sudo apt-get install -y ffmpeg
# macOS
brew install ffmpeg
```

## Deploy to a VPS

### Option A — Docker (recommended)

```bash
git clone https://github.com/MahanHG88/Musibot.git
cd Musibot
docker build -t musibot .
docker run -d --name musibot --restart unless-stopped \
    -e BOT_TOKEN="your-telegram-bot-token" \
    musibot
```

Update later with:

```bash
git pull && docker build -t musibot . \
    && docker rm -f musibot \
    && docker run -d --name musibot --restart unless-stopped \
       -e BOT_TOKEN="your-telegram-bot-token" musibot
```

### Option B — systemd

```bash
sudo apt-get update && sudo apt-get install -y ffmpeg python3-venv git
git clone https://github.com/MahanHG88/Musibot.git /opt/musibot
cd /opt/musibot
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env   # edit .env and add BOT_TOKEN
```

Create `/etc/systemd/system/musibot.service`:

```ini
[Unit]
Description=Musibot Telegram bot
After=network-online.target
Wants=network-online.target

[Service]
WorkingDirectory=/opt/musibot
ExecStart=/opt/musibot/.venv/bin/python bot.py
EnvironmentFile=/opt/musibot/.env
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now musibot
sudo systemctl status musibot
journalctl -u musibot -f      # view logs
```

## Configuration

| Variable    | Description                              |
| ----------- | ---------------------------------------- |
| `BOT_TOKEN` | Telegram bot token from @BotFather (req) |

## License

MIT
