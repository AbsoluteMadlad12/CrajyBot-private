"""A cog that keeps track of certain chat metrics.
Stores data in it's own collection on MongoDB.

This is an alpha version of the cog, and as such MUST use a testing cache of data, instead of the live database.
"""
import discord
from discord.ext import commands, tasks
import datetime
from bson.codec_options import CodecOptions
from collections import defaultdict
from contextlib import suppress

from utils import graphing
from utils import timezone


class MetricsAlpha(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        db = self.bot.mongo["bot-data"]
        self.bot.test_metrics_collection = db["testing_metrics"]    # remember to switch with actual metrics collection when branch is merged.
        self.metrics_collection = self.bot.test_metrics_collection.with_options(codec_options=CodecOptions(tz_aware=True, tzinfo=timezone.BOT_TZ))
        
        self.loaded_time = datetime.datetime.now(tz=timezone.BOT_TZ)
        self.last_stored_time = None

        self.author_cache = defaultdict(lambda: 0)
        self.channel_cache = defaultdict(lambda: 0)
        self.cached_message_count = 0

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        self.author_cache[str(message.author.id)] += 1
        self.channel_cache[str(message.channel.id)] += 1
        self.cached_message_count += 1

    @commands.has_guild_permissions(administrator=True)
    @commands.command(name="start-metrics_")
    async def start_metrics(self, ctx):
            # copying data from real metrics collection
        data = await self.bot.metrics_collection.find().to_list(length=None)
        await self.metrics_collection.insert_many(data)

        self.metrics_dump.start()
        await ctx.message.add_reaction("✅")
        with suppress(AttributeError):
            embed = discord.Embed(title="Metrics Tracking: Started!", description=f"Time: {self.last_stored_time}", color=discord.Color.green())
            return await ctx.send(embed=embed)

    @commands.has_guild_permissions(administrator=True)
    @commands.command(name="stop-metrics_")
    async def stop_metrics(self, ctx):
        '''self.metrics_dump.stop()

        if len(self.author_cache) != 0 or len(self.channel_cache) != 0:
            self.last_stored_time = datetime.datetime.now(tz=timezone.BOT_TZ)
            insert_doc = {"datetime": self.last_stored_time, "author_counts": self.author_cache, "channel_counts": self.channel_cache}
            await self.metrics_collection.insert_one(insert_doc)
            self.author_cache = defaultdict(lambda: 0)
            self.channel_cache = defaultdict(lambda: 0)
            self.cached_message_count = 0
        
        embed = discord.Embed(title="Metrics Tracking: Stopped", description=f"Time: {self.last_stored_time}", color=discord.Color.red())
        return await ctx.send(embed=embed)'''
        # only clears test metric collection
        await self.bot.test_metrics_collection.delete_many({}) 
    
    @commands.group(name="metrics", invoke_without_command=True)   # add aliases back on merging branch
    async def metrics(self, ctx, amt: int=None):
        if amt is not None:
            delta = datetime.datetime.now(tz=timezone.BOT_TZ) - datetime.timedelta(hours=amt)
            raw_data = await self.metrics_collection.find({"datetime": {"$gte": delta}}).to_list(length=amt)
        else:
            hours, minutes = datetime.datetime.now(tz=timezone.BOT_TZ).hour, datetime.datetime.now(tz=timezone.BOT_TZ).minute
            delta = datetime.datetime.now(tz=timezone.BOT_TZ) - datetime.timedelta(hours=hours, minutes=minutes)
            raw_data = await self.metrics_collection.find({"datetime": {"$gte": delta}}).to_list(length=amt)

        parsed = list(map(graphing.parse_data, raw_data))
        async with ctx.channel.typing():
            file_, embed = graphing.graph_hourly_message_count(parsed)
            return await ctx.send(file=file_, embed=embed)

    @metrics.command(name="hours_")
    async def metrics_status(self, ctx):
        embed = discord.Embed(title="Metrics",
                              description=f"Been tracking since: {self.loaded_time.strftime('%H:%M, %d %B, %Y')}\nLast data dump: {self.last_stored_time.strftime('%H:%M')}",
                              color=discord.Color.green())
        return await ctx.send(embed=embed)

    @tasks.loop(hours=1)
    async def metrics_dump(self):
        # add new data hourly to the db and then reset counts and cache
        self.last_stored_time = datetime.datetime.now(tz=timezone.BOT_TZ)

        if len(self.author_cache) != 0 or len(self.channel_cache) != 0:
            insert_doc = {"datetime": self.last_stored_time, "author_counts": self.author_cache, "channel_counts": self.channel_cache}
            await self.metrics_collection.insert_one(insert_doc)

        self.author_cache = defaultdict(lambda: 0)
        self.channel_cache = defaultdict(lambda: 0)
        self.cached_message_count = 0

    @tasks.loop(hours=24)
    async def metrics_clear(self):
        # a loop to clear out old data. details needs to be discussed.
        pass

def setup(bot):
    bot.add_cog(MetricsAlpha(bot))
