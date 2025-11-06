import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from typing import Literal

class RLReadyUpView(discord.ui.View):
    def __init__(self, bot, players, channel, queue_number, pool, mode, message=None):
        super().__init__(timeout=240)
        self.bot = bot
        self.players = players
        self.channel = channel
        self.queue_number = queue_number
        self.ready_players = []
        self.pool = pool
        self.mode = mode
        self.max_players = len(players)
        self.message = message
        self.start_time = asyncio.get_event_loop().time()
    
    @discord.ui.button(label="Ready Up", style=discord.ButtonStyle.green, custom_id="rl_ready_up")
    async def ready_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in self.players:
            await interaction.response.send_message("You are not in this match!", ephemeral=True)
            return
        
        if interaction.user.id in self.ready_players:
            await interaction.response.send_message("You are already readied up!", ephemeral=True)
            return
        
        self.ready_players.append(interaction.user.id)
        
        elapsed_time = int(asyncio.get_event_loop().time() - self.start_time)
        remaining_time = 240 - elapsed_time
        minutes = remaining_time // 60
        seconds = remaining_time % 60
        
        ready_list = '\n'.join([f"<@{player_id}> ✅" for player_id in self.ready_players])
        unready_list = '\n'.join([f"<@{player_id}> ⏳" for player_id in self.players if player_id not in self.ready_players])
        
        embed = discord.Embed(
            title=f"{len(self.ready_players)}/{self.max_players} readied up",
            description=f"**Ready:**\n{ready_list}\n\n**Not Ready:**\n{unready_list}" if unready_list else f"**Ready:**\n{ready_list}",
            color=discord.Color.orange()
        )
        embed.set_footer(text=f"Time remaining: {minutes}m {seconds}s")
        
        await interaction.response.edit_message(embed=embed, view=self)
        
        if len(self.ready_players) == self.max_players:
            await self.start_match(interaction)
    
    async def on_timeout(self):
        unready_players = [player for player in self.players if player not in self.ready_players]
        
        if len(self.pool) >= len(unready_players):
            substitutes = self.pool[:len(unready_players)]
            for player_id in substitutes:
                self.pool.remove(player_id)
            
            for i, player_id in enumerate(unready_players):
                self.players.remove(player_id)
                self.players.append(substitutes[i])
                
                member = self.channel.guild.get_member(player_id)
                if member:
                    await self.channel.set_permissions(member, read_messages=False)
                
                sub_member = self.channel.guild.get_member(substitutes[i])
                if sub_member:
                    await self.channel.set_permissions(sub_member, read_messages=True)
                
                current_mmr = await self.bot.db.get_player_mmr(player_id, "rl")
                await self.bot.db.update_player_mmr(player_id, "rl", current_mmr - 80, "Failed to ready up")
            
            unready_mentions = ', '.join([f'<@{p}>' for p in unready_players])
            sub_mentions = ', '.join([f'<@{p}>' for p in substitutes])
            
            embed = discord.Embed(
                title="Players Substituted",
                description=f"**Removed (-80 MMR):** {unready_mentions}\n**Added:** {sub_mentions}",
                color=discord.Color.yellow()
            )
            await self.channel.send(embed=embed)
            
            ready_view = RLReadyUpView(self.bot, self.players, self.channel, self.queue_number, self.pool, self.mode)
            ready_list = '\n'.join([f"<@{player_id}> ⏳" for player_id in self.players])
            embed = discord.Embed(
                title=f"0/{self.max_players} readied up",
                description=f"**Not Ready:**\n{ready_list}",
                color=discord.Color.orange()
            )
            embed.set_footer(text="Time remaining: 4m 0s")
            ready_message = await self.channel.send(embed=embed, view=ready_view)
            ready_view.message = ready_message
        else:
            if self.message:
                try:
                    await self.message.delete()
                except:
                    pass
            
            unready_mentions = ', '.join([f'<@{player}>' for player in unready_players])
            embed = discord.Embed(
                title="Not All Players Readied Up",
                description=f"Canceling queue in 10 seconds.\n\n**Players who didn't ready up:** {unready_mentions}",
                color=discord.Color.red()
            )
            await self.channel.send(embed=embed)
            
            for player_id in unready_players:
                current_mmr = await self.bot.db.get_player_mmr(player_id, "rl")
                await self.bot.db.update_player_mmr(player_id, "rl", current_mmr - 80, "Failed to ready up")
            
            await asyncio.sleep(10)
            await self.channel.delete()
    
    async def start_match(self, interaction):
        if self.mode == "1v1":
            team1 = [self.players[0]]
            team2 = [self.players[1]]
        else:
            team1, team2 = await self.bot.mmr_system.balance_teams(self.players, "rl")
        
        embed = discord.Embed(
            title=f"Rocket League {self.mode.upper()} Match #{self.queue_number}",
            color=discord.Color.gold()
        )
        
        team1_list = '\n'.join([f"<@{player}>" for player in team1])
        team2_list = '\n'.join([f"<@{player}>" for player in team2])
        
        embed.add_field(name="Team 1", value=team1_list, inline=True)
        embed.add_field(name="Team 2", value=team2_list, inline=True)
        
        await interaction.followup.send(embed=embed)
        
        vote_view = RLWinnerVoteView(self.bot, team1, team2, self.channel, self.queue_number, self.mode)
        
        if self.mode == "3v3":
            votes_needed = 4
        elif self.mode == "2v2":
            votes_needed = 3
        else:
            votes_needed = 2
        
        vote_embed = discord.Embed(
            title="Vote for Winner",
            description=f"{votes_needed} votes needed to determine the winner",
            color=discord.Color.red()
        )
        vote_embed.add_field(name="Team 1 Votes", value=f"0/{votes_needed}", inline=True)
        vote_embed.add_field(name="Team 2 Votes", value=f"0/{votes_needed}", inline=True)
        
        vote_message = await self.channel.send(embed=vote_embed, view=vote_view)
        vote_view.message = vote_message

class RLWinnerVoteView(discord.ui.View):
    def __init__(self, bot, team1, team2, channel, queue_number, mode, message=None):
        super().__init__(timeout=1800)
        self.bot = bot
        self.team1 = team1
        self.team2 = team2
        self.channel = channel
        self.queue_number = queue_number
        self.mode = mode
        self.team1_votes = []
        self.team2_votes = []
        self.message = message
        
        if mode == "3v3":
            self.votes_needed = 4
        elif mode == "2v2":
            self.votes_needed = 3
        else:
            self.votes_needed = 2
    
    @discord.ui.button(label="Team 1 Wins", style=discord.ButtonStyle.green, custom_id="rl_team1_wins")
    async def team1_wins(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.team1_votes or interaction.user.id in self.team2_votes:
            await interaction.response.send_message("You have already voted!", ephemeral=True)
            return
        
        self.team1_votes.append(interaction.user.id)
        await interaction.response.send_message("Voted for Team 1!", ephemeral=True)
        
        embed = discord.Embed(
            title="Vote for Winner",
            description=f"{self.votes_needed} votes needed to determine the winner",
            color=discord.Color.red()
        )
        embed.add_field(name="Team 1 Votes", value=f"{len(self.team1_votes)}/{self.votes_needed}", inline=True)
        embed.add_field(name="Team 2 Votes", value=f"{len(self.team2_votes)}/{self.votes_needed}", inline=True)
        
        if self.message:
            await self.message.edit(embed=embed, view=self)
        
        if len(self.team1_votes) >= self.votes_needed:
            await self.finish_match(1)
    
    @discord.ui.button(label="Team 2 Wins", style=discord.ButtonStyle.green, custom_id="rl_team2_wins")
    async def team2_wins(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.team1_votes or interaction.user.id in self.team2_votes:
            await interaction.response.send_message("You have already voted!", ephemeral=True)
            return
        
        self.team2_votes.append(interaction.user.id)
        await interaction.response.send_message("Voted for Team 2!", ephemeral=True)
        
        embed = discord.Embed(
            title="Vote for Winner",
            description=f"{self.votes_needed} votes needed to determine the winner",
            color=discord.Color.red()
        )
        embed.add_field(name="Team 1 Votes", value=f"{len(self.team1_votes)}/{self.votes_needed}", inline=True)
        embed.add_field(name="Team 2 Votes", value=f"{len(self.team2_votes)}/{self.votes_needed}", inline=True)
        
        if self.message:
            await self.message.edit(embed=embed, view=self)
        
        if len(self.team2_votes) >= self.votes_needed:
            await self.finish_match(2)
    
    async def finish_match(self, winning_team):
        mmr_changes = await self.bot.mmr_system.calculate_team_mmr_changes(
            self.team1, self.team2, winning_team, "rl"
        )
        
        await self.bot.mmr_system.apply_mmr_changes(mmr_changes, "rl")
        
        for player in self.team1:
            await self.bot.db.update_player_stats(player, "rl", winning_team == 1)
        
        for player in self.team2:
            await self.bot.db.update_player_stats(player, "rl", winning_team == 2)
        
        await self.bot.db.save_match(
            "rl", self.queue_number, self.team1, self.team2, winning_team, mmr_changes
        )
        
        embed = discord.Embed(
            title=f"Rocket League {self.mode.upper()} Match #{self.queue_number} Results",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="Winner",
            value=f"Team {winning_team}",
            inline=False
        )
        
        team1_mmr_text = []
        for player in self.team1:
            change = mmr_changes[player]
            team1_mmr_text.append(f"<@{player}>: {'+' if change >= 0 else ''}{change}")
        
        team2_mmr_text = []
        for player in self.team2:
            change = mmr_changes[player]
            team2_mmr_text.append(f"<@{player}>: {'+' if change >= 0 else ''}{change}")
        
        embed.add_field(
            name="Team 1 MMR Changes",
            value='\n'.join(team1_mmr_text),
            inline=True
        )
        
        embed.add_field(
            name="Team 2 MMR Changes",
            value='\n'.join(team2_mmr_text),
            inline=True
        )
        
        await self.channel.send(embed=embed)
        
        await asyncio.sleep(30)
        await self.channel.delete()

class RocketLeagueQueue(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue_3v3 = []
        self.queue_2v2 = []
        self.queue_1v1 = []
        self.CATEGORY_ID = 1435576716532908114
    
    @app_commands.command(name="rocketleague-queue", description="Join a Rocket League queue")
    @app_commands.describe(type="Choose the game mode")
    async def rl_queue(self, interaction: discord.Interaction, type: Literal["3v3", "2v2", "1v1"]):
        if type == "3v3":
            if interaction.user.id in self.queue_3v3:
                await interaction.response.send_message("You are already in the 3v3 queue!", ephemeral=True)
                return
            
            self.queue_3v3.append(interaction.user.id)
            
            await interaction.response.send_message(
                f"You have joined the Rocket League 3v3 queue! ({len(self.queue_3v3)}/6)",
                ephemeral=True
            )
            
            if len(self.queue_3v3) >= 6:
                await self.start_match(interaction.guild, "3v3")
        
        elif type == "2v2":
            if interaction.user.id in self.queue_2v2:
                await interaction.response.send_message("You are already in the 2v2 queue!", ephemeral=True)
                return
            
            self.queue_2v2.append(interaction.user.id)
            
            await interaction.response.send_message(
                f"You have joined the Rocket League 2v2 queue! ({len(self.queue_2v2)}/4)",
                ephemeral=True
            )
            
            if len(self.queue_2v2) >= 4:
                await self.start_match(interaction.guild, "2v2")
        
        else:
            if interaction.user.id in self.queue_1v1:
                await interaction.response.send_message("You are already in the 1v1 queue!", ephemeral=True)
                return
            
            self.queue_1v1.append(interaction.user.id)
            
            await interaction.response.send_message(
                f"You have joined the Rocket League 1v1 queue! ({len(self.queue_1v1)}/2)",
                ephemeral=True
            )
            
            if len(self.queue_1v1) >= 2:
                await self.start_match(interaction.guild, "1v1")
    
    async def start_match(self, guild, mode):
        if mode == "3v3":
            players = self.queue_3v3[:6]
            self.queue_3v3 = self.queue_3v3[6:]
            pool = self.queue_3v3
        elif mode == "2v2":
            players = self.queue_2v2[:4]
            self.queue_2v2 = self.queue_2v2[4:]
            pool = self.queue_2v2
        else:
            players = self.queue_1v1[:2]
            self.queue_1v1 = self.queue_1v1[2:]
            pool = self.queue_1v1
        
        category = guild.get_channel(self.CATEGORY_ID)
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
        }
        
        for user_id in players:
            user = guild.get_member(user_id)
            if user:
                overwrites[user] = discord.PermissionOverwrite(read_messages=True)
        
        channel_name = f"rl-{self.bot.rl_counter:04d}"
        self.bot.rl_counter += 1
        
        match_channel = await guild.create_text_channel(
            channel_name,
            category=category,
            overwrites=overwrites
        )
        
        for user_id in players:
            user = guild.get_member(user_id)
            if user:
                try:
                    dm_embed = discord.Embed(
                        title=f"Rocket League {mode.upper()} Match Ready!",
                        description=f"Your Rocket League match is ready in {match_channel.mention}",
                        color=discord.Color.green()
                    )
                    await user.send(embed=dm_embed)
                except:
                    pass
        
        mentions = " ".join([f"<@{user_id}>" for user_id in players])
        await match_channel.send(f"{mentions}")
        
        ready_view = RLReadyUpView(self.bot, players.copy(), match_channel, self.bot.rl_counter - 1, pool, mode)
        ready_list = '\n'.join([f"<@{player_id}> ⏳" for player_id in players])
        embed = discord.Embed(
            title=f"0/{len(players)} readied up",
            description=f"**Not Ready:**\n{ready_list}",
            color=discord.Color.orange()
        )
        embed.set_footer(text="Time remaining: 4m 0s")
        
        ready_message = await match_channel.send(embed=embed, view=ready_view)
        ready_view.message = ready_message

async def setup(bot):
    await bot.add_cog(RocketLeagueQueue(bot))