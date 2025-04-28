# summarizer_bot.py
import os
import discord
import aiohttp
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
#print(TOKEN)
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK")

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} commands")
    print(f"Logged in as {bot.user}!")
    

@bot.tree.command(name="tldr")
async def summarize(interaction: discord.Interaction, limit: int = 75):
    """Summarize last N messages in this DM group"""
    await interaction.response.defer(thinking=True)

    msgs = []
    async for message in interaction.channel.history(limit=limit*2, oldest_first=False):
        #only pick real user messages
        if not message.author.bot and message.content.strip():
            msgs.append({
                "id": str(message.id),
                "author": message.author.display_name,
                "content": message.clean_content,
                "timestamp": str(message.created_at)
            })
    
    msgs.reverse()

    payload = {
        "channel_id": str(interaction.channel.id),
        "limit": limit,
        "msgs": msgs
    }


    # POST to n8n webhook
    async with aiohttp.ClientSession() as session:
        async with session.post(N8N_WEBHOOK_URL, json=payload) as resp:
            summary = (await resp.text()).strip()
    
    if not summary:
        summary = "No messages to summarize"

    # Send the response back in chat
    # Discord limit is 2000 chars 
    await interaction.followup.send(content=summary[:1990])

bot.run(TOKEN)