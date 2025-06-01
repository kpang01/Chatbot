# gemini_multichat_bot/platforms/whatsapp_bot.py

from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import os
import logging
from dotenv import load_dotenv

# Import core logic
from core import main as core_logic

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
# TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER") # This is your Twilio WhatsApp number

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Twilio client (optional here if only receiving, but good for sending replies)
# client = None
# if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
#     client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
# else:
#     logger.warning("Twilio credentials not found. Sending replies might not work.")


def process_whatsapp_message(user_id: str, message_body: str) -> str:
    """
    Processes the incoming WhatsApp message using core logic and Gemini.
    This function will determine if it's a command or general text.
    """
    # Basic command parsing (can be made more sophisticated)
    # For WhatsApp, users might not use a prefix like '!' or '/'
    # We might need to rely more on Gemini to interpret intent or define keywords.
    
    # Example: if message_body.lower().startswith("add task"):
    #    _, task_content = message_body.split("add task", 1)
    #    description, _, due_date_str = task_content.strip().partition(" due ")
    #    return core_logic.add_task(user_id, description.strip(), due_date_str.strip() or None)
    # elif message_body.lower() == "list tasks":
    #    return core_logic.list_tasks(user_id)
    # ... and so on for other commands.

    # Use the new generate_chat_response function from core_logic
    # The SYSTEM_INSTRUCTION in core_logic.py will guide the model's general behavior.
    # The user_id for WhatsApp will be their phone number (e.g., "whatsapp:+14155238886")
    response_text = core_logic.generate_chat_response(user_id, message_body)
    return response_text

@app.route("/whatsapp_webhook", methods=["POST"])
def whatsapp_webhook():
    """
    Endpoint to receive incoming WhatsApp messages from Twilio.
    """
    incoming_msg = request.values.get('Body', '').strip()
    sender_id = request.values.get('From', '') # e.g., 'whatsapp:+14155238886'
    
    logger.info(f"Received WhatsApp message from {sender_id}: {incoming_msg}")

    if not incoming_msg or not sender_id:
        logger.warning("Received empty message or no sender ID.")
        return Response(status=400) # Bad request

    # Process the message using our core logic / Gemini
    reply_text = process_whatsapp_message(sender_id, incoming_msg)

    # Create a TwiML response
    twiml_response = MessagingResponse()
    twiml_response.message(reply_text)

    return Response(str(twiml_response), mimetype="application/xml")

def main():
    """
    Runs the Flask app for the WhatsApp bot.
    Note: For production, use a proper WSGI server like Gunicorn or Waitress.
    """
    logger.info("Starting WhatsApp bot (Flask server)...")
    # Make sure to configure your Twilio WhatsApp number's webhook
    # to point to this server's /whatsapp_webhook endpoint (e.g., using ngrok for local dev).
    app.run(port=5002, debug=True) # Using port 5002 to avoid conflict if other servers run

if __name__ == "__main__":
    main()
