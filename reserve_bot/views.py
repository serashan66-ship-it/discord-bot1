import discord
import sqlite3
import datetime

def get_db():
    return sqlite3.connect("reserve.db")

# ==========================
# 状態取得
# ==========================
def get_status(time_label):

    conn = get_db()
    c = conn.cursor()
    today = str(datetime.date.today())

    c.execute(
        "SELECT user_id, locked FROM reservations WHERE date=? AND time=?",
        (today, time_label)
    )
    row = c.fetchone()
    conn.close()

    if not row:
        return "free", None

    user_id, locked = row

    if locked == 1:
        return "rest", None

    return "reserved", user_id


# ==========================
# Embed
# ==========================
def generate_embed(label, start, end, interval):

    current = start * 60
    end_min = end * 60

    total = 0
    reserved = 0
    lines = []

    while current <= end_min:
        h = current // 60
        m = current % 60
        time_label = f"{h:02}:{m:02}"

        status, user_id = get_status(time_label)

        total += 1

        if status == "free":
            line = f"`{time_label}` │ 🟢 空き"
        elif status == "rest":
            line = f"`{time_label}` │ ❌ 休憩"
        else:
            reserved += 1
            line = f"`{time_label}` │ 🔴 <@{user_id}>"

        lines.append(line)
        current += interval

    return discord.Embed(
        title=f"{label} ({reserved}/{total})",
        description="\n".join(lines),
        color=discord.Color.green()
    )


# ==========================
# 予約ボタン
# ==========================
class ReserveButton(discord.ui.Button):
    def __init__(self, time_label, room_view):
        super().__init__(label=time_label)
        self.time_label = time_label
        self.room_view = room_view

    async def callback(self, interaction: discord.Interaction):

        await interaction.response.defer(ephemeral=True)

        conn = get_db()
        c = conn.cursor()
        today = str(datetime.date.today())

        status, user_id = get_status(self.time_label)
        is_admin = interaction.user.guild_permissions.manage_guild
        rest_mode = self.room_view.rest_mode

        if is_admin and rest_mode:

            if status == "rest":
                c.execute("DELETE FROM reservations WHERE date=? AND time=?",
                          (today, self.time_label))
            else:
                c.execute("INSERT OR REPLACE INTO reservations VALUES (?, ?, NULL, 1, 0)",
                          (today, self.time_label))

        else:
            if status == "free":
                c.execute("INSERT INTO reservations VALUES (?, ?, ?, 0, 0)",
                          (today, self.time_label, interaction.user.id))

            elif status == "reserved":

                if user_id == interaction.user.id:
                    c.execute("DELETE FROM reservations WHERE date=? AND time=?",
                              (today, self.time_label))
                else:
                    await interaction.followup.send("🔒 他の人が予約しています", ephemeral=True)
                    conn.close()
                    return

            elif status == "rest":
                await interaction.followup.send("❌ 休憩中", ephemeral=True)
                conn.close()
                return

        conn.commit()
        conn.close()

        self.room_view.refresh()

        embed = generate_embed(
            self.room_view.label,
            self.room_view.start,
            self.room_view.end,
            self.room_view.interval
        )

        await interaction.followup.edit_message(
            interaction.message.id,
            embed=embed,
            view=self.room_view
        )


# ==========================
# 休憩ボタン
# ==========================
class RestToggleButton(discord.ui.Button):
    def __init__(self, room_view):
        super().__init__(label="休憩モード OFF", style=discord.ButtonStyle.secondary, row=0)
        self.room_view = room_view

    async def callback(self, interaction: discord.Interaction):

        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("管理者のみ", ephemeral=True)
            return

        self.room_view.rest_mode = not self.room_view.rest_mode
        self.label = "休憩モード ON" if self.room_view.rest_mode else "休憩モード OFF"

        await interaction.response.edit_message(view=self.room_view)


# ==========================
# View
# ==========================
class RoomView(discord.ui.View):
    def __init__(self, start, end, interval, label):
        super().__init__(timeout=None)

        self.start = start
        self.end = end
        self.interval = interval
        self.label = label
        self.rest_mode = False

        self.refresh()

    def refresh(self):

        self.clear_items()

        # 休憩ボタン
        self.add_item(RestToggleButton(self))

        current = self.start * 60
        end_min = self.end * 60

        row = 1
        count = 0

        while current <= end_min:

            if row >= 5:
                break

            h = current // 60
            m = current % 60
            time_label = f"{h:02}:{m:02}"

            button = ReserveButton(time_label, self)

            status, _ = get_status(time_label)

            if status == "free":
                button.style = discord.ButtonStyle.success
            elif status == "rest":
                button.style = discord.ButtonStyle.secondary
            else:
                button.style = discord.ButtonStyle.danger

            button.row = row
            self.add_item(button)

            count += 1
            if count % 5 == 0:
                row += 1

            current += self.interval


# ==========================
# ConfirmView
# ==========================
class ConfirmView(discord.ui.View):
    def __init__(self, start, end, interval, label):
        super().__init__(timeout=120)
        self.start = start
        self.end = end
        self.interval = interval
        self.label = label
        self.everyone = False

    @discord.ui.button(label="@everyone OFF", style=discord.ButtonStyle.secondary)
    async def toggle(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.everyone = not self.everyone
        button.label = "@everyone ON" if self.everyone else "@everyone OFF"
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="作成する", style=discord.ButtonStyle.success)
    async def create(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.defer()

        view = RoomView(self.start, self.end, self.interval, self.label)
        embed = generate_embed(self.label, self.start, self.end, self.interval)

        if self.everyone:
            await interaction.followup.edit_message(
                interaction.message.id,
                content="@everyone",
                embed=embed,
                view=view,
                allowed_mentions=discord.AllowedMentions(everyone=True)
            )
        else:
            await interaction.followup.edit_message(
                interaction.message.id,
                embed=embed,
                view=view
            )