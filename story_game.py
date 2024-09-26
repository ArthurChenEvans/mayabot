import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import random

class StoryGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games = {}

    @app_commands.command(name="host_story", description="Host a story writing game")
    @app_commands.describe(
        wait_time="Time in seconds to wait for each player's response",
        num_rounds="Number of rounds for the game",
        max_players="Maximum number of players allowed (including host)"
    )
    async def host_story(self, interaction: discord.Interaction, wait_time: int=120, num_rounds: int=1, max_players: int=5):
        try:
            await interaction.response.defer(thinking=True)
            await self.create_game(interaction, wait_time, num_rounds, max_players)
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}", ephemeral=True)
            print(f"Error in host_story command: {str(e)}")

    @app_commands.command(name="cancel_story", description="Cancel the story game you're hosting")
    async def cancel_story(self, interaction: discord.Interaction):
        await self.force_cancel_game(interaction)

    async def create_game(self, interaction: discord.Interaction, wait_time: int, num_rounds: int, max_players: int):
        if any(game['host'] == interaction.user for game in self.games.values()):
            await interaction.followup.send("You are already hosting a game.", ephemeral=True)
            return

        game_id = len(self.games) + 1

        self.games[game_id] = {
            'host': interaction.user,
            'players': set([interaction.user]),
            'wait_time': wait_time,
            'num_rounds': num_rounds,
            'max_players': max_players,
            'started': False,
            'story': [],
            'original_channel': interaction.channel
        }

        embed = discord.Embed(title=f"{interaction.user.name} is hosting a game of story writers!")
        embed.add_field(name="Max Players", value=str(max_players))
        embed.add_field(name="Rounds", value=str(num_rounds))
        embed.add_field(name="Wait Time", value=f"{wait_time} seconds")
        embed.add_field(
            name="How to Play",
            value=(
                "1. Players take turns adding a sentence to the story in secret.\n"
                "2. You will receive a DM when it's your turn.\n"
                "3. You have a limited time to respond (as set by the host).\n"
                "4. If you fail to respond or exceed the word limit, your turn is skipped.\n"
                "5. The game lasts for a set number of rounds, and the full story is revealed at the end!"
            ),
            inline=False
        )
        view = StoryGameView(self, interaction, game_id)
        await interaction.followup.send(embed=embed, view=view)

    async def start_game(self, interaction: discord.Interaction, game_id: int):
        game = self.games[game_id]
        if game['started']:
            return

        # Check if we can DM all players
        closed_dm_users = []
        for player in game['players']:
            try:
                await player.send("Checking if DMs are open.")
            except discord.Forbidden:
                closed_dm_users.append(player)

        if closed_dm_users:
            closed_dm_mentions = " ".join([user.mention for user in closed_dm_users])
            await interaction.followup.send(
                f"Cannot start game! {closed_dm_mentions} have their DMs set to closed. "
                "Please temporarily open your DMs if you wish to play this game.",
                ephemeral=False
            )
            return

        game['started'] = True
        players = list(game['players'])
        random.shuffle(players)

        await interaction.followup.send("The game is starting now! Check your DMs for your turn.", ephemeral=False)

        for round_num in range(1, game['num_rounds'] + 1):
            await game['original_channel'].send(f"Starting Round {round_num}")

            for player in players:
                previous_sentence = game['story'][-1] if game['story'] else "Start the story!"

                await game['original_channel'].send(f"It's now the next person's turn to add to the story! Check your DM, you've been pinged!")

                await player.send(f"It's your turn! The previous sentence was:\n\n{previous_sentence}")

                def check(m):
                    return m.author == player and isinstance(m.channel, discord.DMChannel)

                try:
                    msg = await self.bot.wait_for('message', check=check, timeout=game['wait_time'])
                    game['story'].append(msg.content)
                    await player.send("Your contribution has been added to the story!")
                except asyncio.TimeoutError:
                    await player.send("You didn't respond in time. Skipping your turn.")

        await self.end_game(interaction, game_id)

    async def end_game(self, interaction: discord.Interaction, game_id: int):
        game = self.games[game_id]
        full_story = " ".join(game['story'])
        await game['original_channel'].send("The story is complete! Here's what you all wrote:")

        if len(full_story) <= 1999:
            await game['original_channel'].send(full_story)
        else:
            parts = [full_story[i:i + 1999] for i in range(0, len(full_story), 1999)]
            for part in parts:
                await game['original_channel'].send(part)

        del self.games[game_id]

    async def cancel_game(self, interaction: discord.Interaction, game_id: int):
        game = self.games[game_id]
        await game['original_channel'].send("The game has been cancelled.")
        del self.games[game_id]
        await interaction.response.send_message("The game has been cancelled.", ephemeral=True)

    async def force_cancel_game(self, interaction: discord.Interaction):
        for game_id, game in self.games.items():
            if game['host'] == interaction.user:
                await self.cancel_game(interaction, game_id)
                return
        await interaction.response.send_message("You are not hosting any games.", ephemeral=True)


class StoryGameView(discord.ui.View):
    def __init__(self, game, interaction, game_id):
        super().__init__(timeout=None)
        self.game = game
        self.interaction = interaction
        self.game_id = game_id

    @discord.ui.button(label="Start", style=discord.ButtonStyle.green)
    async def start_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user == self.game.games[self.game_id]['host']:
            await interaction.response.defer()
            await self.game.start_game(interaction, self.game_id)
            self.disable_all_items()
            await interaction.edit_original_response(view=self)
        else:
            await interaction.response.send_message("Only the host can start the game.", ephemeral=True)

    @discord.ui.button(label="Join", style=discord.ButtonStyle.blurple)
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        game = self.game.games[self.game_id]
        if game['started']:
            await interaction.response.send_message("Sorry, the game has already started.", ephemeral=True)
        elif len(game['players']) >= game['max_players']:
            await interaction.response.send_message("This game is full.", ephemeral=True)
        elif interaction.user not in game['players']:
            game['players'].add(interaction.user)
            await interaction.response.send_message("You've joined the game!", ephemeral=True)
            await game['original_channel'].send(f"{interaction.user.mention} has joined the game!")
        else:
            await interaction.response.send_message("You've already joined the game.", ephemeral=True)

    @discord.ui.button(label="Leave", style=discord.ButtonStyle.red)
    async def leave_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        game = self.game.games[self.game_id]
        if game['started']:
            await interaction.response.send_message("Sorry, the game has already started. You can't leave now.", ephemeral=True)
        elif interaction.user in game['players'] and interaction.user != game['host']:
            game['players'].remove(interaction.user)
            await interaction.response.send_message("You've left the game.", ephemeral=True)
            await game['original_channel'].send(f"{interaction.user.mention} has left the game.")
        elif interaction.user == game['host']:
            await interaction.response.send_message("The host cannot leave the game. Use /cancel_story to end the game.", ephemeral=True)
        else:
            await interaction.response.send_message("You haven't joined the game yet.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(StoryGame(bot))