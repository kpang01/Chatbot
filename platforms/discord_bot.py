# gemini_multichat_bot/platforms/discord_bot.py

import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv

# Import core logic
import re # For parsing due date
from core import main as core_logic

# Load environment variables from .env file (expected in the parent directory)
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Configure logging
logger = logging.getLogger('discord') # Using discord's logger
logger.setLevel(logging.INFO) # Or logging.DEBUG for more verbosity
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# Define intents
# discord.py 2.0+ requires explicit intents.
# For a basic bot, default intents might be enough, but for reading messages, message_content is needed.
intents = discord.Intents.default()
intents.message_content = True  # Crucial for reading message content
intents.members = True # If you need member information

# Initialize the bot
# Using commands.Bot for command handling
bot = commands.Bot(command_prefix="!", intents=intents) # Using '!' as the command prefix

@bot.event
async def on_ready():
    """Event handler for when the bot has successfully connected."""
    logger.info(f'{bot.user.name} has connected to Discord!')
    logger.info(f'User ID: {bot.user.id}')
    logger.info('Bot is ready and listening for commands.')
    try:
        # Sync commands if using slash commands (discord.app_commands)
        # For traditional prefix commands, this is not strictly necessary on startup
        # but good practice if you mix them or plan to use app_commands.
        # synced = await bot.tree.sync()
        # logger.info(f"Synced {len(synced)} slash commands.")
        pass # Not using slash commands for now
    except Exception as e:
        logger.error(f"Error syncing slash commands: {e}")

# Placeholder for a simple ping command
@bot.command(name='ping')
async def ping(ctx):
    """A simple command that replies with Pong!"""
    await ctx.send('Pong!')

@bot.command(name='help')
async def help_discord(ctx):
    """Shows this help message."""
    help_text = (
        "I'm a conversational chatbot powered by Gemini!\n\n"
        "You can chat with me about various topics, ask questions, or just have a friendly conversation.\n"
        "My command prefix is `!`.\n\n"
        "**Commands:**\n"
        "  `!help` - Show this help message.\n"
        "  `!ping` - Check if I'm responsive.\n\n"
        "Just type your message (without a prefix) to chat with me!"
    )
    await ctx.send(help_text)

@bot.event
async def on_message(message):
    """Handles messages that are not commands."""
    if message.author == bot.user: # Ignore messages from the bot itself
        return

    # If the message starts with the command prefix, let the command system handle it.
    # This ensures commands like !help and !ping are processed correctly.
    if message.content.startswith(bot.command_prefix):
        await bot.process_commands(message)
        return

    # If it's not a command and not from the bot, then process with Gemini chat logic
    user_id = str(message.author.id)
    text = message.content
    
    # Pass the platform-specific logger to the core logic
    response_text = core_logic.generate_chat_response(user_id, text, logger)
    
    # Discord messages have a 2000 character limit.
    if len(response_text) > 2000:
        await message.channel.send(f"{response_text[:1997]}...")
    else:
        await message.channel.send(response_text)

def main():
    if not DISCORD_BOT_TOKEN:
        logger.error("DISCORD_BOT_TOKEN not found in environment variables. Discord bot cannot start.")
        return

    logger.info("Starting Discord bot...")
    try:
        bot.run(DISCORD_BOT_TOKEN)
    except discord.LoginFailure:
        logger.error("Login failed: Invalid Discord token.")
    except Exception as e:
        logger.error(f"An error occurred while running the Discord bot: {e}")
    logger.info("Discord bot stopped.")

if __name__ == "__main__":
    # This allows running the Discord bot independently for testing
    # In a real deployment, you might have a main script that runs all bots.
    main()
