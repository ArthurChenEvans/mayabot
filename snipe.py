import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
from datetime import datetime

class SnipeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def format_time_ago(self, deleted_at):
        now = datetime.now()
        deleted_time = datetime.fromisoformat(deleted_at)
        delta = now - deleted_time

        if delta.days > 0:
            return f"{delta.days} days ago"
        elif delta.seconds // 3600 > 0:
            return f"{delta.seconds // 3600} hours ago"
        elif delta.seconds // 60 > 0:
            return f"{delta.seconds // 60} minutes ago"
        else:
            return "Just now"

    @app_commands.command(name="snipe", description="Retrieve deleted messages")
    @app_commands.describe(
        user="The user whose deleted messages to retrieve (optional)"
    )
    async def snipe(self, interaction: discord.Interaction, user: discord.Member = None):
        await interaction.response.defer(thinking=True)

        conn = sqlite3.connect('snipe_data.db')
        c = conn.cursor()

        if user:
            c.execute(
                "SELECT user_id, content, deleted_at FROM deleted_messages WHERE user_id = ? AND guild_id = ? AND channel_id = ? ORDER BY deleted_at DESC",
                (user.id, interaction.guild.id, interaction.channel.id))
            title = f"Deleted Messages for {user.name}"
        else:
            c.execute(
                "SELECT user_id, content, deleted_at FROM deleted_messages WHERE guild_id = ? AND channel_id = ? ORDER BY deleted_at DESC",
                (interaction.guild.id, interaction.channel.id))
            title = "Deleted Messages"

        results = c.fetchall()

        if results:
            pages = []
            messages_per_page = 5
            for i in range(0, len(results), messages_per_page):
                page_messages = results[i:i + messages_per_page]
                embed = discord.Embed(title=title, color=discord.Color.blue())
                for user_id, content, deleted_at in page_messages:
                    message_user = interaction.guild.get_member(user_id) or await self.bot.fetch_user(user_id)
                    user_name = message_user.display_name if message_user else f"Unknown User ({user_id})"
                    time_ago = self.format_time_ago(deleted_at)
                    embed.add_field(name=f"{user_name} - {time_ago}", value=content, inline=False)
                embed.set_footer(text=f"Page {i // messages_per_page + 1}/{(len(results) - 1) // messages_per_page + 1}")
                pages.append(embed)

            view = SnipeView(pages)
            await interaction.followup.send(embed=pages[0], view=view)
        else:
            await interaction.followup.send("No deleted messages found in this channel.")

        conn.close()

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return

        conn = sqlite3.connect('snipe_data.db')
        c = conn.cursor()
        c.execute("INSERT INTO deleted_messages (user_id, guild_id, channel_id, content, deleted_at) VALUES (?, ?, ?, ?, ?)",
                  (message.author.id, message.guild.id, message.channel.id, message.content, datetime.now().isoformat()))
        conn.commit()
        conn.close()

class SnipeView(discord.ui.View):
    def __init__(self, pages):
        super().__init__(timeout=60)
        self.pages = pages
        self.index = 0

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.grey, emoji="⬅️")
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.index > 0:
            self.index -= 1
            await interaction.response.edit_message(embed=self.pages[self.index], view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.grey, emoji="➡️")
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.index < len(self.pages) - 1:
            self.index += 1
            await interaction.response.edit_message(embed=self.pages[self.index], view=self)

async def setup(bot):
    await bot.add_cog(SnipeCog(bot))