from discord.ext import tasks
from datetime import datetime, timedelta
import database
from config import VC_NAME
import discord

def setup_scheduler(bot):

    @tasks.loop(minutes=1)
    async def notify():

        now = datetime.now()
        before5 = (now + timedelta(minutes=5)).strftime("%H:%M")
        current = now.strftime("%H:%M")

        for time, user_id in database.get_all():

            # 5分前DM
            if time == before5:
                user = await bot.fetch_user(int(user_id))
                try:
                    await user.send(f"【5分前通知】{time} の予約です！")
                except:
                    pass

            # VC移動
            if time == current:
                for guild in bot.guilds:
                    vc = discord.utils.get(guild.voice_channels, name=VC_NAME)
                    member = guild.get_member(int(user_id))
                    if vc and member:
                        try:
                            await member.move_to(vc)
                        except:
                            pass

    notify.start()