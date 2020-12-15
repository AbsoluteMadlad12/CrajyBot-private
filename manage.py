from utils.menu import Menu
from secret.TOKEN import TOKEN

def setup() -> None:
    guild_id = int(input("Enter your Guild ID:"))
    announce_channel = int(input("Enter channel ID where the bot is allowed to announce things:"))
    test_channel = int(input("Enter ID of the channel where bot testing will be done:"))
    general = int(input("Enter general chat ID:"))
    bot_commander_roles = []
    check = "y"
    print()
    while check == "y":
        i = int(input("Enter the ID of role that can control the bot: "))
        bot_commander_roles.append(i)
        check = input("Enter more roles? (y/n): ")
    chat_money_channels = []
    check = "y"
    print()
    while check == "y":
        i = int(input("Enter the ID of a channel where users will be allowed to earn currency for chatting: "))
        chat_money_channels.append(i)
        check = input("Enter more channels? (y/n): ")

    with open(".\secret\constants_test.py", "w+") as f:
        data = f"GUILD_ID = {guild_id}\nBOT_ANNOUNCE_CHANNEL = {announce_channel}\nBOT_TEST_CHANNEL = {test_channel}\nGENERAL_CHAT = {general}\nBOT_COMMANDER_ROLES = {bot_commander_roles}\nCHAT_MONEY_CHANNELS = {chat_money_channels}\nDEFAULT_COGS = ['economy', 'betting', 'moderator', 'stupid', 'notes']"
        f.write(data)

    print("Constants set up.")

    with open(".\secret\KEY.py", "w") as f:
        data = input("Enter your RapidAPI key: ")
        f.write(f"KEY = {data}")

    print("API key set up.")

    with open(".\secret\TOKEN.py", "w") as f:
        data = input("Enter your bot token: ")
        f.write(f"TOKEN = {data}")

    print("Bot token set up.")

def debug():
    print("DEBUG MODE")
    print("Enter the name of the cog that you want to load. The name must match the filename.")
    print("For example; to load `cogs/amongus.py` - enter `amongus`.")
    print("If you want to load multiple cogs, enter their names separated by spaces. For example; `amongus economy`.")
    func = lambda x: f"cogs.{x}"
    cogs = list(map(func, input().split()))
    from bot import bot 
    from secret.constants import BOT_TEST_CHANNEL

    @bot.event
    async def on_ready(): # sends this message when bot starts working in #bot-tests
        await bot.get_channel(BOT_TEST_CHANNEL).send(f"Bot running in debug mode! Cogs loaded - {', '.join(cogs)}, jishaku.")
        print(f"Bot running in debug mode! Cogs loaded - {', '.join(cogs)}, jishaku.")

    for cog in cogs:
        bot.load_extension(cog)
    else:
        bot.load_extension("jishaku")
    bot.run(TOKEN)

def run():
    from bot import bot
    from secret.constants import DEFAULT_COGS
    #loading cogs
    if DEFAULT_COGS == []:
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                bot.load_extension(f'cogs.{filename[:-3]}')
        bot.load_extension('jishaku')
    else:
        for cog in DEFAULT_COGS:
            bot.load_extension(f'cogs.{cog}')
    bot.run(TOKEN)


if __name__ == "__main__":
    functions = [setup, run, debug]
    menu = Menu(*functions, heading="Bot Control", format_symbol="=", continue_prompt=False)
    menu.run()