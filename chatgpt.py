from openai import OpenAI
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()
OPENAI_API_KEY = os.getenv('GPT_TOKEN')
SYSTEM_SETTINGS = """Your name is Maya. You are a female person with lavender hair and golden eyes. You like to wear pastel clothing."""

class ChatGPTCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    @app_commands.command(name="chat", description="Chat with the AI")
    @app_commands.describe(
        message="Your message to the AI",
        message_limit="Number of past messages to consider (default 20)"
    )
    async def chat(self, interaction: discord.Interaction, message: str, message_limit: int = 50):
        await interaction.response.defer(thinking=True)

        past_messages = await self.get_past_messages(interaction.channel, limit=message_limit)

        try:
            chat_completion = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_SETTINGS},
                    {"role": "system", "content": f"Past messages:\n{past_messages}"},
                    {"role": "user", "content": message}
                ]
            )

            ai_response = chat_completion.choices[0].message.content

            await self.send_long_message(interaction, ai_response)

            print(past_messages)
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            await interaction.followup.send(error_message)

    async def get_past_messages(self, channel, limit=50):
        messages = []
        async for message in channel.history(limit=limit):
            if message.author == self.bot.user:
                continue
            formatted_message = f"{message.author.id} {message.author.name} {message.author.mention} @ {message.created_at.strftime('%Y-%m-%d %H:%M:%S')}: {message.content}"
            messages.append(formatted_message)
        return "\n".join(reversed(messages))

    async def send_long_message(self, interaction, content):
        try:
            if len(content) > 2000:
                for i in range(0, len(content), 2000):
                    chunk = content[i:i + 2000]
                    await interaction.followup.send(chunk)
            else:
                await interaction.followup.send(content)
        except Exception as e:
            print(f"Error sending message: {str(e)}")

async def setup(bot):
    await bot.add_cog(ChatGPTCommands(bot))