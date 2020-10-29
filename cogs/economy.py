import discord
from discord.ext import commands

from pymongo import MongoClient

from contextlib import suppress

import typing
import asyncio
import random

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return ctx.channel.name in ["bot-test","botspam-v2","botspam"]

    def get_user_dict(self, ctx: discord.ext.commands.Context, user: typing.Union[discord.Member, str]) -> dict:
        """Helper function to get user data from database"""
        if user is not None:
            if isinstance(user, discord.Member): 
                user_dict = self.bot.economy_collection.find_one({'user': user.id})
            elif isinstance(user, str):
                for member in ctx.guild.members:
                    if member.name.lower() == user.lower():
                        user = member
                    elif member.nick is not None:
                        if member.nick.lower() == user.lower():
                            user = member
                user_dict = self.bot.economy_collection.find_one({'user': user.id})
        else: 
            user_dict = self.bot.economy_collection.find_one({'user': ctx.author.id})
        return user_dict

    @commands.command(name="withdraw", aliases=["with"])
    async def withdraw(self, ctx, amount):
        try:
            amount = int(amount)
            if self.bot.economy_collection.find_one({'user': ctx.author.id})['bank'] >= amount:
                self.bot.economy_collection.update_one({'user': ctx.author.id},{"$inc": {'bank': -amount, 'cash':amount}})
                response = discord.Embed(title = str(ctx.message.author), description = f"Withdrew {int(amount)}", colour = discord.Color.green())
                await ctx.message.channel.send(embed=response)
            else:
                await ctx.message.channel.send("You do not have that much balance")
        except ValueError:
            if amount.lower() == "all":
                user_data = self.bot.economy_collection.find_one({'user': ctx.author.id})
                self.bot.economy_collection.find_one_and_update({'user': ctx.author.id}, {"$set":{'bank': 0, 'cash': user_data['cash']+user_data['bank']}})
                response = discord.Embed(title = str(ctx.message.author), description = f"Withdrew {int(user_data['bank'])}", colour = discord.Color.green())
                await ctx.message.channel.send(embed=response)

    @commands.command(name="deposit", aliases=["dep"])
    async def deposit(self, ctx, amount):
            try:
                amount = int(amount)
                user_data = self.bot.economy_collection.find_one({'user': ctx.author.id})
                if user_data['cash'] >= amount:
                    self.bot.economy_collection.update_one({'user': ctx.author.id}, {"$inc":{'cash': -amount, 'bank': amount}})
                    response = discord.Embed(title = str(ctx.message.author), description = f"Deposited {int(amount)}", colour = discord.Color.green())
                    await ctx.message.channel.send(embed=response)
                else:
                    await ctx.message.channel.send("You don't have that much moni to deposit")
            except ValueError:
                if amount.lower() == "all":
                    user_data = self.bot.economy_collection.find_one({'user': ctx.author.id})
                    self.bot.economy_collection.update_one({'user': ctx.author.id}, {"$inc":{'cash': -user_data['cash'], 'bank': user_data['cash']}})
                    response = discord.Embed(title = str(ctx.message.author), description = f"Deposited {int(user_data['cash'])}", colour = discord.Color.green())
                    await ctx.message.channel.send(embed=response)
                    
    @commands.command(name='bal')
    async def balance(self, ctx, user: typing.Union[discord.Member, str]=None):
        if user is None: user = ctx.author
        user_dict = self.get_user_dict(ctx, user)

        networth = (user_dict['cash'] + user_dict['bank']) - user_dict['debt']
        response = discord.Embed(title=str(user), description="Balance is:")
        response.add_field(name="Cash Balance : ",value=f"{int(user_dict['cash'])}", inline = False)
        response.add_field(name="Bank balance : ",value=f"{int(user_dict['bank'])}", inline = False)
        response.add_field(name="Debt : ",value=f"{-user_dict['debt']}", inline = False)
        response.add_field(name="Net Worth : ",value=int(networth), inline = False)

        return await ctx.send(embed=response)

    @commands.command(name='work')
    @commands.cooldown(1, 3600, commands.BucketType.user)  
    async def work(self, ctx):
        rand_val = random.randint(50,200)
        self.bot.economy_collection.update_one({'user': ctx.author.id}, {"$inc": {'cash': rand_val}})
        response = discord.Embed(title=str(ctx.message.author), description=f"You earned {rand_val}", colour=discord.Colour.green())
        return await ctx.message.channel.send(embed=response)

    @work.error
    async def work_error(self,ctx,error):             
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.message.channel.send(f"Time remaining = {int(error.retry_after/60)} mins")

    @commands.command(name='slut')
    @commands.cooldown(1, 3600, commands.BucketType.user)          
    async def slut(self, ctx):
        winning_odds=[1,2,3,4,5,6]
        if random.randint(1,10) in winning_odds:
            rand_val = random.randint(60,200)
            self.bot.economy_collection.update({'user': ctx.author.id}, {"$inc": {'cash': rand_val}})
            response = discord.Embed(title=str(ctx.message.author), description=f"You whored out and earned {rand_val}!", colour=discord.Colour.green())
        
        else:
            rand_val = random.randint(60,200)
            self.bot.economy_collection.update({'user': ctx.author.id}, {"$inc": {'cash': -rand_val}})
            response = discord.Embed(title=str(ctx.message.author),description=f"You hooked up with a psychopath lost {rand_val}!",colour=discord.Colour.red())
        return await ctx.message.channel.send(embed=response)
    
    @slut.error
    async def slut_error(self,ctx,error):   
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.message.channel.send(f"Time remaining = {int(error.retry_after/60)} mins")

    @commands.command(name="crime")
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def crime(self, ctx):            
        winning_odds=[1,2,3,4]
        if random.randint(1,10) in winning_odds:
            rand_val = random.randint(150,400)
            self.bot.economy_collection.update({'user': ctx.author.id}, {"$inc": {'cash': rand_val}})
            response = discord.Embed(title=str(ctx.author), description=f"You successfuly commited crime and earned {rand_val}!", colour=discord.Colour.green())
        else:
            rand_val = random.randint(150,250)
            self.bot.economy_collection.update({'user': ctx.author.id}, {"$inc": {'cash': -rand_val}})
            response = discord.Embed(title=str(ctx.author), description=f"You got caught and were fined {rand_val}!", colour=discord.Colour.red())
        return await ctx.send(embed=response)

    @crime.error
    async def crime_error(self,ctx,error):            
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.message.channel.send(f"Time remaining = {int(error.retry_after/60)} mins")

    @commands.command(name="leaderboard", aliases=["top","lb"])   
    async def leaderboard(self,ctx):
        leaderboard_data = list(self.bot.economy_collection.find())
        #Bubble sort inefficient.
        for i in range(0,len(leaderboard_data)):
            for j in range(0,len(leaderboard_data) - 1 - i):
                if leaderboard_data[j]["bank"] + leaderboard_data[j]["cash"] > leaderboard_data[j + 1]["bank"] + leaderboard_data[j + 1]["cash"]:
                    leaderboard_data[j],leaderboard_data[j+1] = leaderboard_data[j+1],leaderboard_data[j]

        leaderboard_data.reverse()

        response = discord.Embed(title="Crajy Leaderboard", description="")
        for i in leaderboard_data:
            person = ctx.guild.get_member(i['user'])
            with suppress(AttributeError):
                response.add_field(name=f"{leaderboard_data.index(i)+1}. {person.nick if person.nick is not None else person.name}", value=f"Balance {i['bank'] + i['cash']}", inline=False)
        return await ctx.send(embed=response)

    @commands.command(name="get-loan", aliases=["gl"])    
    async def loan(self,ctx,loan_val:int):
        
        user_data = self.bot.economy_collection.find_one({'user': ctx.author.id})
        if loan_val < user_data['bank'] * 2 and user_data["debt"] == 0:
            response = discord.Embed(title=str(ctx.message.author), description=f"You took a loan of {loan_val}!", colour=discord.Colour.red()) 

            user_data['debt'] += (loan_val + int(loan_val * 0.05))
            user_data['bank'] += loan_val
            
            self.bot.economy_collection.update_one({'user': ctx.author.id}, {"$set":user_data})              
            await ctx.send(embed=response)

            await asyncio.sleep(64800)           
                                   #checks if debt has been repaid, if not sends reminder
                                   #Search for a better option than asyncio.sleep

            user_data = self.bot.economy_collection.find_one({'user': ctx.author.id})
            if user_data['debt'] != 0:                      
                await ctx.message.author.send("You're about to default on your loan")
            else:
                return
            
            await asyncio.sleep(21600)

            user_data = self.bot.economy_collection.find_one({'user': ctx.author.id})
            if user_data['debt'] != 0:
                user_data['debt'] = 0
                user_data['cash'] -= (loan_val + int(loan_val * 0.1))
                self.bot.economy_collection.update_one({'user': ctx.author.id}, {"$set": user_data})
                await ctx.message.author.send(f"poopi you messed up big time")
        else:
            await ctx.message.channel.send("You cannot take a loan greater than twice your current balance / you have an unpaid loan, repay it and try again.")


    @commands.command(name="repay-loan", aliases=["rl"])
    async def repay_loan(self, ctx):
        user_data = self.bot.economy_collection.find_one({'user': ctx.author.id})
        if user_data['debt'] > 0:
            if user_data['cash'] >= user_data['debt']:
                user_data['cash'] -= user_data['debt']
                user_data['debt'] = 0
                self.bot.economy_collection.update_one({'user': ctx.author.id},{"$set": user_data})
                response = discord.Embed(title=ctx.author.id, description=f"You've paid off your debt!", colour=discord.Color.green())
                return await ctx.send(embed=response)
            else:
                return await ctx.send(f"You do not have enough balance to repay your debt.")

        else:
            return await ctx.send(f"You do not have any debt")

    @commands.command(name="inventory", aliases=["inv"])
    async def inventory(self, ctx, user: typing.Union[discord.Member, str]=None):
        if user is None: user = ctx.author
        user_data = self.get_user_dict(ctx, user)
        response = discord.Embed(title=str(user), description="Inventory")
        for k in user_data['inv']:
            response.add_field(name=k, value=user_data['inv'][k], inline=False)
        return await ctx.send(embed=response)

    @commands.command(name='shop')
    async def shop(self, ctx):
        shop_data = self.bot.store_collection.find()
        response = discord.Embed(title="Shop", description="All available items")

        for i in shop_data:
            response.add_field(name=i['name'], value=f"Price : {i['price']} | Remaining Stock : {i['stock']}", inline=False)

        return await ctx.send(embed=response)

    @commands.command(name="buy")                        #IMPORTANT!! - For items that should have unlimited stock, use stock value as None in store_data collection.
    async def buy(self, ctx, number: int, *, item: str):         
        store_data = self.bot.store_collection.find_one({'name': item.lower().capitalize()})
        user_data = self.bot.economy_collection.find_one({'user': ctx.author.id})

        if user_data['cash'] >= (number * store_data['price']):
            if store_data['stock'] is not None:
                if store_data['stock'] >= number:
                    user_data['cash'] -= (number * store_data['price'])
                    store_data['stock'] -= number
                    self.bot.store_collection.update_one({'name': item.lower().capitalize()}, {"$set": store_data})
                    try:
                        user_data["inv"][item.lower()] += number
                    except KeyError:
                        user_data["inv"][item.lower()] = number
                    self.bot.economy_collection.update_one({'user': ctx.author.id}, {"$set": user_data})
                    response = discord.Embed(title=str(ctx.author), description=f"You bought {number} {item}s!", colour=discord.Color.green())      
                    return await ctx.send(embed=response)
                else:
                    return await ctx.message.channel.send(f"Bruh not enough stock of this item is left.")
            else:
                user_data['cash'] -= (number * store_data['price'])
                try:
                    user_data["inv"][item.lower()] += number
                except KeyError:
                    user_data["inv"][item.lower()] = number
                self.bot.economy_collection.update_one({'user': ctx.author.id}, {"$set": user_data})
                response = discord.Embed(title=str(ctx.author), description=f"You bought {number} {item}s!", colour=discord.Color.green())
                return await ctx.send(embed=response)
        else:
            return await ctx.send(f"poopi you don't have enough moni {self.bot.get_emoji(703648812669075456)}")

    @commands.command(name="sell")
    async def sell(self, ctx, n:int, item:str):
        store = self.bot.store_collection.find_one({'name': item.lower().capitalize()})
        sell_data = self.bot.economy_collection.find_one({'user': ctx.author.id})
        
        sell_data["inv"][item.lower()] -= n
        sell_data['cash'] += (store['price'] * n)
        self.bot.economy_collection.update_one({'user': ctx.author.id}, {"$set": sell_data})

        response = discord.Embed(title=f"{str(ctx.message.author)}", description=f"You sold {n} {item}s for {store['price'] * n}")
        return await ctx.send(embed=response)

    @commands.command(name='givemoney')
    async def givemoney(self, ctx, person: typing.Union[discord.Member, str], amount: int):
        sender = self.bot.economy_collection.find_one({'user': ctx.author.id})
        reciever = self.get_user_dict(ctx, person)

        if isinstance(person, str):
            person = [member for member in ctx.guild.members if member.name.lower()==person.lower() or member.nick.lower()==person.lower()][0]
        
        if amount < 0:  
            response = discord.Embed(title='Money Transfer:', description="You can't send negative money, popi.")
            return await ctx.send(embed=response)
        else:
            if sender['cash'] >= amount:
                sender['cash'] -= amount
                reciever['cash'] += amount
                self.bot.economy_collection.update_one({'user': ctx.author.id}, {"$set": sender})
                self.bot.economy_collection.update_one({'user': person.id}, {"$set": reciever})
                response = discord.Embed(title='Money Transfer: ', description=f"{ctx.author.mention} transferred {int(amount)} to {person.mention}")
            else:
                response = discord.Embed(title='Money Transfer: ', description=f"You don't have enough money on hand.")
        return await ctx.send(embed=response)
                                 
    @commands.command(name="rob")
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def rob(self, ctx, person: typing.Union[discord.Member, str]):
        robber = self.bot.economy_collection.find_one({'user': ctx.author.id})
        victim = self.get_user_dict(ctx, person)

        if isinstance(person, str):
            try:
                for member in ctx.guild.members:
                    if person.lower() == member.name.lower():
                        person = member
                    else:
                        if member.nick is not None:
                            if person.lower() in member.nick.lower():
                                person = member
            except:
                await ctx.send("Person not found 😔")
                ctx.command.reset_cooldown(ctx)      #should fix issue of faulty cooldown trigger
                return
        
        if robber['inv']['heist tools'] > 0 and victim['cash'] > 10:
            robber["inv"]["heist tools"] -= 1
            win_chance = random.choice([True, True, True, False])
            win_percent = random.randint(50, 80)
            
            if win_chance is True:
                win_amount = int(victim['cash'] * (win_percent/100))
                victim['cash'] -= win_amount
                robber['cash'] += win_amount
                response = discord.Embed(title=str(ctx.author), description=f"You robbed {win_amount} from {str(person)}", colour=discord.Color.green())
                self.bot.economy_collection.update_one({'user': ctx.author.id}, {"$set": robber})
                self.bot.economy_collection.update_one({'user': person.id}, {"$set": victim})
                return await ctx.send(embed=response)
            else:
                fine_amount = random.randint(75, 200)
                robber['cash'] -= fine_amount
                self.bot.economy_collection.update_one({'user': ctx.author.id}, {"$set": robber})
                response = discord.Embed(title=str(ctx.message.author), description=f"You were caught robbing, and fined {fine_amount}", colour=discord.Color.red())
                return await ctx.send(embed=response)
        else:
            await ctx.message.channel.send("You do not have enough Heist tools items/ person doesn't have enough cash balance.")
            ctx.command.reset_cooldown(ctx)
                                 
    @rob.error
    async def rob_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            return await ctx.message.channel.send(f"Time remaining = {int(error.retry_after//60)} mins and {int(error.retry_after)-(int(error.retry_after//60))*60} seconds")
        ctx.command.reset_cooldown(ctx)
    
    @commands.command(name="use-item", aliases=["useitem"])
    async def use_item(self, ctx, item):
        user_data = self.bot.economy_collection.find_one({'user': ctx.author.id})
        store_data = self.bot.store_collection.find_one({'name': item})
        role_get = store_data['role']
        for i in user_data["inv"]:
            if item.lower() in i.keys():
                i[item.lower()] -= 1
        self.bot.economy_collection.update_one({'user': ctx.author.id},{"$set": user_data})
        
        if role_get != None:
            role = discord.utils.get(ctx.guild.roles, name = role_get)
            await ctx.author.add_roles(role)
            await ctx.send("Role added!")
        else: await ctx.send("This item does not give a role")
    
def setup(bot):
    bot.add_cog(Economy(bot))
