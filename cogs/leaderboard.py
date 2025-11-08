import discord
from discord.ext import commands
from discord import app_commands

class LeaderboardView(discord.ui.View):
    def __init__(self, bot, players_data):
        super().__init__(timeout=300)
        self.bot = bot
        self.players_data = players_data
        self.game_type = "r6"
        self.game_names = {
            "r6": "Rainbow Six Siege",
            "rl": "Rocket League",
            "valorant": "Valorant",
            "breachers": "Breachers"
        }

    async def create_embed(self):
        embed = discord.Embed(
            title=f"{self.game_names[self.game_type]} - Top 10 Players",
            color=discord.Color.gold()
        )

        top_players = self.players_data[self.game_type]

        if not top_players:
            embed.description = "No players found for this game yet."
            return embed

        for idx, (user_id, mmr) in enumerate(top_players, 1):
            try:
                user = await self.bot.fetch_user(user_id)
                username = user.display_name
                avatar_url = user.display_avatar.url
            except:
                username = "Unknown User"
                avatar_url = None

            embed.add_field(
                name=f"#{idx} - {username}",
                value=f"**MMR:** {mmr}",
                inline=False
            )

            if idx == 1 and avatar_url:
                embed.set_thumbnail(url=avatar_url)

        return embed

    @discord.ui.select(
        placeholder="Select a game",
        options=[
            discord.SelectOption(label="Rainbow Six Siege", value="r6"),
            discord.SelectOption(label="Rocket League", value="rl"),
            discord.SelectOption(label="Valorant", value="valorant"),
            discord.SelectOption(label="Breachers", value="breachers"),
        ],
        custom_id="leaderboard_game_select"
    )
    async def game_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.game_type = select.values[0]
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label="◄", style=discord.ButtonStyle.blurple, custom_id="leaderboard_prev")
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

    @discord.ui.button(label="►", style=discord.ButtonStyle.blurple, custom_id="leaderboard_next")
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()


class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="leaderboard", description="View the leaderboard for each game")
    async def leaderboard(self, interaction: discord.Interaction):
        await interaction.response.defer()

        game_types = ["r6", "rl", "valorant", "breachers"]
        players_data = {}

        for game in game_types:
            top_players = await self.bot.db.get_top_mmr_players(game, limit=10)
            players_data[game] = top_players

        view = LeaderboardView(self.bot, players_data)
        embed = await view.create_embed()

        await interaction.followup.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Leaderboard(bot))
