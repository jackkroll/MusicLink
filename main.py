#https://discord.com/oauth2/authorize?client_id=1264744396365238365&permissions=67648&integration_type=0&scope=bot
import discord, requests, os, json
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
defaultPlatforms = ["spotify", "appleMusic", "youtubeMusic"]
thumbnailPreferences = ["appleMusic", "spotify"]


def findLink(message: discord.message) -> [str]:
    links = []
    for validLink in validLinks:
        if validLink in message.content:
            spliced = message.content.split()
            for item in spliced:
                if item.startswith(validLink):
                    links.append(item)
    return links
def worthySearch(message:discord.Message) -> bool :
    for link in validLinks:
        if link in message.content:
            return True

def findURLS(link: str, mesage: discord.Message) -> dict | None:
    songURLs = {}
    response = requests.get("https://api.song.link/v1-alpha.1/links?url=" + link)
    if response.ok:
        response = response.json()
        for platform in response["linksByPlatform"]:
            #Implement filtering by server preference
            preferences = fetchPreferences(mesage)
            if preferences == None:
                return {}
            if platform in preferences:
                songURLs[platform] = response["linksByPlatform"][platform]["url"]
        fallback = None
        for thumnailProvdier in response["entitiesByUniqueId"]:
            try:
                songURLs["thumbnailURL"] = response["entitiesByUniqueId"][thumnailProvdier]["thumbnailUrl"]
                songURLs["title"] = response["entitiesByUniqueId"][thumnailProvdier]["title"]
                if fallback == None:
                    fallback = songURLs
                for preference in thumbnailPreferences:
                    if preference in response["entitiesByUniqueId"][thumnailProvdier]["platforms"]:
                        return songURLs
            except KeyError:
                continue
        if fallback != None:
            songURLs = fallback

        return songURLs

def isChannelBanned(message: discord.Message) -> bool:
    try:
        with open(f"config.json", "r") as f:
            jsonValues = json.load(f)
            return message.channel.id in jsonValues[message.guild.id]["bannedChannels"]
    except json.decoder.JSONDecodeError:
        return True
    except KeyError:
        return False
def fetchPreferences(message: discord.Message) -> list | None:
    try:
        with open(f"config.json", "r") as f:
            jsonValues = json.load(f)
            try:
                return jsonValues[f"{message.guild.id}"]["preferredPlatforms"]
            except KeyError:
                return defaultPlatforms
    except json.decoder.JSONDecodeError:
        return None
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.event
async def on_message(message):
    if message.author == bot.user or isChannelBanned(message):
        return
    links = findLink(message)
    if len(links) != 0:
        await message.add_reaction("🔗")

@bot.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.user):
    if reaction.emoji == "🔗" and user != bot.user:
        if (not isChannelBanned(reaction.message)) and worthySearch(reaction.message):
            async with reaction.message.channel.typing():
                links = findLink(reaction.message)
                embeds = []
                for link in links:
                    urls = findURLS(link, reaction.message)
                    urllib.request.urlretrieve(urls["thumbnailURL"], "thumbnail.png")
                    recColor = ColorThief('thumbnail.png').get_color(quality=1)
                    embed = discord.Embed(color= discord.Color.from_rgb(recColor[0],recColor[1],recColor[2]), title= f"{urls["title"]}", footer= discord.EmbedFooter(text = "Powered by Songlink"))
                    desc = ""
                    for platform in urls:
                        if platform in ["thumbnailURL", "title"]:
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
                value="spotify"
            ),
            discord.SelectOption(
                label="Apple Music",
                value= "appleMusic"
            ),
            discord.SelectOption(
                label="Youtube Music",
                value="youtubeMusic"
            ),
            discord.SelectOption(
                label="Amazon Music",
                value= "amazonMusic"
            ),
            discord.SelectOption(
                label="Tidal",
                value="tidal"
            ),
            discord.SelectOption(
                label="SoundCloud",
                value="soundcloud"
            ),
            discord.SelectOption(
                label="Pandora",
                value="pandora"
            )
        ]
    )
    async def select_callback(self, select, interaction): # the function called when the user is done selecting options
        with open(f"config.json", "r") as f:
            jsonValues = json.load(f)
            if str(interaction.message.guild.id) not in jsonValues:
                jsonValues[interaction.message.guild.id] = {
                    "preferredPlatforms": [],
                    "bannedChannels": []
                }
            jsonValues[f"{interaction.message.guild.id}"]["preferredPlatforms"] = select.values
        with open(f"config.json", "w") as f:
            json.dump(jsonValues, f, indent=4)
        await interaction.response.send_message(f"got it boss👍 {select.values}", ephemeral=True)
@bot.slash_command(name="manage_platforms", guild_ids= [585594090863853588])
async def manage_platforms(ctx):
    modal = ManagePlatformsView()
    await ctx.respond("Select which platforms to both detect links from, and suggest links for",view=modal, ephemeral=True)
@bot.slash_command(name="ignore_channel", guild_ids= [585594090863853588])
async def manage_platforms(ctx):
    with open(f"config.json", "r") as f:
        jsonValues = json.load(f)
        if str(ctx.guild.id) not in jsonValues:
            jsonValues[f"{ctx.guild.id}"] = {
                "preferredPlatforms": [],
                "bannedChannels": []
            }
        jsonValues[f"{ctx.guild.id}"]["bannedChannels"].append(ctx.channel.id)
    with open(f"config.json", "w") as f:
        json.dump(jsonValues, f, indent=4)
    await ctx.respond(f"Will now ignored links sent in {ctx.channel.id}", ephemeral=True)
@bot.slash_command(name="allow_channel", guild_ids= [585594090863853588])
async def manage_platforms(ctx):
    with open(f"config.json", "r") as f:
        jsonValues = json.load(f)
        if str(ctx.guild.id) not in jsonValues:
            jsonValues[ctx.guild.id] = {
                "preferredPlatforms": [],
                "bannedChannels": []
            }
    if ctx.channel.id not in jsonValues[f"{ctx.guild.id}"]["bannedChannels"]:
        jsonValues[f"{ctx.guild.id}"]["bannedChannels"].append(ctx.channel.id)
        with open(f"config.json", "w") as f:
            json.dump(jsonValues, f, indent=4)
        await ctx.respond(f"Will now allow links sent in this channel", ephemeral=True)
    else:
        await ctx.respond(f"Links were already allowed in this channel :)", ephemeral=True)
try:
    f = open("config.json", "x")
    f.write("{}")
    f.close()
except FileExistsError:
    pass
bot.run(token)