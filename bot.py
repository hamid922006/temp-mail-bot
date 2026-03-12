# -----------------------------
# Telegram Temp Mail OTP Bot
# -----------------------------

BOT_TOKEN = "8125617126:AAH_tuqQuFhjR69AgsfNKmi9rlXkUk6QWxM"  # <-- এখানে BotFather token বসান

import requests
import random
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# User tokens dictionary
users = {}

# -----------------------------
# Mail.tm API functions
# -----------------------------
def create_email():
    # Get first available domain
    domains = requests.get("https://api.mail.tm/domains").json()
    domain = domains["hydra:member"][0]["domain"]

    # Generate random username
    username = "user" + str(random.randint(10000,99999))
    email = f"{username}@{domain}"
    password = "123456"

    # Create mail account
    data = {"address": email, "password": password}
    requests.post("https://api.mail.tm/accounts", json=data)

    # Get API token
    token = requests.post("https://api.mail.tm/token", json={"address": email, "password": password}).json()["token"]

    return email, token

def get_messages(token):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get("https://api.mail.tm/messages", headers=headers).json()
    return r

def find_otp(text):
    return re.findall(r"\b\d{4,8}\b", text)

# -----------------------------
# Telegram bot functions
# -----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📧 New Email", callback_data="new")],
        [InlineKeyboardButton("📥 Inbox", callback_data="inbox")],
        [InlineKeyboardButton("🔑 Get OTP", callback_data="otp")]
    ]
    await update.message.reply_text(
        "📬 Temp Mail OTP Bot Ready",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "new":
        email, token = create_email()
        users[user_id] = token
        await query.edit_message_text(f"📧 Temp Email Created:\n\n{email}")

    elif query.data == "inbox":
        token = users.get(user_id)
        if not token:
            await query.edit_message_text("❌ Create email first")
            return
        msgs = get_messages(token)
        if msgs["hydra:totalItems"] == 0:
            await query.edit_message_text("📭 Inbox Empty")
            return
        text = ""
        for m in msgs["hydra:member"]:
            text += f"From: {m['from']['address']}\nSubject: {m['subject']}\n\n"
        await query.edit_message_text(text)

    elif query.data == "otp":
        token = users.get(user_id)
        if not token:
            await query.edit_message_text("❌ Create email first")
            return
        msgs = get_messages(token)
        codes = []
        for m in msgs["hydra:member"]:
            codes += find_otp(m["intro"])
        if codes:
            await query.edit_message_text("🔑 OTP Codes:\n" + "\n".join(codes))
        else:
            await query.edit_message_text("❌ No OTP Found")

# -----------------------------
# Run Bot
# -----------------------------
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))

print("Bot is running...")
app.run_polling()
