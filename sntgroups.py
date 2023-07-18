import discord
import re
import time
import sqlite3
import json
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
from discord.ext import commands
from discord.utils import get

serverGroups = {}
serverChannels = {}

scheduler = AsyncIOScheduler()

activity = discord.Activity(type=discord.ActivityType.competing, name="dooting...!")
bot = commands.Bot(activity=activity,
                   # help_command=help_command,
                   intents=discord.Intents.all())


# sqlBroker = None


class Group:
    def __init__(self, startTime, gameType, guildid, creator):
        self.groupid = None
        self.startTime = startTime
        self.playerCount = 4
        self.gameType = gameType
        self.guildid = guildid
        self.creator = creator
        self.messageTime = None  # Time of last embed update
        self.message = None
        self.members = []  # discord.Member objects for each user
        self.membersmaybe = []
        self.membersno = []

    async def addMember(self, user):
        if not self.hasMember(user):
            self.members.append(user)

        await GroupDB.saveGroup(self)

    async def addMemberMaybe(self, user):
        if not self.hasMaybeMember(user):
            self.membersmaybe.append(user)

        await GroupDB.saveGroup(self)

    async def addMemberNo(self, user):
        if not self.hasNoMember(user):
            self.membersno.append(user)

        await GroupDB.saveGroup(self)

    async def removeMember(self, user):
        self.members = [x for x in self.members if x.id != user.id]

        await GroupDB.saveGroup(self)

    async def removeMemberMaybe(self, user):
        self.membersmaybe = [x for x in self.membersmaybe if x.id != user.id]

        await GroupDB.saveGroup(self)

    async def removeMemberNo(self, user):
        self.membersno = [x for x in self.membersno if x.id != user.id]

        await GroupDB.saveGroup(self)

    def hasMember(self, user):
        return user.id in [x.id for x in self.members]

    def hasMaybeMember(self, user):
        return user.id in [x.id for x in self.membersmaybe]

    def hasNoMember(self, user):
        return user.id in [x.id for x in self.membersno]

    def memberCount(self):
        return len(self.members)

    def memberMaybeCount(self):
        return len(self.membersmaybe)

    def memberNoCount(self):
        return len(self.membersno)

    async def disband(self):
        groups = serverGroups.get(self.guildid, [])
        serverGroups[self.guildid] = [x for x in groups if x is not self]

        self.members = []

        if self.message:
            await self.message.delete()

        await GroupDB.deleteGroup(self)

    async def updateMessage(self):
        channel = GroupUtils.getServerChannel(self.guildid)

        if len(self.members):
            lines = []
            for m in self.members:
                line = discord.utils.escape_markdown(m.display_name)

                lines.append(line)

            memberList = "\n".join(lines)
        else:
            memberList = "-"

        if len(self.membersmaybe):
            lines2 = []
            for n in self.membersmaybe:
                line2 = discord.utils.escape_markdown(n.display_name)

                lines2.append(line2)

            memberMaybeList = "\n".join(lines2)
        else:
            memberMaybeList = "-"

        if len(self.membersno):
            lines3 = []
            for o in self.membersno:
                line3 = discord.utils.escape_markdown(o.display_name)

                lines3.append(line3)

            memberNoList = "\n".join(lines3)
        else:
            memberNoList = "-"

        # if time.time() < self.startTime:
        #     color = discord.Colour.yellow()
        #     title = "{} starting at <t:{}:t> on <t:{}:D>".format(
        #         discord.utils.escape_markdown(self.gameType), self.startTime, self.startTime)
        # else:
        #     color = discord.Colour.green()
        #     title = "{} starting at <t:{}:t> on <t:{}:D>".format(
        #         discord.utils.escape_markdown(self.gameType), self.startTime, self.startTime)

        color = discord.Colour.blue()
        title = "{} starting on <t:{}:F>".format(
            discord.utils.escape_markdown(self.gameType), self.startTime, self.startTime)

        embed = discord.Embed(title=title, color=color)
        embed.add_field(name=f"Yes ({self.memberCount()})",
                        value=memberList)
        embed.add_field(name=f"Maybe ({self.memberMaybeCount()})",
                        value=memberMaybeList)
        embed.add_field(name=f"Cannot Attend ({self.memberNoCount()})",
                        value=memberNoList)
        # embed.set_footer(text=f"Needing {self.playerCount} people")

        if (self.message is None) and channel:
            guild = bot.get_guild(self.guildid)
            surfy = get(guild.roles, name="surfy people")
            await channel.send(surfy.mention)
            self.message = await channel.send(embeds=[embed], view=GroupView(self))
        else:
            self.message = await self.message.edit(embeds=[embed], view=GroupView(self))

        self.messageTime = time.time()

        await GroupDB.saveGroup(self)  # Update the message id (can it actually change?)

    def getMessageLink(self):
        if self.message is None:
            return None
        else:
            return self.message.jump_url


class GroupDB:
    @classmethod
    async def saveGroup(cls, group):
        memberjson = json.dumps([x.id for x in group.members])
        memberjsonmaybe = json.dumps([x.id for x in group.membersmaybe])
        memberjsonno = json.dumps([x.id for x in group.membersno])
        sqltime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(group.startTime))
        messageid = group.message.id if group.message else None

        sqlBroker = sqlite3.connect("reminders.db")
        cur = sqlBroker.cursor()

        cur.execute(
            "CREATE TABLE if not exists group_games(guildid, ownerid, starttime, playercount, gametype, members, membersmaybe, membersno,  "
            "messageid, groupid)")

        if group.groupid is None:
            cur.execute(
                "INSERT INTO group_games (guildid, ownerid, starttime, playercount, gametype, members, membersmaybe, membersno, messageid) "
                "VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')".format(
                    group.guildid, group.creator.id, sqltime, group.playerCount, group.gameType, memberjson, memberjsonmaybe, memberjsonno, messageid))
            group.groupid = cur.lastrowid
        else:
            # cur.execute("ALTER TABLE group_games ADD COLUMN IF NOT EXISTS groupid TEXT")
            cur.execute(
                "UPDATE group_games SET starttime = '{}', playercount = '{}', gametype = '{}', members = '{}', membersmaybe = '{}', membersno = '{}', "
                "messageid = '{}' WHERE (groupid = '{}')".format(sqltime, group.playerCount, group.gameType, memberjson, memberjsonmaybe, memberjsonno,
                                                                 messageid, group.groupid))
        sqlBroker.commit()

    @classmethod
    async def loadGroups(cls):
        sqlBroker = sqlite3.connect("reminders.db")
        cur = sqlBroker.cursor()
        cur.execute("SELECT * FROM group_games")
        rows = cur.fetchall()
        for row in rows:
            print(repr(row))

            channel = GroupUtils.getServerChannel(int(row['guildid']))
            startTime = row['starttime'].timestamp()
            creator = bot.get_user(row['ownerid'])

            if creator is None:
                print(
                    f"loadGroups(): Can't find group owner by id {row['ownerid']}, discarding group with id {row['groupid']}")
                cur.execute("DELETE FROM group_games WHERE (groupid = {})".format(row['groupid'], ))
                continue

            memberids = json.loads(row['members'])
            members = [bot.get_user(id) for id in memberids]
            members = [x for x in members if not (x is None)]

            membermaybeids = json.loads(row['membersmaybe'])
            membersmaybe = [bot.get_user(id) for id in membermaybeids]
            membersmaybe = [x for x in membersmaybe if not (x is None)]

            membernoids = json.loads(row['membersno'])
            membersno = [bot.get_user(id) for id in membernoids]
            membersno = [x for x in membersno if not (x is None)]

            message = (await channel.fetch_message(row['messageid'])) if row['messageid'] else None

            print(repr(row), repr(members), repr(message))
            g = Group(startTime, row['gametype'], int(row['guildid']), creator)
            g.groupid = int(row['groupid'])
            g.message = message
            g.members = members
            g.membersmaybe = membersmaybe
            g.membersno = membersno

            await g.updateMessage()

            if g.memberCount == 0:
                await g.disband()

        sqlBroker.commit()

    @classmethod
    async def deleteGroup(cls, group):
        if group.groupid is None:
            return
        sqlBroker = sqlite3.connect("reminders.db")
        cur = sqlBroker.cursor()
        cur.execute("DELETE FROM group_games WHERE (groupid = {})".format(group.groupid, ))
        sqlBroker.commit()


class GroupSettingsModal(discord.ui.Modal):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        startTime = discord.ui.InputText(custom_id='startTime', label="Starting in how long",
                                         style=discord.InputTextStyle.short, placeholder="MM or HH:MM or DD:HH:MM",
                                         min_length=1,
                                         max_length=8, required=True, row=1)
        # duration = discord.ui.InputText(custom_id='duration', label="How long to keep the group open after start",
        #                                 style=discord.InputTextStyle.short, placeholder="MM or HH:MM", min_length=1,
        #                                 max_length=5, row=2)
        # playerCount = discord.ui.InputText(custom_id='playerCount', label="Players wanted (including you)",
        #                                    style=discord.InputTextStyle.short, min_length=1, max_length=2, value="4",
        #                                    row=3, required=False)
        gameType = discord.ui.InputText(custom_id='gameType', label="Game type", style=discord.InputTextStyle.short,
                                        min_length=1, max_length=100, placeholder="Scrim vs Aquatic Vanguard", row=4)

        self.add_item(startTime)
        # self.add_item(duration)
        # self.add_item(playerCount)
        self.add_item(gameType)

        self.callbackHandler = None

    def setFields(self, values):
        GroupUtils.scatterModalValues(self.children, values)

    def getFields(self):
        values = GroupUtils.gatherModalValues(self.children)

        if len(values['startTime']) == 0:
            values['startTime'] = '0'

        return values

    def checkFieldError(self):
        values = self.getFields()

        startMinutes = GroupUtils.parseMinutes(values['startTime'])
        if startMinutes is None:
            return f"I could not understand your start time of `{values['startTime']}`. Try DD:HH:MM or HH:MM or MM " \
                   f"format."

        # durationMinutes = GroupUtils.parseMinutes(values['duration'])
        # if durationMinutes == None:
        #     return "I could not understand your duration of `{values['duration']}`. Try HH:MM or MM format."
        # elif durationMinutes > (12 * 60):
        #     return f"Sorry, maximum duration is 12 hours"

        return None

    def setCallbackHandler(self, cbh):
        self.callbackHandler = cbh

    async def callback(self, interaction: discord.Interaction):
        error = self.checkFieldError()
        if error:
            await interaction.response.send_message(content=error, allowed_mentions=discord.AllowedMentions.none(),
                                                    ephemeral=True, delete_after=10)
            return

        if self.callbackHandler is None:
            return
        elif asyncio.iscoroutinefunction(self.callbackHandler):
            await self.callbackHandler(interaction, self)
        else:
            self.callbackHandler(interaction, self)


class GroupView(discord.ui.View):
    def __init__(self, group):
        # NOTE: For a view to be persistent, timeout must not be set,
        #  and all items must have a custom_id set.
        super().__init__()
        self.timeout = None
        self.group = group

    @discord.ui.button(label="Can Attend", style=discord.ButtonStyle.success, custom_id="joinButton", emoji="\u2714")
    async def joinCallback(self, button, interaction):
        print(f"Joined - {interaction.user.name}")
        if self.group.hasMember(interaction.user):
            await interaction.response.send_message("You already said you can come!", ephemeral=True)
        elif self.group.hasMaybeMember(interaction.user):
            await self.group.removeMemberMaybe(interaction.user)
            await self.group.addMember(interaction.user)
            await self.group.updateMessage()
            await interaction.response.send_message(f"You said you can attend: {discord.utils.escape_markdown(self.group.gameType)}", ephemeral=True)
        elif self.group.hasNoMember(interaction.user):
            await self.group.removeMemberNo(interaction.user)
            await self.group.addMember(interaction.user)
            await self.group.updateMessage()
            await interaction.response.send_message(f"You said you can attend: {discord.utils.escape_markdown(self.group.gameType)}", ephemeral=True)
        else:
            await self.group.addMember(interaction.user)
            await self.group.updateMessage()
            await interaction.response.send_message(f"You said you can attend: {discord.utils.escape_markdown(self.group.gameType)}", ephemeral=True)
            # await interaction.response.send_message("User {} joined group '{}'!".format(
            #     discord.utils.escape_markdown(interaction.user.name),
            #     discord.utils.escape_markdown(self.group.gameType)),
            #                                         delete_after=3)

    @discord.ui.button(label="Maybe", style=discord.ButtonStyle.primary, custom_id="maybeButton", emoji="\u2754")
    async def maybeCallback(self, button, interaction):
        print(f"Maybe'd - {interaction.user.name}")
        if self.group.hasMaybeMember(interaction.user):
            await interaction.response.send_message("You're already listed as maybe!", ephemeral=True)
        elif self.group.hasMember(interaction.user):
            await self.group.removeMember(interaction.user)
            await self.group.addMemberMaybe(interaction.user)
            await self.group.updateMessage()
            await interaction.response.send_message("You're listed as maybe", ephemeral=True)
        elif self.group.hasNoMember(interaction.user):
            await self.group.removeMemberNo(interaction.user)
            await self.group.addMemberMaybe(interaction.user)
            await self.group.updateMessage()
            await interaction.response.send_message("You're listed as maybe", ephemeral=True)
        else:
            await self.group.addMemberMaybe(interaction.user)
            await self.group.updateMessage()
            await interaction.response.send_message("You're listed as maybe", ephemeral=True)

    @discord.ui.button(label="Cannot Attend", style=discord.ButtonStyle.danger, custom_id="noButton", emoji="\u2753")
    async def noCallback(self, button, interaction):
        print(f"No'd - {interaction.user.name}")
        if self.group.hasNoMember(interaction.user):
            await interaction.response.send_message("You're already said you can't come!", ephemeral=True)
        elif self.group.hasMember(interaction.user):
            await self.group.removeMember(interaction.user)
            await self.group.addMemberNo(interaction.user)
            await self.group.updateMessage()
            await interaction.response.send_message("You're listed as not attending", ephemeral=True)
        elif self.group.hasMaybeMember(interaction.user):
            await self.group.removeMemberMaybe(interaction.user)
            await self.group.addMemberNo(interaction.user)
            await self.group.updateMessage()
            await interaction.response.send_message("You're listed as not attending", ephemeral=True)
        else:
            await self.group.addMemberNo(interaction.user)
            await self.group.updateMessage()
            await interaction.response.send_message("You're listed as not attending", ephemeral=True)

    @discord.ui.button(label="Leave", style=discord.ButtonStyle.secondary, custom_id="leaveButton", emoji="\u274C")
    async def leaveCallback(self, button, interaction):
        print(f"Left - {interaction.user.name}")
        if not self.group.hasMember(interaction.user) and not self.group.hasNoMember(interaction.user) and not self.group.hasMaybeMember(interaction.user):
            await interaction.response.send_message("You haven't any category joined yet!", ephemeral=True)
        else:
            await self.group.removeMember(interaction.user)
            await self.group.removeMemberMaybe(interaction.user)
            await self.group.removeMemberNo(interaction.user)
            await self.group.updateMessage()
            await interaction.response.send_message(f"You left {self.group.gameType}", ephemeral=True)

            # if self.group.memberCount() > 0:
            # await interaction.response.send_message("You left group {}".format(discord.utils.escape_markdown(
            # self.group.gameType)))
            # await interaction.response.send_message("User {} left group '{}'!".format(
            #     discord.utils.escape_markdown(interaction.user.name),
            #     discord.utils.escape_markdown(self.group.gameType)), delete_after=3)
            # else:
            #     await interaction.response.send_message(
            #         "User %s left group '%s'! All members are gone, so group is disbanded." % (
            #             discord.utils.escape_markdown(interaction.user.name),
            #             discord.utils.escape_markdown(self.group.gameType)), delete_after=3)
            #     await self.group.disband()


class GroupUtils:
    @classmethod
    def gatherModalValues(cls, children):
        values = {}
        for c in children:
            values[c.custom_id] = c.value.strip()
        return values

    @classmethod
    def scatterModalValues(cls, children, values):
        for c in children:
            if not c.custom_id:
                continue
            v = values.get(c.custom_id)
            if v is None:
                continue
            c.value = str(v)

    @classmethod
    def parseMinutes(cls, text):
        # Try DD:HH:MM

        match3 = re.match("^([0-9]{1,2}):([0-9]{1,2}):([0-9]{1,2})$", text)
        if match3:
            return (int(match3.groups()[0]) * 1440) + (int(match3.groups()[1]) * 60) + int(match3.groups()[2])

        # Try HH:MM
        match1 = re.match("^([0-9]{1,2}):([0-9]{1,2})$", text)
        if match1:
            return (int(match1.groups()[0]) * 60) + int(match1.groups()[1])

        # Try MMM
        match2 = re.match("^[0-9]{1,3}$", text)
        if match2:
            return int(text)

        # Not understood
        return None

    @classmethod
    def getServerChannel(cls, guildid):
        return serverChannels.get(guildid)


class Groups:
    @classmethod
    def findGroupWithMember(cls, guildid, user):
        groups = serverGroups.get(guildid, [])
        for g in groups:
            if g.hasMember(user):
                return g
        return None

    @classmethod
    def findGroupWithCreator(cls, guildid, user):
        groups = serverGroups.get(guildid, [])
        for g in groups:
            if g.creator.id == user.id:
                return g
        return None

    @classmethod
    async def update(cls):
        now = int(time.time())
        for guildid in serverGroups.keys():
            groups = serverGroups[guildid]
            for g in groups:
                if g.messageTime and (g.messageTime < (now - 55)):
                    # print(f"Updating group message for '{g.gameType}'")
                    await g.updateMessage()

    @classmethod
    async def setServerChannel(cls, guildid, channel):
        serverChannels[guildid] = channel
        sqlBroker = sqlite3.connect("reminders.db")
        cur = sqlBroker.cursor()
        cur.execute("CREATE TABLE if not exists group_channels(guildid, channelid)")
        cur.execute("DELETE FROM group_channels WHERE (guildid = {})".format(guildid))
        cur.execute("INSERT INTO group_channels (guildid, channelid) VALUES ({}, {})".format(guildid, channel.id))
        sqlBroker.commit()

    @classmethod
    async def loadServerChannels(cls):
        sqlBroker = sqlite3.connect("reminders.db")
        cur = sqlBroker.cursor()
        cur.execute("SELECT guildid, channelid FROM group_channels")
        rows = cur.fetchall()
        sqlBroker.commit()
        for row in rows:
            (guildid, channelid) = row

            channel = bot.get_channel(channelid)
            if channel is None:
                continue  # Channel was probably deleted

            # print(f"  Groups channel for guild {guildid} is '{channel.name}'")
            serverChannels[guildid] = channel

    @classmethod
    async def startup(cls):
        await cls.loadServerChannels()
        await GroupDB.loadGroups()


class GroupCmds:
    def __init__(self):
        pass

    @classmethod
    async def handleGroupModalCreate(cls, interaction, modal):
        values = modal.getFields()
        print(f"handleGroupModalCreate(): {repr(values)}")

        startMinutes = GroupUtils.parseMinutes(values['startTime'])
        # durationMinutes = GroupUtils.parseMinutes(values['duration'])

        # print("stmin", startMinutes)
        # the following turns days into seconds
        # print(60 * 60 * 24)
        # print("time", time.time())
        # the following turns minutes into seconds
        # print("sttime", startMinutes * 60)
        # print("added", time.time() + (startMinutes * 60))

        startTime = int(time.time()) + (startMinutes * 60)
        g = Group(startTime, values['gameType'], interaction.guild_id, interaction.user)
        if not serverGroups.get(interaction.guild_id):
            serverGroups[interaction.guild_id] = []
        serverGroups[interaction.guild_id].append(g)

        # await g.addMember(interaction.user)
        # await g.addMemberMaybe(interaction.user)
        # await g.addMemberNo(interaction.user)
        await g.updateMessage()

        link = g.getMessageLink()
        responseText = "Okay, created a new group for '{}'.".format(discord.utils.escape_markdown(g.gameType))
        if link:
            responseText += f" You can find it here: {link}"
        await interaction.response.send_message(content=responseText, ephemeral=True)

    @classmethod
    async def handleGroupModalEdit(cls, interaction, modal):
        values = modal.getFields()
        print(f"handleGroupModalEdit(): {repr(values)}")

        startMinutes = GroupUtils.parseMinutes(values['startTime'])
        # durationMinutes = GroupUtils.parseMinutes(values['duration'])

        g = Groups.findGroupWithCreator(interaction.guild_id, interaction.user)

        g.startTime = int(time.time()) + (startMinutes * 60)
        # g.duration = durationMinutes * 60
        g.playerCount = values['playerCount']
        g.gameType = values['gameType']

        await g.updateMessage()

        responseText = "Okay, edited your group for '{}'.".format(discord.utils.escape_markdown(g.gameType))
        await interaction.response.send_message(content=responseText, ephemeral=True)

    @classmethod
    async def create(cls, ctx):
        if not ctx.guild_id:
            await ctx.respond("You can only use this command on a server, not in a DM.", ephemeral=True)
        # elif Groups.findGroupWithCreator(ctx.guild_id, ctx.user):
        #     await ctx.respond("You have already created a group. You can use `/group disband` to disband the old one.",
        #                       ephemeral=True)
        elif GroupUtils.getServerChannel(ctx.guild_id) is None:
            await ctx.respond("There is no event channel defined for this server. Try `event channel` to set one.",
                              ephemeral=True)
        else:
            modal = GroupSettingsModal(title="Create a group")
            modal.setCallbackHandler(cls.handleGroupModalCreate)
            await ctx.send_modal(modal)

    @classmethod
    async def edit(cls, ctx):
        if not ctx.guild_id:
            await ctx.respond("You can only use this command on a server, not in a DM.", ephemeral=True)

        g = Groups.findGroupWithCreator(ctx.guild_id, ctx.user)
        if not g:
            await ctx.respond("You haven't created an event. You can create one with `/event create`.", ephemeral=True)
        else:
            startMinutes = max(0, int((g.startTime - time.time()) / 60))

            modal = GroupSettingsModal(title="Edit event")
            modal.setFields({"startTime": startMinutes, "playerCount": g.playerCount,
                             "gameType": g.gameType})
            modal.setCallbackHandler(cls.handleGroupModalEdit)
            await ctx.send_modal(modal)

    @classmethod
    async def disband(cls, ctx):
        if not ctx.guild_id:
            await ctx.respond("You can only use this command on a server, not in a DM.")
            return

        g = Groups.findGroupWithCreator(ctx.guild_id, ctx.user)
        if not g:
            await ctx.respond("You haven't created any group to disband.", ephemeral=True)
        else:
            await g.disband()
            await ctx.respond("Okay, disbanded your group '{}'.".format(discord.utils.escape_markdown(g.gameType)),
                              ephemeral=True)

    @classmethod
    async def channel(cls, ctx, channel):
        if not ctx.guild_id:
            await ctx.respond("You can only use this command on a server, not in a DM.", ephemeral=True)
        await Groups.setServerChannel(ctx.guild_id, channel)
        await ctx.respond("Okay, set groups channel to '{}'".format(discord.utils.escape_markdown(channel.name)),
                          ephemeral=True)


scheduler.add_job(Groups.update, 'cron', minute='*', timezone='UTC')
scheduler.start()
