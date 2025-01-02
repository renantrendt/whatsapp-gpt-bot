# WhatsApp GPT Bot

A Python bot that automatically responds to WhatsApp Web messages using ChatGPT.

## Features

- Automatically responds to messages starting with "GPT"
- Uses OpenAI's GPT-3.5 Turbo model
- Works with WhatsApp Web
- Natural typing simulation

## Setup

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/whatsapp-gpt-bot.git
cd whatsapp-gpt-bot
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Create a `.env` file with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

4. Run the bot:
```bash
python bot.py
```

5. Scan the QR code with WhatsApp on your phone to log in to WhatsApp Web.

## Usage

1. Send a message starting with "GPT" in your WhatsApp chat
2. The bot will automatically respond using ChatGPT
3. Example: "GPT what is the capital of Brazil?"

## Requirements

- Python 3.8+
- Chrome browser installed
- OpenAI API key
- Active internet connection

## License

MIT License
