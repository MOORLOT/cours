import os
import disnake

from disnake.ext import commands

intents = disnake.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=">", intents=intents)


@bot.event
async def on_member_join(member):
    await member.send(
        f'Welcome to the server, {member.mention}! Enjoy your stay here.'
    )

@bot.event
async def on_ready():
    await bot.change_presence(activity=disnake.Game("PyCharm"))
    print(f"{bot.user.name}: I prepare to work.")


for filename in os.listdir("./cogs"):
    if filename.endswith(".py"):
        bot.load_extension(f"cogs.{filename[:-3]}")

bot.run("MTExNjcxODMzOTcxNzM0NTM2Mg.G0ZXd1.Gfhr8-f59N9ZkkUfp2-zRXCdh2kokF4CV1PVGI")
