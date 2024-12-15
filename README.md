# TikTok Uploader Telegram Bot

A Telegram bot that allows you to easily upload videos to TikTok, with support for scheduling uploads up to 10 days in advance.

## Features

- ✨ Upload videos directly through Telegram
- 📅 Schedule uploads up to 10 days in advance
- 🎯 Customizable video titles
- 🛠️ Simple command interface

## Prerequisites

- Python 3.7+
- Node.js (required for TikTok signature generation)
- Telegram Bot Token (get it from [@BotFather](https://t.me/botfather))

## Installation

1. Clone the repository:

```bash
git clone [your-repository-url]
```

2. Install Python requirements:

```bash
pip install -r requirements.txt
```

3. Install Node.js requirements:

```bash
cd tiktok_uploader/tiktok-signature/
npm i
```

4. Create a `.env` file and add your Telegram bot token:

```bash
TELEGRAM_TOKEN=your_telegram_bot_token_here
```

5. Run the bot:

```bash
python telegrambot.py
```

6. Start the bot by sending `/start` to your bot in Telegram.

