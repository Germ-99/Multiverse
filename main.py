import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv
from database.database import DatabaseManager
from utils.mmr_system import MMRSystem

load_dotenv()

class Multiverse(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(command_prefix='!', intents=intents)
        
        self.db = DatabaseManager()
        self.mmr_system = MMRSystem(self.db)
        self.r6_counter = 1
        self.rl_counter = 1
        self.valorant_counter = 1
        self.breachers_counter = 1
        
    async def setup_hook(self):
        await self.db.initialize()
        
        await self.load_extension('cogs.r6_queue')
        await self.load_extension('cogs.rocketleague_queue')
        await self.load_extension('cogs.valorant_queue')
        await self.load_extension('cogs.breachers_queue')
        await self.load_extension('cogs.parties')
        await self.load_extension('cogs.admin')
        
        await self.tree.sync()
        print(f"Synced commands for {self.user}")
    
    async def on_ready(self):
        print(f'{self.user} has logged in!')

    async def on_message(self, message):
        if message.author.bot:
            return

        if message.channel.id == 1436097772372758668:
            await message.delete()
            return

        if "how do i queue" in message.content.lower():
            await message.reply("For information on how to queue, please refer to [this message](https://discord.com/channels/1268967648352538624/1436097772372758668/1436098741575880754)!")

        await self.process_commands(message)

bot = Multiverse()

if __name__ == "__main__":
    bot.run(os.getenv("TOKEN"))