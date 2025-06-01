# Gemini Multichat Conversational Bot

This project implements a conversational chatbot powered by Google's Gemini API, with integrations for Telegram, Discord, and WhatsApp (via Twilio). The bot is designed for general chatting and can remember the context of your conversation.

## Features

-   **Conversational AI**: Engage in general conversations, ask questions, and get informative responses.
-   **Conversation Memory**: Remembers previous parts of your chat for more contextual interactions.
-   **Multi-Platform**: Interact with the bot on Telegram, Discord, and WhatsApp.
-   **Gemini Powered**: Utilizes Gemini for natural language understanding and response generation.

## Project Structure

```
gemini_multichat_bot/
├── core/
│   ├── __init__.py
│   └── main.py             # Core chatbot logic, task management, Gemini API interaction
├── platforms/
│   ├── __init__.py
│   ├── telegram_bot.py     # Telegram bot specific logic
│   ├── discord_bot.py      # Discord bot specific logic
│   └── whatsapp_bot.py     # WhatsApp integration (Flask app for Twilio webhooks)
├── .env.example            # Example environment variables
├── .gitignore              # Git ignore file
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## Setup

1.  **Clone the repository (if applicable)**:
    ```bash
    # git clone <repository_url>
    # cd gemini_multichat_bot
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    ```
    Activate it:
    -   Windows: `venv\Scripts\activate`
    -   macOS/Linux: `source venv/bin/activate`

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables**:
    -   Copy `.env.example` to a new file named `.env` in the `gemini_multichat_bot` directory.
        ```bash
        cp .env.example .env
        ```
    -   Open the `.env` file and fill in your API keys and tokens:
        -   `GEMINI_API_KEY`: Your Google Gemini API key.
        -   `TELEGRAM_BOT_TOKEN`: Your Telegram Bot Token from BotFather.
        -   `DISCORD_BOT_TOKEN`: Your Discord Bot Token from the Discord Developer Portal.
        -   `TWILIO_ACCOUNT_SID`: Your Twilio Account SID.
        -   `TWILIO_AUTH_TOKEN`: Your Twilio Auth Token.
        -   `TWILIO_WHATSAPP_NUMBER`: Your Twilio WhatsApp-enabled number (e.g., `whatsapp:+14155238886`).
        -   `DATABASE_URL`: (Recommended for persistent conversation memory) Your PostgreSQL connection URL. For example, `postgresql://user:password@host:port/dbname`. If deploying on Render, create a PostgreSQL instance and use the provided connection string.

## Running the Bots

Each bot typically runs as a separate process.

### 1. Telegram Bot

Navigate to the `platforms` directory and run:
```bash
cd platforms
python telegram_bot.py
```
Ensure your `.env` file is in the parent directory (`gemini_multichat_bot/.env`) or adjust the `dotenv_path` in `telegram_bot.py`.

### 2. Discord Bot

Navigate to the `platforms` directory and run:
```bash
cd platforms
python discord_bot.py
```
Ensure your `.env` file is in the parent directory (`gemini_multichat_bot/.env`) or adjust the `dotenv_path` in `discord_bot.py`.

### 3. WhatsApp Bot (Twilio & Flask)

The WhatsApp bot requires a publicly accessible webhook for Twilio.

1.  **Run the Flask server**:
    Navigate to the `platforms` directory and run:
    ```bash
    cd platforms
    python whatsapp_bot.py
    ```
    This will typically start the server on `http://127.0.0.1:5002`.

2.  **Expose the webhook**:
    Since Twilio needs to reach your Flask server over the internet, you'll need to expose your local server. Tools like `ngrok` are excellent for this during development.
    ```bash
    ngrok http 5002
    ```
    `ngrok` will provide you with a public URL (e.g., `https://your-unique-id.ngrok.io`).

3.  **Configure Twilio Webhook**:
    -   Go to your Twilio console.
    -   Navigate to your WhatsApp Senders (Phone Numbers > Active Numbers > Select your WhatsApp number, or Messaging > Senders > WhatsApp Senders).
    -   Under "Messaging Configuration" or similar, find the "A MESSAGE COMES IN" webhook setting.
    -   Set the webhook URL to `https://your-unique-id.ngrok.io/whatsapp_webhook` (replace with your actual ngrok URL) and ensure the method is `HTTP POST`.
    -   Save the configuration.

Now, messages sent to your Twilio WhatsApp number should be forwarded to your local Flask application.

## Usage

-   **Telegram**: Interact with your bot by sending any message to chat. Use `/start` for a welcome message and `/help` for basic info.
-   **Discord**: Interact with your bot by sending any message (without a command prefix) to chat. Use `!help` for basic info and `!ping` to check responsiveness.
-   **WhatsApp**: Send any message to chat with the bot.

## Further Development

-   More sophisticated error handling and resilience.
-   Advanced database schema/logic for history pruning or summarization.
-   Deployment to a server environment (this README provides Render guidance).
-   Unit and integration tests.
-   A unified script to manage running all bots (e.g., using `multiprocessing` or `asyncio` for concurrent execution, though separate processes are often simpler for different bot types).
