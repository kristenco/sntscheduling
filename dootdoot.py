from discord import SlashCommandGroup, option
from dotenv import load_dotenv
from os import getenv, environ
from discord.ext import commands
import sntgroups
import sys
import traceback
import os
import sys
from zoneinfo import ZoneInfo
import requests
from datetime import datetime, time
import discord
import random
import schedule
from schedule import every, repeat, run_pending
import re
import asyncio
import fnmatch as fn
from discord.ext import commands, tasks
import youtube_dl

help_command = commands.DefaultHelpCommand(no_category='Commands')

bot = sntgroups.bot

groupCmds = SlashCommandGroup('event', 'For creating events')
# Owners in order: Me, Steven, Kai, James, Haku
owners = [134517959124058112, 406690221694910464, 261652932947083274, 357243868053372929, 245591249027989504]

# -----------------------------------------------------------------------------

###
# # KRISSY MED REMINDER
# ####

@tasks.loop(minutes=1)
async def reminder_loop():
    user = bot.get_user(134517959124058112)
    tz = ZoneInfo("America/New_York")
    t = datetime.now(tz)
    if t.hour == 10 and t.minute == 0:
        await user.send("take viibryd!")
        print("reminder sent!")

    # Steven's ID: 406690221694910464
    # My ID: 134517959124058112

# -----------------------------------------------------------------------------

####
# RESTART COMMAND
####

def restart_bot(): 
  os.execv(sys.executable, ['python'] + sys.argv)

@bot.slash_command(name= 'restart')
@commands.is_owner()
async def restart(ctx):
  await ctx.respond("i restart now!")
  print("Restarting Dooter...")
  restart_bot()

# -----------------------------------------------------------------------------

####
# HEEMO COMMAND
####

@bot.slash_command(name="heemo")
async def heemo(ctx): 
    await ctx.respond("heemo!!")


# -----------------------------------------------------------------------------

####
# CHANNEL SELECT TEST
####

@bot.slash_command(name="channelselect")
@option("channel", discord.TextChannel, description="Select a channel")
async def channel_select(ctx: discord.ApplicationContext, channel: discord.TextChannel):
    await ctx.respond(f"Hi! You selected {channel.mention} channel.")

# -----------------------------------------------------------------------------

###
# TEST REMINDER COMMAND
####

@bot.slash_command(name="remind", case_insensitive = True, aliases = ["remind", "remindme", "remind_me", "r", "rm"])
async def setreminder(ctx, time, reminder):
    user = await bot.fetch_user(ctx.author.id)
    embed = discord.Embed(color=0x55a7f7, timestamp=datetime.utcnow())
    seconds = 0
    if reminder is None:
        embed.add_field(name='invalid reminder', value='what do you want me to remind you about?') # Error message
    if time.lower().endswith("d"):
        seconds += int(time[:-1]) * 60 * 60 * 24
        if seconds == 86400:
            counter = f"{seconds // 60 // 60 // 24} day"
        else:
            counter = f"{seconds // 60 // 60 // 24} days"
    if time.lower().endswith("h"):
        seconds += int(time[:-1]) * 60 * 60
        if seconds == 3600:
            counter = f"{seconds // 60 // 60} hour"
        else:
            counter = f"{seconds // 60 // 60} hours"
    elif time.lower().endswith("m"):
        seconds += int(time[:-1]) * 60
        if seconds == 60:
            counter = f"{seconds // 60} minute"
        else:
            counter = f"{seconds // 60} minutes"
    elif time.lower().endswith("s"):
        seconds += int(time[:-1])
        if seconds == 1:
            counter = f"{seconds} second"
        else:
            counter = f"{seconds} seconds"
    if seconds == 0:
        embed.add_field(name='invalid duration',
                        value='please enter a duration!')
    # elif seconds < 300:
    #     embed.add_field(name='Warning',
    #                     value='You have specified a too short duration!\nMinimum duration is 5 minutes.')
    # elif seconds > 7776000:
    #     embed.add_field(name='Warning', value='You have specified a too long duration!\nMaximum duration is 90 days.')
    else:
        await ctx.respond(f"okie, i will remind you about **{reminder}** in **{counter}**!")
        await asyncio.sleep(seconds)
        await ctx.respond(f"{ctx.author.mention} i've sent the reminder in your dms!")
        await user.send(f"hiya, **{counter} ago** you asked me to remind you about: **{reminder}**")
        return
    await ctx.respond(embed=embed)

# -----------------------------------------------------------------------------

####
# ERROR MESSAGE
####

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.respond('Phew, I need a break! Please try again in **{:.0f} seconds**.'.format(error.retry_after))
    elif isinstance(error, commands.NotOwner):
        await ctx.respond('sorry, this command is owner only!')

# -----------------------------------------------------------------------------

###
# WORDS REQUESTS
####

word_site = "https://www.mit.edu/~ecprice/wordlist.10000"

response1 = requests.get(word_site)
words = response1.content.decode('UTF-8')

# -----------------------------------------------------------------------------

###
# COUNTRY REQUESTS
####

country_site = "https://gist.githubusercontent.com/kalinchernev/486393efcca01623b18d/raw/daa24c9fea66afb7d68f8d69f0c4b8eeb9406e83/countries"

country_response = requests.get(country_site)

# -----------------------------------------------------------------------------

####
# ON READY
####

@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")
    # await bot.change_presence(activity=discord.Game("doot doot"))

    reminder_loop.start()

# -----------------------------------------------------------------------------

####
# RANDOM WORD
####

@bot.slash_command(description="Pulls a random word from a list of words")
async def word(ctx):
    send = random.choice(words.splitlines())
    await ctx.respond(send)

# -----------------------------------------------------------------------------

####
# MULTIPLE RANDOM WORDS
####

@bot.slash_command(description="Pulls random words from a list of words (prints 2-10 words)")
async def wordplus(ctx):
    multiple = ""
    for w in range(random.randint(2, 10)):
        multiple += random.choice(words.splitlines()) + " "
    await ctx.respond(multiple)

# -----------------------------------------------------------------------------

####
# TTR DISTRICT
####

@bot.slash_command(description="Gives a random TTR district")
async def ttrdist(ctx):
    ttr_dist = [
    'Blam Canyon', 'Boingbury', 'Bounceboro', 'Fizzlefield', 'Gulp Gulch',
    'Hiccup Hills', 'Kaboom Cliffs', 'Splashport', 'Splat Summit',
    'Splatville', 'Thwackville', 'Whoosh Rapids', 'Zapwood', 'Zoink Falls'
]
    dist = random.choice(ttr_dist)
    await ctx.respond(dist)

# -----------------------------------------------------------------------------

####
# TTCC DISTRICT
####

@bot.slash_command(aliases=['ccdist'], description="Gives a random TTCC district")
async def ttccdist(ctx):
    ttcc_dist = [
    'Anvil Acres', 'Cupcake Cove', 'Hypno Heights', 'Kazoo Kanyon',
    'Quicksand Quarry', 'Seltzer Summit', 'Tesla Tundra'
]
    dist = random.choice(ttcc_dist)
    await ctx.respond(dist)

# -----------------------------------------------------------------------------

####
# GRAB UTENSIL
####

@bot.slash_command(description="Responds with a writing utensil (a funny is hidden in here)")
async def utensil(ctx):
    utensil_list = [
    'pen', 'pencil', 'marker', 'coloured pencil', 'pencil crayon', 'sharpie',
    'mechanical pencil', 'fork'
]
    grabbed_utensil = random.choice(utensil_list)
    utensil_string = "You should use a " + grabbed_utensil + "."
    await ctx.respond(utensil_string)

# -----------------------------------------------------------------------------

####
# RNG COMMAND
####

@bot.slash_command(description="Responds with a random number between 1 and 1000")
async def rng(ctx):
    num = random.randint(1, 1000)
    await ctx.respond(num)

# -----------------------------------------------------------------------------

####
# RANDOM EMOTE
####

@bot.slash_command(description="Responds with a random text emote")
async def emote(ctx):
    emotes = [
    '¯\_(ツ)_/¯', '(✿◠‿◠)', '(｡◕‿◕｡)', '(. ❛ ᴗ ❛.)', '｡^‿^｡', '(=^ェ^=)',
    'ヾ(＾。^*)♪～', 'ヾ(´〇`)ﾉ♪♪♪', '( o˘◡˘o) ┌iii┐'
]
    pick = random.choice(emotes)
    await ctx.respond(pick)

# -----------------------------------------------------------------------------

####
# RANDOM COUNTRY
####

@bot.slash_command(description="Responds with a random country")
async def country(ctx):
    country_item = country_response.content.decode('UTF-8').splitlines()
    random_country_pick = random.choice(country_item)
    await ctx.respond(random_country_pick)

# -----------------------------------------------------------------------------

####
# RANDOM STATE
####

@bot.slash_command(description="Responds with a random state")
async def state(ctx):
    states_list = [
    'Alaska', 'Alabama', 'Arkansas', 'Arizona', 'California', 'Colorado',
    'Connecticut', 'District of Columbia', 'Delaware', 'Florida', 'Georgia',
    'Hawaii', 'Iowa', 'Idaho', 'Illinois', 'Indiana', 'Kansas', 'Kentucky',
    'Louisiana', 'Massachusetts', 'Maryland', 'Maine', 'Michigan', 'Minnesota',
    'Missouri', 'Mississippi', 'Montana', 'North Carolina', 'North Dakota',
    'Nebraska', 'New Hampshire', 'New Jersey', 'New Mexico', 'Nevada',
    'New York', 'Ohio', 'Oklahoma', 'Oregon', 'Pennsylvania', 'Rhode Island',
    'South Carolina', 'South Dakota', 'Tennessee', 'Texas', 'Utah', 'Virginia',
    'Vermont', 'Washington', 'Wisconsin', 'West Virginia', 'Wyoming'
]
    state_pick = random.choice(states_list)
    await ctx.respond(state_pick)

# -----------------------------------------------------------------------------

####
# RANDOM PROVINCE
####

@bot.slash_command(description="Responds with a random province")
async def province(ctx):
    provinces_list = [
    'Alberta', 'British Columbia', 'Manitoba', 'New Brunswick',
    'Newfoundland and Labrador', 'Northwest Territories', 'Novia Scotia',
    'Nunavut', 'Ontario', 'Prince Edward Island', 'Quebec', 'Saskatchewan',
    'Yukon'
]
    province_pick = random.choice(provinces_list)
    await ctx.respond(province_pick)

# -----------------------------------------------------------------------------

####
# SQUID GAME SIM
####

# @bot.slash_command(aliases=['sg', 'dg', 'dootgame'])
# async def squidgame(ctx):
#     await ctx.respond('hi, you activated the DOOT GAMES! (squid game simulator!)')

#     global times_used
#     await ctx.respond(f"y or n")

#     # This will make sure that the response will only be registered if the following
#     # conditions are met:
#     def check(msg):
#         return msg.author == ctx.author and msg.channel == ctx.channel and \
#         msg.content.lower() in ["y", "n"]

#     msg = await client.wait_for("message", check=check)
#     if msg.content.lower() == "y":
#         await ctx.respond("You said yes!")
#     else:
#         await ctx.respond("You said no!")

#     times_used = times_used + 1

#     # code
#     try:
#         msg = await client.wait_for("message", check=check, timeout=30) # 30 seconds to reply
#     except asyncio.TimeoutError:
#         await ctx.respond("oops, you didn't reply in time!")


# -----------


# @bot.slash_command(aliases=['sg', 'dg', 'dootgame'])
# async def squidgame(ctx):
#     await ctx.respond('hi, you activated the DOOT GAMES! (squid game simulator!)')

#     global times_used
#     cont = True

#     try:
#         while cont:
#             await ctx.respond(f"enter a person's name")

#             def check(msg):
#                 return msg.author == ctx.author and msg.channel == ctx.channel
            
#             msg = await asyncio.bot.wait_for("message", check=check, timeout=30)

#             if msg:
#                 await ctx.respond("woohoo!")
#             else:
#                 await ctx.respond("uh oh!!!")
            
#             times_used = times_used + 1

#             if times_used > 100:
#                 await ctx.respond("you've reached the maximum number of people! let's begin the games!")
#                 cont = False
#     except asyncio.TimeoutError:
#         await ctx.respond("oops, you didn't reply in time!")


# -----------------------------------------------------------------------------

####
# AWAKE
####

@bot.slash_command(description="Check if she's awake!")
async def awake(ctx):
    await ctx.respond('i here, heemo!')

# -----------------------------------------------------------------------------

####
# JOIN VC
####

@bot.slash_command()
async def join(ctx):
    author = ctx.author
    if not ctx.author.voice:
        await ctx.respond("{} is not connected to a voice channel! >:(".format(ctx.author.name))
        return
    elif ctx.guild.voice_client in bot.voice_clients:
        await ctx.respond("i'm already here!!!")
    else:
        channel = ctx.author.voice.channel
        await channel.connect()

@bot.slash_command()
async def gn(ctx):
    if ctx.guild.voice_client in bot.voice_clients:
        await ctx.voice_client.disconnect()
    else:
        await ctx.respond("i'm not in a voice channel! >:(")

# -----------------------------------------------------------------------------

####
# WATER BALLOON
####

@bot.slash_command(description="Throws water balloon!")
async def balloon(ctx):
    await ctx.respond('*throws water balloon*')

# -----------------------------------------------------------------------------

####
# TOP BANANA
####

@bot.slash_command(description="Says top banana phrase!")
async def banana(ctx):
    await ctx.respond('You\'re the top banana.')

# -----------------------------------------------------------------------------

####
# KITCHEN
####

@bot.slash_command(description="Says kitchen heat phrase!")
async def kitchen(ctx):
    await ctx.respond('If you can\'t take the heat, stay out of the kitchen.')

# -----------------------------------------------------------------------------

####
# FITNESSGRAM
####

@bot.slash_command(aliases=['fitness gram'], description="the fitnessgram pacer test is a")
async def fitnessgram(ctx):
    await ctx.respond('''The FitnessGram Pacer Test is a multistage aerobic capacity test that progressively gets more difficult as it continues. 
    The 20 meter pacer test will begin in 30 seconds. Line up at the start. 
    The running speed starts slowly but gets faster each minute after you hear this signal bodeboop. 
    A sing lap should be completed every time you hear this sound. ding Remember to run in a straight line and run as long as possible. 
    The second time you fail to complete a lap before the sound, your test is over. 
    The test will begin on the word start. On your mark. Get ready!… Start. ding''')

# -----------------------------------------------------------------------------


####
# COMMAND TO PURGE MESSAGES
####

@bot.slash_command(name="purge", description="Purges the last x messages that were sent before inputting this command.")
@commands.is_owner()
async def purge(ctx, amount: int):
	await ctx.respond(f"Successfully deleted {amount} messages.", ephemeral=True)
	await ctx.channel.purge(limit=amount)

# ------------------------------------------------------------------------------------------------------------------------------------------------

####
# SAY COMMAND
####

@bot.slash_command(help="Doots will say anything you want her to with this command",
             description="Doots repeats after you")
async def say(ctx, *args):
    respons3 = ""
    no_say = [
        '*idiot*', '*dumbass*', '*dick', '*fuck*', '*shit*', '*bitch*', '*damn*'
    ]

    for arg in args:
        if arg in no_say:
            respons3 = "i won't say that :("
            break
        for i in no_say:
            if fn.fnmatch(arg, i):
                respons3 = "i won't say that :("
                break
        if respons3 != "i won't say that :(":
                respons3 = respons3 + " " + arg
    if respons3 == "i won't say that :(":
        await ctx.respond(respons3, ephemeral=True)
    else:
        await ctx.respond("Got it!", ephemeral=True)

    await ctx.channel.send(respons3)

# -----------------------------------------------------------------------------

####
# SAY COMMAND
####

@bot.slash_command(name="send")
@commands.has_any_role(762485971827556442, 966140524891349132) 
async def say(ctx, *, messagesent):
    await ctx.respond("Got it!", ephemeral=True)
    await ctx.channel.send(messagesent)
    await ctx.message.delete()

# ------------------------------------------------------------------------------------------------------------------------------------------------

@groupCmds.command(name='create', description='Create an event')
async def cmdGroupCreate(ctx):
    await sntgroups.GroupCmds.create(ctx)


@groupCmds.command(name='edit', description='Edit event settings')
async def cmdGroupEdit(ctx):
    await sntgroups.GroupCmds.edit(ctx)


@groupCmds.command(name='remove', description='Remove your event')
async def cmdGroupDisband(ctx):
    await sntgroups.GroupCmds.disband(ctx)


@groupCmds.command(name='channel', description='Set group channel')
@option("channel", discord.TextChannel, description="Select a channel")
async def cmdGroupChannel(ctx: discord.ApplicationContext, channel: discord.TextChannel):
    if (ctx.user.id not in owners) and (not ctx.user.guild_permissions.administrator):
        await ctx.respond("You're not allowed to do that.", ephemeral=True)
    else:
        await sntgroups.GroupCmds.channel(ctx, channel)


# ------------------------------------------------------------------------------------------------------------------------------------------------

@bot.event
async def on_message(message):
    await bot.process_commands(message)

    if message.author == bot.user:
        return

    if 'hewwo' in message.content.lower():
        await message.channel.send("hewwo!")
    elif 'hemwo' in message.content.lower():
        await message.channel.send("hemwo!")

    if message.content.lower() == '*hugs*':
        await message.channel.send("*hugs back*")

    if 'goobnight doot' in message.content.lower(
    ) or 'goodnight doot' in message.content.lower():
        await message.channel.send(
            f"goobnight {message.author.mention}!!")

    if 'goob morning doot' in message.content.lower(
    ) or 'good morning doot' in message.content.lower():
        await message.channel.send(
            f"goob morning {message.author.mention}!!")

    if 'good doot' in message.content.lower() or 'goob doot' in message.content.lower() or 'best doot' in message.content.lower():
        await message.channel.send('yay! :D')

    if "sowwy doot" in message.content.lower():
        await message.channel.send("it's okie, i forgive u")

    if message.content.lower() == 'does doots love me' or message.content.lower() == 'does doots love me?' or message.content.lower() == 'does doot love me' or message.content.lower() == 'does doot love me?':
        await message.channel.send("YES OF COURSE! <3")
    
    if "love u doot" in message.content.lower() or "love you doot" in message.content.lower() or "loving doot" in message.content.lower() or "love doot" in message.content.lower():
        await message.channel.send("yay i love u too!")

    if 'thank you doot' in message.content.lower() or 'thank u doot' in message.content.lower():
        await message.channel.send(f"of course!!!!!!! >:) {message.author.mention}!")

    if 'hi doot' in message.content.lower() or 'hey doot' in message.content.lower() or 'hello doot' in message.content.lower() or 'hewwo doot' in message.content.lower() or 'hemwo doot' in message.content.lower():
        await message.channel.send('hey thas me! hemwo!')

    if 'doot doot' in message.content.lower():
        await message.channel.send('doot doot!')
    
    if 'bopbop' in message.content.lower().replace(" ", ""):
        await message.channel.send('bop bop!')
    
    if 'where is doot' in message.content.lower() or 'where\'s doot' in message.content.lower() or 'where doot' in message.content.lower() or 'i miss doot' in message.content.lower():
        await message.channel.send("<:dootpeek:894467119738146896>")
    
    if bot.user.mentioned_in(message):
        await message.channel.send('<:dootpeek:894467119738146896>')


bot.add_application_command(groupCmds)
load_dotenv()
token = getenv("TOKEN")
my_secret = environ["TOKEN"]
bot.run(my_secret)
