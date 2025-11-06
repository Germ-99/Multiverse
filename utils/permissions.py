import discord

ADMIN_ROLES = [1268967648381636827, 1268967648369184835, 1268967648381636822]

def has_admin_role(member):
    if not isinstance(member, discord.Member):
        return False
    return any(role.id in ADMIN_ROLES for role in member.roles)

def check_admin_permissions(interaction):
    return has_admin_role(interaction.user)