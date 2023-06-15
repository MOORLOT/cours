import disnake
from disnake.ext import commands


class Clear(commands.Cog):
    def init(self, bot):
        self.bot = bot

    @commands.slash_command(description='Очищення чату на вказану кількість повідомлень')
    async def clear(self, interaction, amount: int):
        avatar_url = interaction.bot.user.avatar.url

        embed = disnake.Embed(title="Clear", description=f"Deleted {amount} messages", color=0xDB8CBA)
        embed.set_author(name=interaction.bot.user.name, icon_url=avatar_url)

        await interaction.response.send_message(embed=embed, ephemeral=True)
        await interaction.channel.purge(limit=amount + 1)


def setup(bot):
    bot.add_cog(Clear(bot))
