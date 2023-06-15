import asyncio

import disnake
import requests
from disnake.ext import commands, tasks

from main import bot


class Currency(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.currency_emojis = {
            'AUD': '\U0001F1E6\U0001F1FA',  # Australia flag emoji
            'CAD': '\U0001F1E8\U0001F1E6',  # Canada flag emoji
            'CNY': '\U0001F1E8\U0001F1F3',  # China flag emoji
            'CZK': '\U0001F1E8\U0001F1FF',  # Czech Republic flag emoji
            'DKK': '\U0001F1E9\U0001F1F0',  # Denmark flag emoji
            'HKD': '\U0001F1ED\U0001F1F0',  # Hong Kong flag emoji
            'HUF': '\U0001F1ED\U0001F1FA',  # Hungary flag emoji
            'INR': '\U0001F1EE\U0001F1F3',  # India flag emoji
            'IDR': '\U0001F1EE\U0001F1E9',  # Indonesia flag emoji
            'ILS': '\U0001F1EE\U0001F1F1',  # Israel flag emoji
            'JPY': '\U0001F1EF\U0001F1F5',  # Japan flag emoji
            'KZT': '\U0001F1F0\U0001F1FF',  # Kazakhstan flag emoji
            'KRW': '\U0001F1F0\U0001F1F7',  # South Korea flag emoji
            'MXN': '\U0001F1F2\U0001F1FD',  # Mexico flag emoji
            'MDL': '\U0001F1F2\U0001F1E9',  # Moldova flag emoji
            'NZD': '\U0001F1F3\U0001F1FF',  # New Zealand flag emoji
            'NOK': '\U0001F1F3\U0001F1F4',  # Norway flag emoji
            'RUB': 'none',  # Russia flag emoji
            'SGD': '\U0001F1F8\U0001F1EC',  # Singapore flag emoji
            'ZAR': '\U0001F1FF\U0001F1E6',  # South Africa flag emoji
            'SEK': '\U0001F1F8\U0001F1EA',  # Sweden flag emoji
            'CHF': '\U0001F1E8\U0001F1ED',  # Switzerland flag emoji
            'EGP': '\U0001F1EA\U0001F1EC',  # Egypt flag emoji
            'GBP': '\U0001F1EC\U0001F1E7',  # United Kingdom flag emoji
            'USD': '\U0001F1FA\U0001F1F8',  # United States flag emoji
        }
        self.send_currency.start()  # Start the task

    def cog_unload(self):
        self.send_currency.cancel()  # Cancel the task when the cog is unloaded

    @tasks.loop(hours=12)
    async def send_currency(self):
        channel = disnake.utils.get(self.bot.get_all_channels(), name="currency")
        if channel:
            url = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json"
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception for non-2xx status codes
            data = response.json()

            # Extract 'txt', 'cc', 'rate', and 'exchangedate' values from the JSON data
            extracted_data = []
            for item in data:
                txt = item.get('txt', '')
                cc = item.get('cc', '')
                rate = item.get('rate', '')
                dateE = item.get('exchangedate', '')
                extracted_data.append({'txt': txt, 'cc': cc, 'rate': rate, 'exchangedate': dateE})

            # Create an embedded message with the extracted data and emojis
            embed = disnake.Embed(title="Currency Exchange Rates to UAH 🇺🇦", description=f"Latest rates ({dateE}):")
            for item in extracted_data:
                cc = item['cc']
                emoji = self.currency_emojis.get(cc, '')  # Get the corresponding emoji for the currency code
                value = f"{emoji} `{cc}`\n{item['txt']}: `{item['rate']}`"
                embed.add_field(name='\u200b', value=value, inline=False)
            print(f"{bot.user.name}: I drop currency to channel: {channel} (class: Currency).")
            await channel.send(embed=embed)
        else:
            print("Channel not found.")

    @send_currency.before_loop
    async def before_send_currency(self):
        await self.bot.wait_until_ready()  # Wait until the bot is ready before starting the task


def setup(bot):
    bot.add_cog(Currency(bot))
