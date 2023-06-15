import disnake
from disnake.ext import commands
import sqlite3
import datetime


class WelcomeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.welcome_channel_id = 1116823058129354774

    @commands.Cog.listener()
    async def on_member_join(self, member):
        welcome_channel = self.bot.get_channel(self.welcome_channel_id)

        embed = disnake.Embed(
            title=f'Ласкаво просимо на сервер, {member.name}!',color=0xE28CC0
        )
        embed.set_thumbnail(url=member.avatar.url)
        await welcome_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        welcome_channel = self.bot.get_channel(self.welcome_channel_id)

        embed = disnake.Embed(
            title=f'{member.name} покинув(-ла) сервер.',
            color=0xE28CC0
        )
        embed.set_thumbnail(url=member.avatar.url)
        await welcome_channel.send(embed=embed)


def setup(bot):
    bot.add_cog(WelcomeCog(bot))
