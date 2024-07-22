#https://discord.com/oauth2/authorize?client_id=1264744396365238365&permissions=67648&integration_type=0&scope=bot
import discord, requests, re, os
from dotenv import load_dotenv

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True


client = discord.Client(intents=intents)

load_dotenv()

token = os.getenv('DISC_TOKEN')

validLinks = ["https://music.apple.com/","https://open.spotify.com/"]

def findLink(message: discord.message) -> [str]:
    links = []
    for validLink in validLinks:
        if validLink in message.content:
            spliced = message.content.split()
            for item in spliced:
                if item.startswith(validLink):
                    links.append(item)
    return links
def worthySearch(message:discord.Message) -> bool:
    for link in validLinks:
        if link in message.content:
            return True
@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')



@client.event
async def on_message(message):
    if message.author == client.user:
        return
    links = findLink(message)
    if len(links) != 0:
        print(f"{len(links)} link(s) detected")
        await message.add_reaction("🔗")

@client.event
async def on_reaction_add(reaction, user):
    if reaction.emoji == "🔗" and user != client.user:
        if worthySearch(reaction.message):
            links = findLink(reaction.message)
            print(f"{len(links)}")


client.run(token)