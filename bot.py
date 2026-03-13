# -----------------------------
# Telegram Temp Mail OTP Bot
# -----------------------------

BOT_TOKEN = "8125617126:AAEElKkt2Rl7RvgRL2GKNTDFdplt5W69Eik"  # <-- BotFather থেকে token বসান

import requests
import random
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

users = {}

# -----------------------------
# Mail.tm API
# -----------------------------
def create_email():
    domains = requests.get("https://api.mail.tm/domains").json()
    domain = domains["hydra:member"][0]["domain"]

    username = "user" + str(random.randint(10000,99999))
    email = f"{username}@{domain}"
    password = "123456"

    data = {"address": email, "password": password}

    requests.post("https://api.mail.tm/accounts", json=data)

    token = requests.post(
        "https://api.mail.tm/token",
        json={"address": email, "password": password}
    ).json()["token"]

    return email, token


def get_messages(token):
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(
        "https://api.mail.tm/messages",
        headers=headers
    ).json()


def find_otp(text):
    return re.findall(r"\b\d{4,8}\b", text)


# -----------------------------
# Telegram Start
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


# -----------------------------
# Button Handler
# -----------------------------
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
        if msgs.get("hydra:totalItems",0) == 0:
            await query.edit_message_text("📭 Inbox Empty")
            return
        text = ""
        for m in msgs["hydra:member"]:
            sender = m["from"]["address"]
            subject = m["subject"]
            text += f"From: {sender}\nSubject: {subject}\n\n"
        await query.edit_message_text(text)

    elif query.data == "otp":
        token = users.get(user_id)
        if not token:
            await query.edit_message_text("❌ Create email first")
            return
        msgs = get_messages(token)
        codes = []
        for m in msgs["hydra:member"]:
            codes += find_otp(m.get("intro",""))
        if codes:
            await query.edit_message_text("🔑 OTP Codes:\n\n" + "\n".join(codes))
        else:
            await query.edit_message_text("❌ No OTP Found")


# -----------------------------
# Run Bot
# -----------------------------
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))

print("Bot Running...")
app.run_polling()
