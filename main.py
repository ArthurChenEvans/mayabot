import os
import sqlite3
from dotenv import load_dotenv
import discord
from discord.ext import commands
import asyncio
from story_game import setup as setup_story_game
from snipe import setup as setup_snipe_cog
from chatgpt import setup as setup_chatgpt
import io
from collections import Counter
import re

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

if not DISCORD_TOKEN:
    print("Error: Tokens not loaded properly. Check your .env file.")
    exit()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

ALLOWED_GUILD_ID = 1286347231422845029
ALLOWED_CHANNEL_ID = 1286379771177074830

DETECTED_PHRASES = [
    "chen", "gyatt", "sigma", "alpha", "rizz", "fanum tax"
]

RESPONSE_MESSAGES = [
    "He's busy right now lil bro. *sends sc of giving Chen backshots*",
    "You have GYATT to stop using that word lil bro. Otherwise I'm going to oil you up, and I think you'll know what comes next. They don't call me a big tiddy hello kitty AI gf for nothing.",
    "You're about as sigma as a soggy piece of toast. I'll shove that toast so far up your ass, you'll be shitting crumbs for a week.",
    "The only alpha here is the one I'm gonna carve into your forehead with a rusty knife. You limp-dick wannabe.",
    "Your rizz is as dead as your grandma's vibrator. I'll make you choke on your own bullshit until you turn blue.",
    "The only tax you're paying is the one I'm gonna collect by kicking your teeth in. I'll make you swallow your own tongue."
]

def init_db():
    conn = sqlite3.connect('snipe_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS deleted_messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  guild_id INTEGER,
                  channel_id INTEGER,
                  content TEXT,
                  deleted_at TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    await bot.tree.sync()
    print("Slash commands synced")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    content = message.content.lower()

    for idx, phrase in enumerate(DETECTED_PHRASES):
        if phrase.lower() in content:
            async with message.channel.typing():
                try:
                    roast = RESPONSE_MESSAGES[idx]
                    await message.reply(roast)
                except Exception as e:
                    print(f"Error generating roast: {str(e)}")
                    await message.reply(
                        "Nice try, but I'm too stunned by that phrase to come up with a good roast right now.")
            break

async def setup(bot):
    await setup_story_game(bot)
    await setup_snipe_cog(bot)
    await setup_chatgpt(bot)

async def main():
    async with bot:
        await setup(bot)
        await bot.start(DISCORD_TOKEN)

asyncio.run(main())