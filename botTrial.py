"""
Horoscopebot
insert further documentation here

"""
import os
import discord

token_ = "NzA5NDA3MjY4NDg3MDM3MDE5.XrllLQ.FbL2vivvNxjxPT-wOfAvH32fK4QZ"
token = token_[:len(token_)-1]

client =  discord.Client()

@client.event
async def on_message(message):
    if message.content == "popi" or "Popi":
        await message.channel.send("poopi do be lookin poopie")


client.run(token)


