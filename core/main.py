# gemini_multichat_bot/core/main.py

import datetime
import os
import google.generativeai as genai
from dotenv import load_dotenv
import logging
import psycopg2
from psycopg2 import sql

# Define logger for the module
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("core_app") # Use a fixed name for the logger

# Test if logger is available immediately
logger.info("Logger successfully initialized in core.main module.")

# Load environment variables from .env file
# When core/main.py is imported by a script in platforms/, '../.env' is correct.
# When core/main.py might be run directly (e.g. for its own tests), it needs a different path.
# For robustness, try to determine the project root or ensure .env is always relative to the script that *starts* the process.
# For now, we assume it's run via the platform scripts.
dotenv_path_core = os.path.join(os.path.dirname(__file__), '..', '.env')
# print(f"core/main.py attempting to load .env from: {os.path.abspath(dotenv_path_core)}") # Optional debug
if load_dotenv(dotenv_path=dotenv_path_core):
    # print("core/main.py: .env loaded successfully.") # Optional debug
    pass
else:
    # print("core/main.py: .env file not found at expected location.") # Optional debug
    pass


# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not found in environment variables (checked by core/main.py).")
    # Potentially raise an exception or handle this more gracefully
else:
    # print("GEMINI_API_KEY found by core/main.py.") # Optional debug
    genai.configure(api_key=GEMINI_API_KEY)

# Initialize the Generative Model (e.g., gemini-1.5-flash)
# You can choose other models as needed
# For safety settings, refer to https://ai.google.dev/gemini-api/docs/safety-settings
SYSTEM_INSTRUCTION = (
    "You are a friendly and helpful conversational AI. "
    "Your goal is to chat with users, answer their questions, and engage in general conversation. "
    "Keep your responses natural, engaging, and concise."
)

generation_config = {
  "temperature": 0.9, # Good for creative and natural chat
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}
safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
]

# Global model instance (or initialize where needed)
model = None
if GEMINI_API_KEY:
    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash", # Using flash for speed and cost
            safety_settings=safety_settings,
            generation_config=generation_config,
            system_instruction=SYSTEM_INSTRUCTION
        )
        print("Gemini model initialized successfully.")
    except Exception as e:
        print(f"Error initializing Gemini model: {e}")

# --- Database Setup ---
DATABASE_URL = os.getenv("DATABASE_URL") # You'll set this in Render
MAX_HISTORY_MESSAGES = 20 # Store last 20 messages (user + model) for context

def get_db_connection():
    if not DATABASE_URL:
        logger.error("DATABASE_URL environment variable not set.")
        return None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except psycopg2.Error as e:
        logger.error(f"Error connecting to PostgreSQL database: {e}")
        return None

def initialize_database():
    conn = get_db_connection()
    if not conn:
        return

    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
        logger.info("Database initialized (chat_history table checked/created).")
    except psycopg2.Error as e:
        logger.error(f"Error initializing database table: {e}")
    finally:
        if conn:
            conn.close()

# Call initialize_database when the module is loaded
# This is a simple way; for more complex apps, you might do this in an explicit setup step.
if DATABASE_URL: # Only attempt if DATABASE_URL is set
    initialize_database()
else:
    logger.warning("DATABASE_URL not set. Chat history will not be persistent.")


def fetch_history_from_db(user_id: str):
    history = []
    conn = get_db_connection()
    if not conn:
        return history # Return empty history if no DB connection

    try:
        with conn.cursor() as cur:
            cur.execute(
                sql.SQL("""
                    SELECT role, content FROM chat_history
                    WHERE user_id = %s
                    ORDER BY timestamp DESC
                    LIMIT %s
                """),
                (user_id, MAX_HISTORY_MESSAGES)
            )
            # Fetch in descending order and then reverse to get chronological for Gemini
            db_records = cur.fetchall()
            for record in reversed(db_records): # Reverse to get chronological order
                history.append({"role": record[0], "parts": [record[1]]})
    except psycopg2.Error as e:
        logger.error(f"Error fetching history from DB for user {user_id}: {e}")
    finally:
        if conn:
            conn.close()
    return history

def save_message_to_db(user_id: str, role: str, content: str):
    conn = get_db_connection()
    if not conn:
        return

    try:
        with conn.cursor() as cur:
            cur.execute(
                sql.SQL("""
                    INSERT INTO chat_history (user_id, role, content)
                    VALUES (%s, %s, %s)
                """),
                (user_id, role, content)
            )
            conn.commit()
    except psycopg2.Error as e:
        logger.error(f"Error saving message to DB for user {user_id}: {e}")
    finally:
        if conn:
            conn.close()
    
    # Optional: Prune old history to keep DB size manageable (more advanced)
    # e.g., delete messages older than MAX_HISTORY_MESSAGES for this user_id

def generate_chat_response(user_id: str, current_message_text: str) -> str:
    if not model:
        return "Sorry, the AI model is not available at the moment. Please try again later."

    if not DATABASE_URL: # Fallback to in-memory if no DB
        # This part is now effectively removed by prioritizing DB
        logger.warning("DATABASE_URL not set, using non-persistent in-memory history (not recommended for production).")
        # For simplicity, if DATABASE_URL is not set, we won't use history.
        # A proper in-memory fallback would re-implement the old conversation_history dict.
        try:
            response = model.generate_content(current_message_text)
            return response.text
        except Exception as e:
            logger.error(f"Error during Gemini generation (no DB, no history): {e}")
            return "Sorry, I encountered an error processing your request."


    user_specific_history = fetch_history_from_db(user_id)
    
    current_interaction_history = user_specific_history + [{"role": "user", "parts": [current_message_text]}]

    try:
        response = model.generate_content(current_interaction_history)
        response_text = response.text

        save_message_to_db(user_id, "user", current_message_text)
        save_message_to_db(user_id, "model", response_text)
        
        return response_text
    except Exception as e:
        logger.error(f"Error during Gemini generation with DB history: {e}")
        try:
            response = model.generate_content(current_message_text)
            return response.text + " (Error with history, using simple response)"
        except Exception as e_simple:
            logger.error(f"Error during fallback Gemini generation: {e_simple}")
            return "Sorry, I encountered an error processing your request."


if __name__ == '__main__':
    print("Core logic for chat bot. Run platform-specific bot scripts to interact.")
    # The __main__ block test for generate_chat_response would need a DATABASE_URL to be set
    # or it will use the non-persistent path.

    print("\n--- Gemini Chat Test (with memory, requires DATABASE_URL to be set for persistence) ---")
    if model and DATABASE_URL: # Only run DB test if model and DB_URL are available
        # Ensure you have a .env file with DATABASE_URL for this test to work locally
        # Example: DATABASE_URL="postgresql://user:password@host:port/dbname"
        print("Attempting chat test with DB persistence...")
        test_user_id_db = "test_chat_user_db"
        # Clear history for this user for a clean test (optional)
        conn_test = get_db_connection()
        if conn_test:
            with conn_test.cursor() as cur_test:
                cur_test.execute("DELETE FROM chat_history WHERE user_id = %s", (test_user_id_db,))
            conn_test.commit()
            conn_test.close()

        print(f"User ({test_user_id_db}): Hello there, database bot!")
        print(f"Bot: {generate_chat_response(test_user_id_db, 'Hello there, database bot!')}")
        
        print(f"User ({test_user_id_db}): What is the capital of France?")
        print(f"Bot: {generate_chat_response(test_user_id_db, 'What is the capital of France?')}")

        print(f"User ({test_user_id_db}): What was my first message to you?")
        print(f"Bot: {generate_chat_response(test_user_id_db, 'What was my first message to you?')}")
        
        # Verify history in DB (you'd typically use a DB client for this)
        print(f"Current DB history for {test_user_id_db}:")
        for item in fetch_history_from_db(test_user_id_db):
            print(f"  {item['role']}: {item['parts'][0]}")

    elif not DATABASE_URL:
        print("DATABASE_URL not set in .env. Skipping persistent chat test.")
    else:
        print("Gemini model not available for chat testing.")
