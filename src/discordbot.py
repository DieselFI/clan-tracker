import os
import discord
import json

from pprint import pformat
import redis
from tabulate import tabulate
import playertracker

intents = discord.Intents.all()
intents.message_content = True
# Set up your discord bot token 'export DISCORD_BOT_TOKEN="blabla"'
TOKEN = os.getenv('DISCORD_BOT_TOKEN') or ""
if TOKEN == "":
   print("Warning: No DISCORD_TOKEN environment variable set.")
#Create a client instance
client = discord.Client(intents=intents)

# Create a leaderboard class
class LeaderboardView(discord.ui.View):
    def __init__(self, data):
        super().__init__()

        self.leaderboard = data
        self.page = 0
        self.page_size = 25
        self.timeout = None

    @discord.ui.button(style=discord.ButtonStyle.gray, label="<<")
    async def first_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = 0
        await self.update_leaderboard(interaction)

    @discord.ui.button(style=discord.ButtonStyle.gray, label="<")
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
        await self.update_leaderboard(interaction)

    @discord.ui.button(style=discord.ButtonStyle.gray, label=">")
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        total_pages = len(self.leaderboard) // self.page_size + 1
        if self.page < total_pages - 1:
            self.page += 1
        await self.update_leaderboard(interaction)

    @discord.ui.button(style=discord.ButtonStyle.gray, label=">>")
    async def last_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        total_pages = len(self.leaderboard) // self.page_size + 1
        self.page = total_pages - 1
        await self.update_leaderboard(interaction)

    async def update_leaderboard(self, interaction):
        offset = self.page * self.page_size
        await interaction.response.edit_message(content="```{}```".format(tabulate(self.leaderboard[offset:offset + self.page_size], headers=["#", "RSN", "Rank", "Points", "EHB + EHP"])), view=self)

@client.event
async def on_message(message):
  msg = message.content

  if message.author == client.user:
    return

  if msg == "!leaderboard":
    rankings = playertracker.compute_ranks(r)
    leaderboard = playertracker.compute_leaderboard(rankings, r)

    view = LeaderboardView(leaderboard)
    body = tabulate(leaderboard[0:25], headers=["#", "RSN", "Rank", "Points", "EHB + EHP"])
    view.message = await message.author.send(content="```{}```".format(body), view=view)

  if msg.startswith("!rank"):
    rsn = msg.split(" ", 1)[1]

    p = json.loads(r.get(rsn.lower()))

    #send message back
    message = await message.author.send(content="{} has the following data tracked...\n```{}```".format(rsn, pformat(p)))
  
  if msg.startswith("!update"):
    rsn = msg.split(" ", 1)[1]

    playertracker.track_players(r, rsn)

    await update_leaderboard()


@client.event
async def on_ready():
   await update_leaderboard()

async def update_leaderboard():
    # Set up your discord channel id 'export DISCORD_CHANNEL_ID="123"'
    channel_id = int(os.getenv('DISCORD_CHANNEL_ID')) or 0
    if channel == 0:
        print("Warning: No DISCORD_CHANNEL_ID environment variable set. Defaulting to 0.")
    channel = client.get_channel(channel_id)

    rankings = playertracker.compute_ranks(r)
    leaderboard = playertracker.compute_leaderboard(rankings, r)

    view = LeaderboardView(leaderboard)
    body = tabulate(leaderboard[0:25], headers=["#", "RSN", "Rank", "Points", "EHB + EHP"])

    # Set up your discord message id 'export DISCORD_MESSAGE_ID="123"'
    message_id = int(os.getenv('DISCORD_MESSAGE_ID')) or 0
    if message_id == 0:
        print("Warning: No DISCORD_MESSAGE_ID environment variable set. Defaulting to 0.")
    msg = await channel.fetch_message(message_id)
    await msg.edit(content="```{}```".format(body), view=view)

# Run the client
pool = redis.ConnectionPool(host="localhost", port=6379, db=0)
r = redis.Redis(connection_pool=pool)

client.run(TOKEN)
