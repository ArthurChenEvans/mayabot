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