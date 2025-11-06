import discord
from discord.ext import commands
from discord import app_commands
import asyncio

class ValorantReadyUpView(discord.ui.View):
    def __init__(self, bot, players, channel, queue_number, pool, message):
        super().__init__(timeout=240)
        self.bot = bot
        self.players = players
        self.channel = channel
        self.queue_number = queue_number
        self.ready_players = []
        self.pool = pool
        self.message = message
        self.countdown_task = None
    
    async def start_countdown(self):
        for remaining in range(240, 0, -1):
            if len(self.ready_players) == 10:
                return
            
            minutes = remaining // 60
            seconds = remaining % 60
            
            ready_list = '\n'.join([f"<@{player_id}> ✅" for player_id in self.ready_players])
            unready_list = '\n'.join([f"<@{player_id}> ⏳" for player_id in self.players if player_id not in self.ready_players])
            
            embed = discord.Embed(
                title=f"{len(self.ready_players)}/10 readied up",
                description=f"**Ready:**\n{ready_list}\n\n**Not Ready:**\n{unready_list}" if ready_list and unready_list else (f"**Ready:**\n{ready_list}" if ready_list else f"**Not Ready:**\n{unready_list}"),
                color=discord.Color.orange()
            )
            embed.set_footer(text=f"Time remaining: {minutes:02d}:{seconds:02d}")
            
            try:
                await self.message.edit(embed=embed, view=self)
            except:
                pass
            
            await asyncio.sleep(1)
    
    @discord.ui.button(label="Ready Up", style=discord.ButtonStyle.green, custom_id="valorant_ready_up")
    async def ready_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in self.players:
            await interaction.response.send_message("You are not in this match!", ephemeral=True)
            return
        
        if interaction.user.id in self.ready_players:
            await interaction.response.send_message("You are already readied up!", ephemeral=True)
            return
        
        self.ready_players.append(interaction.user.id)
        
        await interaction.response.defer()
        
        if len(self.ready_players) == 10:
            if self.countdown_task:
                self.countdown_task.cancel()
            await self.start_match()
    
    async def on_timeout(self):
        unready_players = [player for player in self.players if player not in self.ready_players]
        
        if len(self.pool) >= len(unready_players):
            substitutes = self.pool[:len(unready_players)]
            for player_id in substitutes:
                self.pool.remove(player_id)
            
            for i, player_id in enumerate(unready_players):
                current_mmr = await self.bot.db.get_player_mmr(player_id, "valorant")
                await self.bot.db.update_player_mmr(player_id, "valorant", current_mmr - 80, "Failed to ready up")
                
                self.players.remove(player_id)
                self.players.append(substitutes[i])
                
                member = self.channel.guild.get_member(player_id)
                if member:
                    await self.channel.set_permissions(member, read_messages=False)
                
                sub_member = self.channel.guild.get_member(substitutes[i])
                if sub_member:
                    await self.channel.set_permissions(sub_member, read_messages=True)
            
            unready_mentions = ', '.join([f'<@{p}>' for p in unready_players])
            sub_mentions = ', '.join([f'<@{p}>' for p in substitutes])
            
            embed = discord.Embed(
                title="Players Substituted",
                description=f"**Removed (-80 MMR):** {unready_mentions}\n**Added:** {sub_mentions}",
                color=discord.Color.yellow()
            )
            await self.channel.send(embed=embed)
            
            mentions = " ".join([f"<@{user_id}>" for user_id in substitutes])
            await self.channel.send(f"{mentions}")
            
            ready_view = ValorantReadyUpView(self.bot, self.players, self.channel, self.queue_number, self.pool, None)
            ready_list = '\n'.join([f"<@{player_id}> ⏳" for player_id in self.players])
            embed = discord.Embed(
                title="0/10 readied up",
                description=f"**Not Ready:**\n{ready_list}",
                color=discord.Color.orange()
            )
            embed.set_footer(text="Time remaining: 04:00")
            new_message = await self.channel.send(embed=embed, view=ready_view)
            ready_view.message = new_message
            ready_view.countdown_task = asyncio.create_task(ready_view.start_countdown())
        else:
            for player_id in unready_players:
                current_mmr = await self.bot.db.get_player_mmr(player_id, "valorant")
                await self.bot.db.update_player_mmr(player_id, "valorant", current_mmr - 80, "Failed to ready up")
            
            unready_mentions = ', '.join([f'<@{player}>' for player in unready_players])
            
            try:
                await self.message.edit(view=None)
            except:
                pass
            
            embed = discord.Embed(
                title="Not All Players Ready",
                description=f"Not all players readied up. Canceling queue in 10 seconds.\n\n**Players who didn't ready (-80 MMR):**\n{unready_mentions}",
                color=discord.Color.red()
            )
            await self.channel.send(embed=embed)
            
            await asyncio.sleep(10)
            await self.channel.delete()
    
    async def start_match(self):
        team1, team2 = await self.bot.mmr_system.balance_teams(self.players, "valorant")
        
        embed = discord.Embed(
            title=f"Valorant Match #{self.queue_number}",
            color=discord.Color.gold()
        )
        
        team1_list = '\n'.join([f"<@{player}>" for player in team1])
        team2_list = '\n'.join([f"<@{player}>" for player in team2])
        
        embed.add_field(name="Team 1", value=team1_list, inline=True)
        embed.add_field(name="Team 2", value=team2_list, inline=True)
        
        await self.channel.send(embed=embed)
        
        vote_view = ValorantWinnerVoteView(self.bot, team1, team2, self.channel, self.queue_number)
        vote_embed = discord.Embed(
            title="Vote for Winner",
            description="6 votes needed to determine the winner",
            color=discord.Color.red()
        )
        vote_embed.add_field(name="Team 1 Votes", value="0", inline=True)
        vote_embed.add_field(name="Team 2 Votes", value="0", inline=True)
        
        vote_message = await self.channel.send(embed=vote_embed, view=vote_view)
        vote_view.message = vote_message

class ValorantWinnerVoteView(discord.ui.View):
    def __init__(self, bot, team1, team2, channel, queue_number):
        super().__init__(timeout=1800)
        self.bot = bot
        self.team1 = team1
        self.team2 = team2
        self.channel = channel
        self.queue_number = queue_number
        self.team1_votes = []
        self.team2_votes = []
        self.message = None
    
    async def update_vote_display(self):
        embed = discord.Embed(
            title="Vote for Winner",
            description="6 votes needed to determine the winner",
            color=discord.Color.red()
        )
        embed.add_field(name="Team 1 Votes", value=str(len(self.team1_votes)), inline=True)
        embed.add_field(name="Team 2 Votes", value=str(len(self.team2_votes)), inline=True)
        
        try:
            await self.message.edit(embed=embed, view=self)
        except:
            pass
    
    @discord.ui.button(label="Team 1 Wins", style=discord.ButtonStyle.green, custom_id="valorant_team1_wins")
    async def team1_wins(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.team1_votes or interaction.user.id in self.team2_votes:
            await interaction.response.send_message("You have already voted!", ephemeral=True)
            return
        
        self.team1_votes.append(interaction.user.id)
        await interaction.response.send_message("Voted for Team 1!", ephemeral=True)
        
        await self.update_vote_display()
        
        if len(self.team1_votes) >= 6:
            await self.finish_match(1)
    
    @discord.ui.button(label="Team 2 Wins", style=discord.ButtonStyle.green, custom_id="valorant_team2_wins")
    async def team2_wins(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.team1_votes or interaction.user.id in self.team2_votes:
            await interaction.response.send_message("You have already voted!", ephemeral=True)
            return
        
        self.team2_votes.append(interaction.user.id)
        await interaction.response.send_message("Voted for Team 2!", ephemeral=True)
        
        await self.update_vote_display()
        
        if len(self.team2_votes) >= 6:
            await self.finish_match(2)
    
    async def finish_match(self, winning_team):
        mmr_changes = await self.bot.mmr_system.calculate_team_mmr_changes(
            self.team1, self.team2, winning_team, "valorant"
        )
        
        await self.bot.mmr_system.apply_mmr_changes(mmr_changes, "valorant")
        
        for player in self.team1:
            await self.bot.db.update_player_stats(player, "valorant", winning_team == 1)
        
        for player in self.team2:
            await self.bot.db.update_player_stats(player, "valorant", winning_team == 2)
        
        await self.bot.db.save_match(
            "valorant", self.queue_number, self.team1, self.team2, winning_team, mmr_changes
        )
        
        embed = discord.Embed(
            title=f"Valorant Match #{self.queue_number} Results",
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

class ValorantQueue(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue_pool = []
        self.CATEGORY_ID = 1435934861214093393
    
    @app_commands.command(name="valorant-queue", description="Join the Valorant 5v5 queue")
    async def valorant_queue(self, interaction: discord.Interaction):
        if interaction.user.id in self.queue_pool:
            await interaction.response.send_message("You are already in the Valorant queue!", ephemeral=True)
            return
        
        self.queue_pool.append(interaction.user.id)
        
        await interaction.response.send_message(
            f"You have joined the Valorant queue! ({len(self.queue_pool)}/10)",
            ephemeral=True
        )
        
        if len(self.queue_pool) >= 10:
            await self.start_match(interaction.guild)
    
    async def start_match(self, guild):
        players = self.queue_pool[:10]
        self.queue_pool = self.queue_pool[10:]
        
        category = guild.get_channel(self.CATEGORY_ID)
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
        }
        
        for user_id in players:
            user = guild.get_member(user_id)
            if user:
                overwrites[user] = discord.PermissionOverwrite(read_messages=True)
        
        channel_name = f"valorant-{self.bot.valorant_counter:04d}"
        self.bot.valorant_counter += 1
        
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
                        title="Valorant Match Ready!",
                        description=f"Your Valorant match is ready in {match_channel.mention}",
                        color=discord.Color.green()
                    )
                    await user.send(embed=dm_embed)
                except:
                    pass
        
        mentions = " ".join([f"<@{user_id}>" for user_id in players])
        await match_channel.send(f"{mentions}")
        
        ready_view = ValorantReadyUpView(self.bot, players.copy(), match_channel, self.bot.valorant_counter - 1, self.queue_pool, None)
        ready_list = '\n'.join([f"<@{player_id}> ⏳" for player_id in players])
        embed = discord.Embed(
            title="0/10 readied up",
            description=f"**Not Ready:**\n{ready_list}",
            color=discord.Color.orange()
        )
        embed.set_footer(text="Time remaining: 04:00")
        
        message = await match_channel.send(embed=embed, view=ready_view)
        ready_view.message = message
        ready_view.countdown_task = asyncio.create_task(ready_view.start_countdown())

async def setup(bot):
    await bot.add_cog(ValorantQueue(bot))