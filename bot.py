import discord
from discord.ext import commands
import sqlite3

# Inisialisasi bot dengan intents
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)
DB_FILE = 'market_bot.db'

# Harga item di shop (inisialisasi global)
shop_items = {
    "Sword": 100,
    "Shield": 50,
    "Potion": 25,
    "Wood": 10,
    "Stone": 15,
    "Iron": 50,
    "Gold": 100,
}

# Fungsi koneksi database
def connect_db():
    try:
        return sqlite3.connect(DB_FILE)
    except sqlite3.Error as e:
        print(f"Error database connection: {e}")
        return None

# Inisialisasi database
def init_db():
    conn = connect_db()
    if conn:
        try:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS gold_balance (
                        user_id INTEGER PRIMARY KEY,
                        balance INTEGER DEFAULT 0)''')
            c.execute('''CREATE TABLE IF NOT EXISTS warehouse (
                        user_id INTEGER,
                        item_name TEXT,
                        item_type TEXT,
                        amount INTEGER,
                        item_id INTEGER,
                        PRIMARY KEY (user_id, item_id))''')
            c.execute('''CREATE TABLE IF NOT EXISTS items (
                        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        item_name TEXT,
                        item_type TEXT)''')
            conn.commit()
        except sqlite3.Error as e:
            print(f"Error initializing database: {e}")
        finally:
            if conn:
                conn.close()

# Fungsi mendapatkan saldo emas
def get_gold_balance(user_id: int) -> int:
    conn = connect_db()
    if conn:
        try:
            c = conn.cursor()
            c.execute('SELECT balance FROM gold_balance WHERE user_id = ?', (user_id,))
            result = c.fetchone()
            return result[0] if result else 0
        except sqlite3.Error as e:
            print(f"Error getting gold balance: {e}")
            return 0
        finally:
            if conn:
                conn.close()
    return 0

# Fungsi memperbarui saldo emas
def set_gold_balance(user_id: int, balance: int) -> None:
    conn = connect_db()
    if conn:
        try:
            c = conn.cursor()
            c.execute('INSERT OR REPLACE INTO gold_balance (user_id, balance) VALUES (?, ?)', (user_id, balance))
            conn.commit()
        except sqlite3.Error as e:
            print(f"Error setting gold balance: {e}")
        finally:
            if conn:
                conn.close()

# Fungsi mendapatkan item dari gudang
def get_warehouse_items(user_id: int) -> list:
    conn = connect_db()
    if conn:
        try:
            c = conn.cursor()
            c.execute('SELECT item_name, item_type, amount, item_id FROM warehouse WHERE user_id = ?', (user_id,))
            return c.fetchall()
        except sqlite3.Error as e:
            print(f"Error getting warehouse items: {e}")
            return []
        finally:
            if conn:
                conn.close()
    return []

# Fungsi menambahkan item ke gudang
def add_warehouse_item(user_id: int, item_name: str, item_type: str, amount: int, item_id: int) -> None:
    conn = connect_db()
    if conn:
        try:
            c = conn.cursor()
            c.execute('INSERT OR REPLACE INTO warehouse (user_id, item_name, item_type, amount, item_id) VALUES (?, ?, ?, ?, ?)', (user_id, item_name, item_type, amount, item_id))
            conn.commit()
        except sqlite3.Error as e:
            print(f"Error adding warehouse item: {e}")
        finally:
            if conn:
                conn.close()

# Fungsi mendapatkan daftar item
def get_item_list() -> list:
    conn = connect_db()
    if conn:
        try:
            c = conn.cursor()
            c.execute('SELECT item_id, item_name, item_type FROM items')
            return c.fetchall()
        except sqlite3.Error as e:
            print(f"Error getting item list: {e}")
            return []
        finally:
            if conn:
                conn.close()
    return []

# Fungsi menambahkan item ke daftar item
def add_item_to_list(item_name: str, item_type: str) -> None:
    conn = connect_db()
    if conn:
        try:
            c = conn.cursor()
            c.execute('INSERT INTO items (item_name, item_type) VALUES (?, ?)', (item_name, item_type))
            conn.commit()
        except sqlite3.Error as e:
            print(f"Error adding item to list: {e}")
        finally:
            if conn:
                conn.close()

# Fungsi menghapus item dari daftar item
def delete_item_from_list(item_id: int) -> None:
    conn = connect_db()
    if conn:
        try:
            c = conn.cursor()
            c.execute('DELETE FROM items WHERE item_id = ?', (item_id,))
            conn.commit()
        except sqlite3.Error as e:
            print(f"Error deleting item from list: {e}")
        finally:
            if conn:
                conn.close()

# Event ketika bot siap
@bot.event
async def on_ready():
    init_db()
    print(f'✅ Logged in as {bot.user}')

# Perintah untuk menampilkan saldo emas pengguna
@bot.command()
async def gold(ctx):
    balance = get_gold_balance(ctx.author.id)
    await ctx.send(f" {ctx.author.mention}, saldo emas Anda: {balance} gold.")

# Perintah untuk menambahkan emas dengan password
@bot.command()
async def add_gold(ctx, password: str, member: discord.Member, amount: int):
    if password != "LMAO":
        await ctx.send("⛔ Password salah!")
        return

    balance = get_gold_balance(member.id)
    set_gold_balance(member.id, balance + amount)
    await ctx.send(f"✅ {ctx.author.mention} menambahkan {amount} gold ke {member.mention}. Total saldo {member.mention}: {balance + amount} gold.")

# Perintah untuk menampilkan shop
@bot.command()
async def shop(ctx):
    items = get_item_list()
    if not items:
        await ctx.send(" Daftar item kosong! Tidak ada item yang bisa dijual.")
        return
    shop_list = "\n".join([f" {item[1]}: {shop_items.get(item[1], 0)} Gold" for item in items if item[1] in shop_items])
    await ctx.send(f"**️ Shop Items:**\n{shop_list}\n\nGunakan `!buy <jumlah> <item>` untuk transaksi!")

# Perintah untuk membeli barang di shop
@bot.command()
async def buy(ctx, amount: int, *, item: str):
    item = item.capitalize()
    items = [i[1] for i in get_item_list()]
    item_id = None
    for i in get_item_list():
        if i[1] == item:
            item_id = i[0]
    if item not in items:
        await ctx.send("❌ Item ini tidak tersedia!")
        return
    if item not in shop_items:
        await ctx.send("❌ Item ini tidak dijual di shop!")
        return
    if amount <= 0:
        await ctx.send("❌ Jumlah item harus lebih dari 0!")
        return

    balance = get_gold_balance(ctx.author.id)
    trade_cost = amount * shop_items[item]

    if balance < trade_cost:
        await ctx.send("❌ Saldo emas tidak cukup untuk membeli item ini!")
        return

    set_gold_balance(ctx.author.id, balance - trade_cost)
    add_warehouse_item(ctx.author.id, item, "Shop Item", amount, item_id)
    await ctx.send(f" {ctx.author.mention} membeli {amount} {item} dari bot seharga {trade_cost} gold! Sisa saldo: {balance - trade_cost} gold. Item ditambahkan ke gudang Anda.")

# Perintah untuk menjual barang ke bot
@bot.command()
async def sell(ctx, amount: int, *, item: str):
    item = item.capitalize()
    items = [i[1] for i in get_item_list()]
    item_id = None
    for i in get_item_list():
        if i[1] == item:
            item_id = i[0]
    if item not in items:
        await ctx.send("❌ Item ini tidak tersedia!")
        return
    if item not in shop_items:
        await ctx.send("❌ Item ini tidak dibeli oleh bot!")
        return
    if amount <= 0:
        await ctx.send("❌ Jumlah item harus lebih dari 0!")
        return

    balance = get_gold_balance(ctx.author.id)
    trade_price = amount * shop_items[item]
    set_gold_balance(ctx.author.id, balance + trade_price)

    await ctx.send(f" {ctx.author.mention} menjual {amount} {item} ke bot dan menerima {trade_price} gold! Sisa saldo: {balance + trade_price} gold.")

# Perintah untuk trade antar pengguna (jual/beli tanpa inventaris)
@bot.command()
async def trade(ctx, member: discord.Member, item: str = None, amount: int = None):
    items = [i[1] for i in get_item_list()]
    item_id = None
    for i in get_item_list():
        if i[1] == item:
            item_id = i[0]
    if ctx.author == member:
        await ctx.send("⛔ Anda tidak bisa trade dengan diri sendiri!")
        return
    if item and item not in items:
        await ctx.send("❌ Item ini tidak tersedia!")
        return
    if item and amount and amount <= 0:
        await ctx.send("❌ Jumlah item harus lebih dari 0!")
        return
    if not item and not amount:
        await ctx.send(f"{member.mention}, {ctx.author.mention} ingin trade dengan Anda. Apakah Anda setuju? (Y/N)")

        def check(m):
            return m.author == member and m.channel == ctx.channel and m.content.upper() == 'Y'

        try:
            await bot.wait_for('message', check=check, timeout=30.0)
            await ctx.send(f"Draft Trade:\n{ctx.author.mention}:\n-\n{member.mention}:\n-")
        except TimeoutError:
            await ctx.send("Trade dibatalkan.")
            return

    elif item and amount:
        add_warehouse_item(member.id, item, "Trade Item", amount, item_id)
        await ctx.send(f" {ctx.author.mention} menawarkan item {item} sejumlah {amount} ke {member.mention}.")
    else:
        await ctx.send("Format penambahan item salah. Contoh: !12 - 34")

# Perintah untuk menghapus item dari daftar item (admin only)
@bot.command()
async def delete_item(ctx, password: str, item_id: int):
    if password != "JK":
        await ctx.send("⛔ Password salah!")
        return

    delete_item_from_list(item_id)
    await ctx.send(f"✅ Item dengan ID {item_id} berhasil dihapus dari daftar item!")

# Perintah untuk menampilkan daftar item
@bot.command()
async def item_list(ctx):
    items = get_item_list()
    if not items:
        await ctx.send(" Daftar item kosong!")
        return
    item_list_str = "\n".join([f"ID: {item[0]}, Nama: {item[1]}, Tipe: {item[2]}" for item in items])
    await ctx.send(f"**Daftar Item:**\n{item_list_str}")

# Jalankan bot dengan token
bot.run('TOKEN')
