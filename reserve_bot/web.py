from flask import Flask, render_template_string, request, redirect, make_response
import sqlite3
import datetime

app = Flask(__name__)

ADMIN_KEY = "3024"

BOT_INVITE_URL = "https://discord.com/oauth2/authorize?client_id=1475326131896062075&permissions=2147485728&integration_type=0&scope=bot+applications.commands"

# ================= DB =================
def get_db():
    return sqlite3.connect("reserve.db")

def today():
    return str(datetime.date.today())

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

def get_reservations():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT time, user_id, locked
        FROM reservations
        WHERE date=?
        ORDER BY time
    """, (today(),))
    data = c.fetchall()
    conn.close()
    return data

def delete_time(time):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM reservations WHERE date=? AND time=?", (today(), time))
    conn.commit()
    conn.close()

# ================= UI =================
HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>予約管理</title>

<style>

body {
    margin:0;
    font-family: Arial;
    background:#0f172a;
    color:white;
    display:flex;
}

/* ===== サイドバー ===== */
.sidebar {
    width:220px;
    height:100vh;
    background:#020617;
    padding-top:20px;
}

/* ===== モバイル ===== */
@media (max-width:768px) {
.sidebar {
    width:100%;
    height:auto;
    display:flex;
    flex-wrap:wrap;
}
.content {
    margin-left:0 !important;
}
}

.sidebar button {
    width:100%;
    padding:15px;
    border:none;
    background:none;
    color:white;
    text-align:left;
    cursor:pointer;
}

.sidebar button:hover {
    background:#1e293b;
}

.content {
    margin-left:220px;
    padding:20px;
    width:100%;
}

.card {
    background:#1e293b;
    padding:20px;
    margin-bottom:20px;
    border-radius:12px;
}

.time {
    padding:12px;
    margin:5px 0;
    border-radius:8px;
    font-weight:bold;
    display:flex;
    justify-content:space-between;
}

.free { background:#22c55e; }
.busy { background:#ef4444; }
.rest { background:#64748b; }

.button {
    background:#3b82f6;
    padding:10px;
    border-radius:10px;
    color:white;
    text-decoration:none;
    border:none;
    cursor:pointer;
}

.delete {
    background:#ef4444;
    border:none;
    padding:5px 10px;
    border-radius:6px;
    color:white;
}

.tab { display:none; }

</style>

<script>
function showTab(id){
    document.querySelectorAll('.tab').forEach(t=>t.style.display='none');
    document.getElementById(id).style.display='block';
}
</script>

</head>

<body onload="showTab('home')">

<div class="sidebar">
<button onclick="showTab('home')">🏠 ホーム</button>
<button onclick="showTab('today')">📅 今日の予約</button>
<button onclick="showTab('bot')">🤖 Bot導入</button>
<button onclick="showTab('commands')">📖 コマンド</button>
<button onclick="showTab('admin')">🔐 管理</button>
</div>

<div class="content">

<div id="home" class="tab card">
<h2>予約管理システム</h2>
<p>スマホ対応しました 👍</p>
</div>

<div id="today" class="tab card">
<h2>📅 今日の予約</h2>

{% for time, user_id, locked in data %}

<form method="post">

{% if locked == 1 %}
<div class="time rest">{{time}} - 休憩</div>

{% elif user_id %}
<div class="time busy">
<span>{{time}} - 予約済</span>
{% if admin %}
<button class="delete" name="delete" value="{{time}}">削除</button>
{% endif %}
</div>

{% else %}
<div class="time free">{{time}} - 空き</div>
{% endif %}

</form>

{% endfor %}
</div>

<div id="bot" class="tab card">
<h2>🤖 Bot導入</h2>
<a class="button" href="{{invite}}" target="_blank">導入する</a>
</div>

<div id="commands" class="tab card">
<h2>📖 コマンド</h2>
<p>/reserve → 予約作成</p>
<p>/clear_all → 全削除</p>
<p>/delete_time → 時間削除</p>
</div>

<div id="admin" class="tab card">
<h2>🔐 管理者ログイン</h2>
<form method="post">
<input type="password" name="key">
<button class="button">ログイン</button>
</form>
</div>

</div>
</body>
</html>
"""

@app.route("/", methods=["GET","POST"])
def index():
    init_db()
    admin = request.cookies.get("admin") == "true"

    if request.method=="POST":
        if "key" in request.form:
            if request.form["key"] == ADMIN_KEY:
                resp = make_response(redirect("/"))
                resp.set_cookie("admin","true", max_age=86400)
                return resp

        if "delete" in request.form and admin:
            delete_time(request.form["delete"])
            return redirect("/")

    data=get_reservations()
    return render_template_string(HTML,data=data,invite=BOT_INVITE_URL,admin=admin)

app.run(host="0.0.0.0", port=5000)