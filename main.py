#https://discord.com/oauth2/authorize?client_id=1264744396365238365&permissions=67648&integration_type=0&scope=bot
import discord, requests, os
from dotenv import load_dotenv
from colorthief import ColorThief


import urllib.request

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True


bot = discord.Bot(intents=intents)

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

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    links = findLink(message)
    if len(links) != 0:
        await message.add_reaction("🔗")

@bot.event
async def on_reaction_add(reaction, user):
    if reaction.emoji == "🔗" and user != bot.user:
        if worthySearch(reaction.message):
            async with reaction.message.channel.typing():
                links = findLink(reaction.message)
                embeds = []
                for link in links:
                    urls = findURLS(link)
                    urllib.request.urlretrieve(urls["thumbnailURL"], "thumbnail.png")
                    recColor = ColorThief('thumbnail.png').get_color(quality=1)
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
class ManagePlatformsView(discord.ui.View):
    @discord.ui.select( # the decorator that lets you specify the properties of the select menu
        placeholder = "Select a platform!",
        min_values = 1, # the minimum number of values that must be selected by the users
        max_values = 7, # the maximum number of values that can be selected by the users
        options = [ # the list of options from which users can choose, a required field
            discord.SelectOption(
                label="Spotify",
            ),
            discord.SelectOption(
                label="Apple Music",
            ),
            discord.SelectOption(
                label="Youtube Music",
            ),
            discord.SelectOption(
                label="Amazon Music",
            ),
            discord.SelectOption(
                label="Tidal",
            ),
            discord.SelectOption(
                label="SoundCloud",
            ),
            discord.SelectOption(
                label="Pandora",
            )
        ]
    )
    async def select_callback(self, select, interaction): # the function called when the user is done selecting options
        await interaction.response.send_message(f"got it boss👍 {select.values}", ephemeral=True)
@bot.slash_command(name="manage_platforms", guild_ids= [585594090863853588])
async def manage_platforms(ctx):
    modal = ManagePlatformsView()
    await ctx.respond("Select which platforms to both detect links from, and suggest links for",view=modal, ephemeral=True)
@bot.slash_command(name="ignore_channel", guild_ids= [585594090863853588])
async def manage_platforms(ctx):
    await ctx.respond(f"Will now ignored links sent in {ctx.channel.id}", ephemeral=True)
@bot.slash_command(name="allow_channel", guild_ids= [585594090863853588])
async def manage_platforms(ctx):
    await ctx.respond(f"Will now allow links sent in {ctx.channel.id}", ephemeral=True)
bot.run(token)