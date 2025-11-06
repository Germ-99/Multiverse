import discord
from discord.ext import commands
from discord import app_commands
from typing import List

class LeavePartyConfirmView(discord.ui.View):
    def __init__(self, bot, party_name, captain_id):
        super().__init__(timeout=60)
        self.bot = bot
        self.party_name = party_name
        self.captain_id = captain_id
        self.value = None
    
    @discord.ui.button(label="Yes", style=discord.ButtonStyle.red)
    async def confirm_leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.bot.db.delete_party(self.party_name, self.captain_id)
        
        embed = discord.Embed(
            title="Party Deleted",
            description=f"Party **{self.party_name}** has been deleted.",
            color=discord.Color.red()
        )
        
        await interaction.response.edit_message(embed=embed, view=None)
        self.value = True
        self.stop()
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.gray)
    async def cancel_leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="Cancelled",
            description="You remain in the party.",
            color=discord.Color.blue()
        )
        
        await interaction.response.edit_message(embed=embed, view=None)
        self.value = False
        self.stop()

class Parties(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="party-create", description="Create a new party")
    @app_commands.describe(name="Name of the party (max 20 characters)")
    async def party_create(self, interaction: discord.Interaction, name: str):
        if len(name) > 20:
            await interaction.response.send_message("Party name cannot exceed 20 characters!", ephemeral=True)
            return
        
        existing_parties = await self.bot.db.get_created_parties(interaction.user.id)
        
        if name in existing_parties:
            await interaction.response.send_message(f"You already have a party named **{name}**!", ephemeral=True)
            return
        
        await self.bot.db.create_party(name, interaction.user.id)
        
        embed = discord.Embed(
            title="Party Created",
            description=f"Successfully created party **{name}**!\nYou are the captain.",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="party-invite", description="Invite a user to your party")
    @app_commands.describe(
        user="User to invite",
        party_name="Party to invite them to"
    )
    async def party_invite(self, interaction: discord.Interaction, user: discord.Member, party_name: str):
        created_parties = await self.bot.db.get_created_parties(interaction.user.id)
        
        if party_name not in created_parties:
            await interaction.response.send_message("You don't have a party with that name!", ephemeral=True)
            return
        
        if user.id == interaction.user.id:
            await interaction.response.send_message("You cannot invite yourself!", ephemeral=True)
            return
        
        party_count = await self.bot.db.get_party_count(party_name, interaction.user.id)
        
        if party_count >= 2:
            await interaction.response.send_message("This party is full! (Max 2 people)", ephemeral=True)
            return
        
        party_members = await self.bot.db.get_party_members(party_name, interaction.user.id)
        
        if user.id in party_members:
            await interaction.response.send_message(f"{user.mention} is already in this party!", ephemeral=True)
            return
        
        await self.bot.db.add_party_member(party_name, interaction.user.id, user.id)
        
        embed = discord.Embed(
            title="User Invited",
            description=f"{user.mention} has been added to party **{party_name}**!",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        try:
            dm_embed = discord.Embed(
                title="Party Invitation",
                description=f"You have been added to party **{party_name}** by {interaction.user.mention}!",
                color=discord.Color.blue()
            )
            await user.send(embed=dm_embed)
        except:
            pass
    
    @app_commands.command(name="party-leave", description="Leave a party")
    @app_commands.describe(name="Party to leave")
    async def party_leave(self, interaction: discord.Interaction, name: str):
        user_parties = await self.bot.db.get_user_parties(interaction.user.id)
        
        party_found = False
        captain_id = None
        
        for party_name, cap_id in user_parties:
            if party_name == name:
                party_found = True
                captain_id = cap_id
                break
        
        if not party_found:
            await interaction.response.send_message("You are not in a party with that name!", ephemeral=True)
            return
        
        is_captain = await self.bot.db.is_party_captain(name, interaction.user.id)
        
        if is_captain:
            embed = discord.Embed(
                title="Confirm Party Deletion",
                description="You created this party. Leaving it will delete the party and remove all people from it. Are you sure you want to leave?",
                color=discord.Color.orange()
            )
            
            view = LeavePartyConfirmView(self.bot, name, interaction.user.id)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        else:
            await self.bot.db.remove_party_member(name, captain_id, interaction.user.id)
            
            embed = discord.Embed(
                title="Left Party",
                description=f"You have left party **{name}**.",
                color=discord.Color.green()
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="party-list", description="View members in a party")
    @app_commands.describe(name="Party to view")
    async def party_list(self, interaction: discord.Interaction, name: str):
        user_parties = await self.bot.db.get_user_parties(interaction.user.id)
        
        party_found = False
        captain_id = None
        
        for party_name, cap_id in user_parties:
            if party_name == name:
                party_found = True
                captain_id = cap_id
                break
        
        if not party_found:
            await interaction.response.send_message("You are not in a party with that name!", ephemeral=True)
            return
        
        members = await self.bot.db.get_party_members(name, captain_id)
        
        embed = discord.Embed(
            title=f"Party: {name}",
            color=discord.Color.blue()
        )
        
        member_list = []
        for member_id in members:
            user = self.bot.get_user(member_id)
            if user:
                if member_id == captain_id:
                    member_list.append(f"👑 {user.mention} (Captain)")
                else:
                    member_list.append(f"{user.mention}")
        
        embed.description = '\n'.join(member_list) if member_list else "No members found"
        embed.set_footer(text=f"{len(members)}/2 members")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @party_invite.autocomplete('party_name')
    async def party_invite_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        parties = await self.bot.db.get_created_parties(interaction.user.id)
        return [
            app_commands.Choice(name=party, value=party)
            for party in parties if current.lower() in party.lower()
        ][:25]
    
    @party_leave.autocomplete('name')
    async def party_leave_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        user_parties = await self.bot.db.get_user_parties(interaction.user.id)
        party_names = [party[0] for party in user_parties]
        return [
            app_commands.Choice(name=party, value=party)
            for party in party_names if current.lower() in party.lower()
        ][:25]
    
    @party_list.autocomplete('name')
    async def party_list_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        user_parties = await self.bot.db.get_user_parties(interaction.user.id)
        party_names = [party[0] for party in user_parties]
        return [
            app_commands.Choice(name=party, value=party)
            for party in party_names if current.lower() in party.lower()
        ][:25]

async def setup(bot):
    await bot.add_cog(Parties(bot))