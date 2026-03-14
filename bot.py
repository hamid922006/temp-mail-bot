import requests
import random
import re
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# ⚠️ আপনার নতুন টোকেন এখানে বসান (পুরনোটি ডিলিট করে দিন)
BOT_TOKEN = "8125617126:AAEG89OKzuYucnYo3-eWOhfZfza6mRJuI8o" 

# -----------------------------
# SQLite Database Setup
# -----------------------------
# ডাটাবেস তৈরি বা কানেক্ট করা
conn = sqlite3.connect("temp_mail.db", check_same_thread=False)
cursor = conn.cursor()

# ইউজারদের ডাটা সেভ করার জন্য টেবিল তৈরি
cursor.execute('''CREATE TABLE IF NOT EXISTS users
                  (user_id INTEGER PRIMARY KEY, email TEXT, token TEXT)''')
conn.commit()

def save_user(user_id, email, token):
    cursor.execute("REPLACE INTO users (user_id, email, token) VALUES (?, ?, ?)", (user_id, email, token))
    conn.commit()

def get_user(user_id):
    cursor.execute("SELECT email, token FROM users WHERE user_id = ?", (user_id,))
    return cursor.fetchone()

# -----------------------------
# Mail.tm API Functions
# -----------------------------
def create_email():
    try:
        domains = requests.get("https://api.mail.tm/domains", timeout=10).json()
        domain = domains["hydra:member"][0]["domain"]

        username = "user" + str(random.randint(100000, 999999))
        email = f"{username}@{domain}"
        password = "SecurePassword123!"

        data = {"address": email, "password": password}
        requests.post("https://api.mail.tm/accounts", json=data, timeout=10)

        token = requests.post(
            "https://api.mail.tm/token",
            json=data,
            timeout=10
        ).json()["token"]

        return email, token
    except Exception as e:
        print(f"Error in create_email: {e}")
        return None, None

def get_messages(token):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        return requests.get(
            "https://api.mail.tm/messages",
            headers=headers,
            timeout=10
        ).json()
    except Exception as e:
        print(f"Error in get_messages: {e}")
        return None

def find_otp(text):
    # ৪ থেকে ৮ ডিজিটের সংখ্যা খুঁজবে
    return re.findall(r"\b\d{4,8}\b", text)

# -----------------------------
# Telegram Handlers
# -----------------------------
# কীবোর্ড তৈরি করার ফাংশন যাতে বারবার একই কোড লিখতে না হয়
def get_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📧 New Email", callback_data="new")],
        [InlineKeyboardButton("📥 Inbox", callback_data="inbox")],
        [InlineKeyboardButton("🔑 Get OTP", callback_data="otp")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📬 Temp Mail OTP Bot Ready\n\nClick a button below to start:",
        reply_markup=get_keyboard()
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    keyboard = get_keyboard()

    if query.data == "new":
        await query.edit_message_
