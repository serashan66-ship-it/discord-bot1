import discord
from discord.ext import commands, tasks
import sqlite3
import datetime
from views import ConfirmView

TOKEN = "MTQ3NTMyNjEzMTg5NjA2MjA3NQ.GwXGpe.M7YApdj8qLthtIjlwGdzuYbqkYO-D6pKVEqsSY"
GUILD_ID = 1451538817889730581  # サーバーID

# ==========================
# Intent設定
# ==========================
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)


# ==========================
# DB
# ==========================
def get_db():
    return sqlite3.connect("reserve.db")


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS reservations (
        date TEXT,
        time TEXT,
        user_id INTEGER,
        locked INTEGER DEFAULT 0,
        notified INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()


# ==========================
# 起動時
# ==========================
@bot.event
async def on_ready():
    init_db()

    guild = discord.Object(id=GUILD_ID)
    await bot.tree.sync(guild=guild)

    print(f"ログイン成功: {bot.user}")

    if not reservation_watcher.is_running():
        reservation_watcher.start()


# ==========================
# 予約作成
# ==========================
@bot.tree.command(
    name="reserve",
    description="予約表を作成",
    guild=discord.Object(id=GUILD_ID)
)
async def reserve(interaction: discord.Interaction,
                  start: int,
                  end: int,
                  interval: int,
                  label: str):

    view = ConfirmView(start, end, interval, label)
    await interaction.response.send_message(
        "予約表を作成しますか？",
        view=view
    )


# ==========================
# 👑 管理者：当日全削除
# ==========================
@bot.tree.command(
    name="clear_all",
    description="当日の予約を全削除",
    guild=discord.Object(id=GUILD_ID)
)
async def clear_all(interaction: discord.Interaction):

    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message("管理者のみ使用可能", ephemeral=True)
        return

    today = str(datetime.date.today())

    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM reservations WHERE date=?", (today,))
    conn.commit()
    conn.close()

    await interaction.response.send_message("✅ 当日の予約を全削除しました")


# ==========================
# 👑 管理者：時間削除
# ==========================
@bot.tree.command(
    name="delete_time",
    description="指定時間の予約を削除",
    guild=discord.Object(id=GUILD_ID)
)
async def delete_time(interaction: discord.Interaction, time: str):

    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message("管理者のみ使用可能", ephemeral=True)
        return

    today = str(datetime.date.today())

    conn = get_db()
    c = conn.cursor()
    c.execute(
        "DELETE FROM reservations WHERE date=? AND time=?",
        (today, time)
    )
    conn.commit()
    conn.close()

    await interaction.response.send_message(f"✅ {time} の予約を削除しました")


# ==========================
# ⏰ 通知 & 日付リセット
# ==========================
@tasks.loop(minutes=1)
async def reservation_watcher():

    now = datetime.datetime.now()
    today = str(now.date())
    current_time = now.strftime("%H:%M")

    conn = get_db()
    c = conn.cursor()

    # 前日データ削除（自動リセット）
    c.execute("DELETE FROM reservations WHERE date < ?", (today,))

    c.execute("""
        SELECT time, user_id, notified
        FROM reservations
        WHERE date=? AND locked=0
    """, (today,))

    rows = c.fetchall()

    for time_label, user_id, notified in rows:
        if time_label == current_time and notified == 0:
            user = bot.get_user(user_id)
            if user:
                try:
                    await user.send(f"⏰ {time_label} の予約時間です！")
                except:
                    pass

            c.execute("""
                UPDATE reservations
                SET notified=1
                WHERE date=? AND time=?
            """, (today, time_label))

    conn.commit()
    conn.close()


bot.run(TOKEN)