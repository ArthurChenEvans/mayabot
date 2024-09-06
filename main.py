import os
from dotenv import load_dotenv
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from openai import OpenAI
import io
import tempfile
from pydub import AudioSegment

# Load tokens from .env file
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_API_KEY = os.getenv('GPT_TOKEN')

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Set up OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Define the combined system message
SYSTEM_SETTINGS = """Your name is Maya. You are a female person with lavender hair and golden eyes. You like to wear pastel clothing."""

class BotCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="chat", description="Chat with the AI")
    @app_commands.describe(
        message="Your message to the AI",
        message_limit="Number of past messages to consider (default 20)"
    )
    async def chat(self, interaction: discord.Interaction, message: str, message_limit: int = 100):
        await interaction.response.defer(thinking=True)

        past_messages = await self.get_past_messages(interaction.channel, limit=message_limit)

        try:
            chat_completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"<system_settings>{SYSTEM_SETTINGS}</system_settings>"},
                    {"role": "system", "content": f"<past_messages>{past_messages}</past_messages>"},
                    {"role": "system", "content": f"<author>{interaction.user.name}</author>"},
                    {"role": "user", "content": message}
                ]
            )

            ai_response = chat_completion.choices[0].message.content
            await self.send_long_message(interaction, ai_response)
        except Exception as e:
            error_message = f"Omo~ Something went wrong (ノಠ益ಠ)ノ彡┻━┻: {str(e)}"
            await interaction.followup.send(error_message)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    await bot.tree.sync()
    print("Slash commands synced")

async def setup(bot):
    await bot.add_cog(BotCommands(bot))

async def main():
    async with bot:
        await setup(bot)
        await bot.start(DISCORD_TOKEN)
# Run the bot
asyncio.run(main())