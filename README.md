# LEGO Alternate Models Telegram Bot

A Telegram bot that helps users find alternative LEGO builds for a specific LEGO set using the Rebrickable API.

## Features

- Search for alternative LEGO models by set number
- Rebrickable API integration
- Russian and English language support
- Interactive Telegram buttons
- Pagination for search results
- Filter models with PDF building instructions
- Saves the user's preferred language

## Commands

- `/start` — open the main menu
- `/alts <set_number>` — search for alternative models
- `/lang` — change the interface language

Example:

```text
/alts 77244-1
```

## Technologies

- Python
- python-telegram-bot
- Telegram Bot API
- Rebrickable API

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/iljakakov/lego-telegram-bot.git
cd lego-telegram-bot
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

The bot requires the following environment variables:

```text
BOT_TOKEN
REBRICKABLE_API_KEY
```

You can get:

- `BOT_TOKEN` from Telegram BotFather
- `REBRICKABLE_API_KEY` from Rebrickable

Example for Linux/macOS:

```bash
export BOT_TOKEN="your_telegram_bot_token"
export REBRICKABLE_API_KEY="your_rebrickable_api_key"
```

Example for Windows PowerShell:

```powershell
$env:BOT_TOKEN="your_telegram_bot_token"
$env:REBRICKABLE_API_KEY="your_rebrickable_api_key"
```

### 4. Run the bot

```bash
python lego_alt_bot.py
```

## How to Use

Start the bot in Telegram and use:

```text
/start
```

To search for alternative LEGO models, enter a LEGO set number in the full format:

```text
77244-1
```

or use:

```text
/alts 77244-1
```

The bot will request available alternate builds from Rebrickable and display information about them.

## Search Results

The bot can display information such as:

- Model name
- Designer
- Number of parts
- Availability of building instructions
- Link to the model

You can browse through results using navigation buttons.

The bot also allows you to filter results and show only models that have PDF building instructions.

## Language Support

The bot supports:

- English
- Russian

Use:

```text
/lang
```

to change the interface language.

## API

This project uses the Rebrickable API to retrieve information about LEGO sets and alternate models.

You need your own Rebrickable API key to run the bot.

## Requirements

Main dependency:

```text
python-telegram-bot==21.6
```

Install all dependencies using:

```bash
pip install -r requirements.txt
```

## Security

Do not publish your Telegram bot token or Rebrickable API key directly in the source code.

Use environment variables instead:

```text
BOT_TOKEN
REBRICKABLE_API_KEY
```
