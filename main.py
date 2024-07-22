#https://discord.com/oauth2/authorize?client_id=1264744396365238365&permissions=67648&integration_type=0&scope=bot
import discord, requests, os
from dotenv import load_dotenv
from colorthief import ColorThief


import urllib.request

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True


client = discord.Client(intents=intents)

load_dotenv()

token = os.getenv('DISC_TOKEN')

validLinks = ["https://music.apple.com/","https://open.spotify.com/", "https://music.youtube.com/","https://www.youtube.com/"]
preferedOutputPlatforms = ["spotify", "appleMusic", "youtubeMusic"]

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

def findURLS(link) -> {str:str}:
    songURLs = {}
    response = requests.get("https://api.song.link/v1-alpha.1/links?url=" + link)
    if response.ok:
        response = response.json()
        for platform in response["linksByPlatform"]:
            #Implement filtering by server preference
            if platform in preferedOutputPlatforms:
                songURLs[platform] = response["linksByPlatform"][platform]["url"]

        for thumnailProvier in response["entitiesByUniqueId"]:
            songURLs["thumbnailURL"] = response["entitiesByUniqueId"][thumnailProvier]["thumbnailUrl"]
            break
        return songURLs

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    links = findLink(message)
    if len(links) != 0:
        await message.add_reaction("🔗")

@client.event
async def on_reaction_add(reaction, user):
    if reaction.emoji == "🔗" and user != client.user:
        if worthySearch(reaction.message):
            async with reaction.message.channel.typing():
                links = findLink(reaction.message)
                print(f"{len(links)}")
                embeds = []
                for link in links:
                    urls = findURLS(link)
                    urllib.request.urlretrieve(urls["thumbnailURL"], "thumbnail.png")
                    recColor = ColorThief('thumbnail.png').get_color(quality=1)
                    print(recColor)
                    embed = discord.Embed(color= discord.Color.from_rgb(recColor[0],recColor[1],recColor[2]), title= "Music Links", footer= discord.EmbedFooter(text = "Powered by Songlink"))
                    desc = ""
                    for platform in urls:
                        if platform == "thumbnailURL":
                            continue
                        platformFormatted = ""
                        for char in platform:
                            if char.isupper():
                                platformFormatted += " "
                                platformFormatted += char.swapcase()
                            else:
                                platformFormatted += char
                        platformFormatted = platformFormatted.title()

                        desc += f"## [{platformFormatted}]({urls[platform]})\n"
                    embed.description = desc
                    embeds.append(embed)
                    embed.set_thumbnail(url=urls["thumbnailURL"])
            await reaction.message.reply(embeds = embeds)


client.run(token)