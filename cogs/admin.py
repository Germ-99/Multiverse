import discord
from discord.ext import commands
from discord import app_commands
from typing import Literal, Optional
from utils.permissions import check_admin_permissions

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="mmr-view", description="View MMR stats for a player")
    @app_commands.describe(
        game="Game to view stats for",
        user="User to view (leave blank for yourself)",
        ephemeral="Whether to send as an ephemeral message (default: True)"
    )
    async def mmr_view(
        self,
        interaction: discord.Interaction,
        game: Literal["r6", "rl", "valorant", "breachers"],
        user: Optional[discord.Member] = None,
        ephemeral: bool = True
    ):
        target_user = user if user else interaction.user
        
        stats = await self.bot.db.get_player_stats(target_user.id, game)
        
        game_names = {
            "r6": "Rainbow Six Siege",
            "rl": "Rocket League",
            "valorant": "Valorant",
            "breachers": "Breachers"
        }
        
        embed = discord.Embed(
            title=f"{target_user.display_name}'s {game_names[game]} Stats",
            color=discord.Color.blue()
        )
        
        embed.set_thumbnail(url=target_user.display_avatar.url)
        
        embed.add_field(name="MMR", value=str(stats['mmr']), inline=True)
        embed.add_field(name="Games Played", value=str(stats['games_played']), inline=True)
        embed.add_field(name="Wins", value=str(stats['wins']), inline=True)
        embed.add_field(name="Losses", value=str(stats['losses']), inline=True)
        
        if stats['games_played'] > 0:
            winrate = (stats['wins'] / stats['games_played']) * 100
            embed.add_field(name="Win Rate", value=f"{winrate:.1f}%", inline=True)
        else:
            embed.add_field(name="Win Rate", value="N/A", inline=True)
        
        embed.add_field(name="W/L", value=f"{stats['wins']}/{stats['losses']}", inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=ephemeral)
    
    @app_commands.command(name="mmr-change", description="ADMIN: Change a player's MMR by an amount")
    @app_commands.describe(
        user="User to modify",
        game="Game to modify MMR for",
        amount="Amount to change (use negative to subtract)"
    )
    async def mmr_change(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        game: Literal["r6", "rl", "valorant", "breachers"],
        amount: int
    ):
        if not check_admin_permissions(interaction):
            await interaction.response.send_message(
                "You do not have the permissions to do this command.",
                ephemeral=True
            )
            return
        
        current_mmr = await self.bot.db.get_player_mmr(user.id, game)
        new_mmr = max(0, current_mmr + amount)
        
        await self.bot.db.update_player_mmr(
            user.id,
            game,
            new_mmr,
            f"Manual adjustment by {interaction.user.display_name}"
        )
        
        game_names = {
            "r6": "Rainbow Six Siege",
            "rl": "Rocket League",
            "valorant": "Valorant",
            "breachers": "Breachers"
        }
        
        change_text = f"+{amount}" if amount >= 0 else str(amount)
        
        embed = discord.Embed(
            title="MMR Changed",
            description=f"Updated {user.mention}'s {game_names[game]} MMR",
            color=discord.Color.green()
        )
        
        embed.add_field(name="Previous MMR", value=str(current_mmr), inline=True)
        embed.add_field(name="Change", value=change_text, inline=True)
        embed.add_field(name="New MMR", value=str(new_mmr), inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="mmr-set", description="ADMIN: Set a player's MMR to a specific value")
    @app_commands.describe(
        user="User to modify",
        game="Game to modify MMR for",
        amount="New MMR value"
    )
    async def mmr_set(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        game: Literal["r6", "rl", "valorant", "breachers"],
        amount: int
    ):
        if not check_admin_permissions(interaction):
            await interaction.response.send_message(
                "You do not have the permissions to do this command.",
                ephemeral=True
            )
            return
        
        if amount < 0:
            await interaction.response.send_message(
                "MMR cannot be negative!",
                ephemeral=True
            )
            return
        
        current_mmr = await self.bot.db.get_player_mmr(user.id, game)
        
        await self.bot.db.update_player_mmr(
            user.id,
            game,
            amount,
            f"MMR set by {interaction.user.display_name}"
        )
        
        game_names = {
            "r6": "Rainbow Six Siege",
            "rl": "Rocket League",
            "valorant": "Valorant",
            "breachers": "Breachers"
        }
        
        embed = discord.Embed(
            title="MMR Set",
            description=f"Set {user.mention}'s {game_names[game]} MMR",
            color=discord.Color.green()
        )
        
        embed.add_field(name="Previous MMR", value=str(current_mmr), inline=True)
        embed.add_field(name="New MMR", value=str(amount), inline=True)
        embed.add_field(name="Change", value=f"{amount - current_mmr:+d}", inline=True)
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Admin(bot))