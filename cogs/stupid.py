"""Some fun commands."""
import discord
from discord.ext import commands, tasks
import disputils

from pymongo import ASCENDING
import json

from typing import Optional, Union
import random

import datetime
import pytz

from contextlib import suppress
import itertools

from secret.constants import GUILD_ID, ROLE_NAME
from secret.KEY import *  
from secret.TOKEN import *    

try:
    from secret.webhooks import BOTSPAM_HOOK, ANOTHERCHAT_HOOK, SLASH_COMMANDS_URL
except:
    pass

#API requests headers and URLs
fancy_url = "https://ajith-fancy-text-v1.p.rapidapi.com/text"

fancy_headers = {
    'x-rapidapi-host': "ajith-Fancy-text-v1.p.rapidapi.com",
    'x-rapidapi-key': KEY
}

love_url = "https://love-calculator.p.rapidapi.com/getPercentage"

love_headers = {
    'x-rapidapi-host': "love-calculator.p.rapidapi.com",
    'x-rapidapi-key': KEY
    }

class stupid(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.pin_cache = set()
        self.pin_vote_threshold = 4
        # a loop that changes the name of a role, based on names saved in the database. Names are added with the `role-name` command
        self.role_name_loop.start()   
        self.qotd_cache_loop.start()

        try:
            self.anotherchat_webhook = discord.Webhook.partial(ANOTHERCHAT_HOOK['id'], ANOTHERCHAT_HOOK['token'], adapter=discord.AsyncWebhookAdapter(self.bot.session))
            self.botspam_webhook = discord.Webhook.partial(BOTSPAM_HOOK['id'], BOTSPAM_HOOK['token'], adapter=discord.AsyncWebhookAdapter(self.bot.session))
        except:
            pass

        self.cached_qotd = None

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if str(reaction) == "📌" and user != self.bot.user:
            if reaction.message in self.pin_cache:
                if reaction.count == self.pin_vote_threshold:
                    mod = self.bot.get_cog("Moderator")
                    ctx = await self.bot.get_context(reaction.message)
                    setattr(ctx, "author", self.bot.user)
                    self.pin_cache.remove(reaction.message)
                    await reaction.message.clear_reactions()
                    return await mod.pin(ctx, id_=reaction.message)
            else:
                self.pin_cache.add(reaction.message)
        
    @commands.command(name="fancy", aliases=["f"])
    async def fancy(self, ctx, *, message):
        querystring = {"text":message}
        async with ctx.channel.typing():
            async with self.bot.session.get(fancy_url, headers=fancy_headers, params=querystring) as response:
                return_text = await response.json()
                return_text = return_text["fancytext"].split(",")[0]
            await ctx.send(return_text)

    @commands.command(name="love-calc", aliases=["lc","love","lovecalc"])
    async def love_calc(self, ctx, sname:str, fname=None):
        if fname is None:
            fname = str(ctx.message.author)
            querystring = {"fname":str(ctx.message.author),"sname":sname}
        else:
            querystring = {"fname":str(fname),"sname":str(sname)}
        async with ctx.channel.typing():
            async with self.bot.session.get(love_url, headers=love_headers, params=querystring) as response:
                percent = await response.json()
                percent = percent["percentage"]
                result = await response.json()
                result = result["result"]
            if int(percent) >= 50:
                embed=discord.Embed(title="Love Calculator", colour=discord.Color.green())
                embed.set_author(name=fname)
                embed.add_field(name="That poor person", value=sname, inline=False)
                embed.add_field(name="Percent", value=percent, inline=True)
                embed.add_field(name="Result", value=result, inline=False)
            else:
                embed=discord.Embed(title="Love Calculator", colour=discord.Color.red())
                embed.set_author(name=fname)
                embed.add_field(name="That poor person", value=sname, inline=False)
                embed.add_field(name="Percent", value=percent, inline=True)
                embed.add_field(name="Result", value=result, inline=False)          
            sent_message = await ctx.message.channel.send(content=None, embed=embed)
            await sent_message.add_reaction("✅")
            await sent_message.add_reaction("❌")

    @commands.command(name="weird", aliases=["w"])
    async def weird(self, ctx, *, message):
        out = ''
        curr_func = "lower"
        for i in message:
            if curr_func == "lower":
                out += i.lower()
                curr_func = "upper"
            else:
                out += i.upper()
                curr_func = "lower"
        #await ctx.message.delete()
        await ctx.message.channel.send(out)

    @commands.group(aliases=['tag'], help="Tags.")
    async def wat(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("bruh that isn't a thing.")

    @wat.command(name="add", aliases=["-a"])
    async def add_to_wat(self, ctx, key, *, output):
        await self.bot.stupid_collection.insert_one({"key":key, "output":output})
        await ctx.send("Added")

    @wat.command(name="remove", aliases=["-r"])
    @commands.has_any_role('admin','Bot Dev')
    async def remove_from_wat(self, ctx, key):
        try:
            await self.bot.stupid_collection.delete_one({"key":key})
            await ctx.send(f"Removed {key}")
        except:
            await ctx.send(f"{key} doesn't exist")

    @wat.command(name="edit-output", aliases=["edit-out"])
    async def edit_wat_output(self, ctx, key, *, output):
        try:
            await self.bot.stupid_collection.update_one({'key':key},{"$set":{"output":output}})
            await ctx.send("Updated output.")
        except:
            await ctx.send("Key doesn't exist")

    @wat.command(name="edit-key", aliases=["edit-name"])
    async def edit_wat_key(self, ctx, key, new_key):
        try:
            await self.bot.stupid_collection.update_one({'key':key},{"$set":{"key":new_key}})
            await ctx.send("Updated name.")
        except:
            await ctx.send("Key doesn't exist")    

    @wat.command(name="use", aliases=["-u"])
    async def use(self, ctx, *, key):
        existing = await self.bot.stupid_collection.find_one({"key": key})
        data = existing["output"]
        if data is not None:
            if ctx.channel.name == "another-chat":
                await self.anotherchat_webhook.send(data, username=ctx.author.nick, avatar_url=ctx.author.avatar_url)
            elif ctx.channel.name == "botspam":
                await self.botspam_webhook.send(data, username=ctx.author.nick, avatar_url=ctx.author.avatar_url)
            else:
                await ctx.send(data)
        else:
            ctx.send("Not found.")

    @wat.command(name="list", aliases=["-l"])
    async def list_(self, ctx):
        out = ""
        async for i in self.bot.stupid_collection.find():
            out += i["key"] + "\n"
        out += f"**Total**: {i}"
        await ctx.send(out)

    @wat.command(name="search", aliases=["-s"])
    async def wat_search(self, ctx, key):
        check = 0
        embed = discord.Embed(title="Search Results", color=discord.Color.blurple())
        async for i in self.bot.stupid_collection.find():
            if key.lower() in i["key"].lower():
                embed.add_field(name=i['key'], value=i['output'], inline=False)
                check += 1
        if check == 0:
            embed.add_field(name="No search results found", value=" ")
        await ctx.send(embed=embed)

    @wat.command(name="react")
    async def react(self, ctx, id_: discord.Message, *emojis):
        for i in emojis:
            await id_.add_reaction(i)
        await ctx.message.delete()

    @wat.command(name="slash-add", aliases=["-sa"])
    async def wat_slash_add(self, ctx, key: str, value: str):
        with open("utils/slash_commands.json", "r") as f:
            existing = json.load(f)

        if len(existing["commands"]) >= 50:
            raise Exception("There are already 50 /wat commands. Remove one of them before adding more.")

        update_function = {"name": key, "value": key}
        existing["commands"].append(update_function)

        update_data = {key: value}

        json = {
            "name": "wat",
            "description": "Some of the best .wat commands, but now they look sick.",
            "options": [
                {
                    "name": "use",
                    "description": "Which tag to bring.",
                    "type": 3,
                    "required": True,
                    "choices": existing["commands"]
                },
            ]
        }
        headers = {"Authorization": f"Bot {TOKEN}"}
        with open("utils/slash_commands.json", "w") as f:
            json.dump(existing, f)

        guild_url = f"https://discord.com/api/v8/applications/{APPLICATION_ID}/guilds/{GUILD_ID}/commands"

        # update the command in the application
        async with ctx.channel.typing():
            async with self.bot.session.post(guild_url, json=json, headers=headers) as resp:
                await ctx.send(await resp.text())
            async with self.bot.session.post(SLASH_COMMANDS_URL, json=json) as resp:
                if resp.status == 200:
                    return await ctx.send(f"**{key}** added!")
                else:
                    return await ctx.send("Internal error occurred.")
    
    @commands.command(name="emojify", aliases=['e'])
    async def emojify(self, ctx, *, message):
        emojis = {'a':'🇦', 'b': '🇧', 'c':'🇨', 'd':'🇩', 'e':'🇪', 'f': '🇫', 'g': '🇬', 'h':'🇭', 'i': '🇮', 'j':'🇯', 'k':'🇰', 'l':'🇱', 'm':'🇲', 'n':'🇳', 'o':'🇴', 'p':'🇵', 'q':'🇶', 'r':'🇷', 's':'🇸', 't':'🇹', 'u':'🇺', 'v':'🇻', 'w':'🇼', 'x':'🇽', 'y':'🇾', 'z':'🇿'}
        out = ""
        for letter in message.lower():
            if letter.isalpha():
                out += f"{emojis[letter]} "
            else:
                out += letter
        await ctx.send(out)

    @commands.command(name="owo", aliases=["uwu"])
    async def owo(self, ctx, *, text):
        out = ""
        for i in text:
            case = "upper" if i.isupper() else "lower"
            if i.lower() in ["l","r"]: out += "w" if case=="lower" else "W"
            else: out+=i

        await ctx.send(out)
        
    @commands.command(name="pins", help="Display the messages pinned in the bot database. Useful if your channel has already reached the 50 pin limit.")
    async def pins(self, ctx): 
        data = self.bot.pins_collection.find()
        embeds = []

        counter = 1

        embed = discord.Embed(title=f"{ctx.guild.name} Pins!", color=discord.Color.dark_gold())
        embed.set_thumbnail(url=ctx.guild.icon_url)
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)

        async for pin in data:
            try:
                author = discord.utils.get(ctx.guild.members, id=pin['message_author']).name
            except AttributeError:
                author = pin['message_author']
            if counter % 5 != 0:
                embed.add_field(name=f"{pin['message_synopsis']}",
                                value=f"[_~{author}_, on {pin['date']}]({pin['message_jump_url']})\nPin ID:{pin['_id']}", 
                                inline=False)
                counter += 1
            else:
                embed.add_field(name=f"{pin['message_synopsis']}",
                                value=f"[_~{author}_, on {pin['date']}]({pin['message_jump_url']})\nPin ID:{pin['_id']} {'' if pin['name'] is None else pin['name']}", 
                                inline=False)
                embeds.append(embed)
                counter += 1
                embed = discord.Embed(title=f"{ctx.guild.name} Pins!", color=discord.Color.dark_gold())
                embed.set_thumbnail(url=ctx.guild.icon_url)
                embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        else:
            embeds.append(embed)

        paginator = disputils.BotEmbedPaginator(ctx, embeds)
        await paginator.run()

    @commands.has_guild_permissions(administrator=True)
    @commands.command(name="change-vote-threshold")
    async def change_vote_threshold(self, ctx, arg: int):
        self.pin_vote_threshold = arg
        await ctx.message.add_reaction("✅")

    @commands.command(name="fetch-pin", aliases=["fetchpin"], help="Return a pin based on the ID provided. WIP.")
    async def fetch_pin(self, ctx, identifier: Union[str, int]):

        if identifier.isalpha():
            data = await self.bot.pins_collection.find_one({"name": identifier})
        elif identifier.isdigit():
            data = await self.bot.pins_collection.find_one({"_id": int(identifier)})

        embed = discord.Embed(title=f"Pin **{data['_id']}**", url=data["message_jump_url"], color=discord.Color.blurple())
        text = f"**{data['message_synopsis']}**\n  _by {data['message_author']} on {data['date']}_"
        embed.description = text 
        embed.set_footer(text=f"Requested by {ctx.author.nick}. Click on the embed title to go to the message.", icon_url=ctx.author.avatar_url)
        return await ctx.send(embed=embed)
        
    @commands.group(name="role-name", aliases=["rolename", "rolenames"], invoke_without_command=True)
    async def role_name(self, ctx, *, name: str):
        if len(name) > 15:
            return await ctx.send("bro too long bro")

        if ctx.author.guild_permissions.administrator:
            pass
        else:
            data = await self.bot.economy_collection.find_one({'user': ctx.author.id})
            if data['inv']['role name'] >= 1:
                data['inv']['role name'] -= 1
                await self.bot.economy_collection.update_one({'user': ctx.author.id}, {"$set": data})
            else:
                return await ctx.send("Buy the `role name` item!")

        await self.bot.role_names_collection.insert_one({'name': name, 'by': ctx.author.name})

        embed = discord.Embed(title="Added!", description=f"`{name}` was added to the database. It will be picked randomly.", color=discord.Color.green(), url=r"https://www.youtube.com/watch?v=DLzxrzFCyOs")
        return await ctx.send(embed=embed)

    @role_name.command(name="list", aliases=["all"])
    async def role_name_list(self, ctx):
        data = await self.bot.role_names_collection.find()
        embed = discord.Embed(title="Role names", color=discord.Color.green())
        val = ""
        for i in data:
            val += i['name'] + "\n"
        embed.description = val
        return await ctx.send(embed=embed)

    @role_name.command(name="remove", aliases=["delete"])
    @commands.has_guild_permissions(administrator=True)
    async def role_name_remove(self, ctx, name: str):
        await self.bot.role_names_collection.delete_one({'name': name})
        return await ctx.send(f"Removed `{name}` (if it exists in the database)")

    @commands.command(name="quote", aliases=["qotd"], help="Displays a random quote.")
    async def qotd(self, ctx):
        await ctx.send(self.cached_qotd)

    @commands.command(name="change-presence", aliases=["changepresence", "changestatus", "change-status"], help="Change the bot's status.")
    async def change_presence(self, ctx, activity: str, *, status: str):
        if activity.lower() not in ["playing", "watching", "listening", "streaming"]:
            return await ctx.send('Status has to be one of `"playing", "watching", "listening", "streaming"`')
        
        if len(status) > 30:
            return await ctx.send("bro too long bro")

        if ctx.author.guild_permissions.administrator:
            pass
        else:
            data = await self.bot.economy_collection.find_one({'user': ctx.author.id})
            if data['inv']['bot status'] >= 1:
                data['inv']['bot status'] -= 1
                await self.bot.economy_collection.update_one({'user': ctx.author.id}, {"$set": data})
            else:
                return await ctx.send("Buy the `bot status` item!")

        discord_activity = discord.Activity(name=status)

        if activity.lower() == "playing":
            discord_activity.type = discord.ActivityType.playing
        elif activity.lower() == "listening":
            discord_activity.type = discord.ActivityType.listening
        elif activity.lower() == "watching":
            discord_activity.type = discord.ActivityType.watching
        elif activity.lower() == "streaming":
            discord_activity = discord.Streaming(name=activity)
            
        await ctx.message.add_reaction("✅")
        return await self.bot.change_presence(status=discord.Status.online, activity=discord_activity)

    @tasks.loop(hours=1)
    async def qotd_cache_loop(self):
        """The quotes.rest API has a very strict limit on number of requests that are given for free, so
        instead of making requests everytime the command is called, this loop does the request once an hour and 
        caches it for further use."""
        async with self.bot.session.get(r"http://quotes.rest/qod.json") as response:
            data = await response.json()
        self.cached_qotd = f"{data['contents']['quotes'][0]['quote']}\n~{data['contents']['quotes'][0]['author']}"
        return

    @qotd_cache_loop.before_loop
    async def before_qotd_cache(self):
        await self.bot.wait_until_ready()
        
    @tasks.loop(hours=12)
    async def role_name_loop(self):
        guild = self.bot.get_guild(GUILD_ID)
        role = guild.get_role(ROLE_NAME)
        existing = self.bot.role_names_collection.find()
        data = await existing.to_list(length=None)
        new_name_data = random.choice(data)
        await role.edit(name=new_name_data['name'])

    @role_name_loop.before_loop
    async def rolename_before(self):
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(stupid(bot))
