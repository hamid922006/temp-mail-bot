import aiohttp
import asyncio
import random
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = "8125617126:AAEG89OKzuYucnYo3-eWOhfZfza6mRJuI8o"

# ইন-মেমোরি স্টোরেজ
users = {}

# -----------------------------
# Helper: মেইন মেনু কিবোর্ড
# -----------------------------
def get_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📧 New Email", callback_data="new")],
        [InlineKeyboardButton("📥 Inbox", callback_data="inbox")],
        [InlineKeyboardButton("🔑 Get OTP", callback_data="otp")],
        [InlineKeyboardButton("📩 Read Latest", callback_data="read")]
    ])

# -----------------------------
# Asynchronous API Functions
# -----------------------------
async def make_request(method, url, headers=None, json_data=None):
    """aiohttp ব্যবহার করে নন-ব্লকিং রিকোয়েস্ট করার ফাংশন"""
    async with aiohttp.ClientSession() as session:
        async with session.request(method, url, headers=headers, json=json_data) as response:
            return await response.json()

async def create_email_async():
    # ডোমেইন লিস্ট নেওয়া
    domains_data = await make_request("GET", "https://api.mail.tm/domains")
    domain = random.choice(domains_data["hydra:member"])["domain"]

    username = f"user{random.randint(10000, 999999)}"
    email = f"{username}@{domain}"
    password = "password123"

    # অ্যাকাউন্ট তৈরি
    await make_request("POST", "https://api.mail.tm/accounts", 
                       json_data={"address": email, "password": password})
    
    # টোকেন নেওয়া
    token_data = await make_request("POST", "https://api.mail.tm/token", 
                                   json_data={"address": email, "password": password})
    
    return email, token_data["token"]

# -----------------------------
# Handlers (বট ফাংশনসমূহ)
# -----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚡ **Fast Temp Mail Bot**\n\nনিচের বাটন চেপে কাজ শুরু করো:",
        parse_mode="Markdown",
        reply_markup=get_keyboard()
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    try:
        if query.data == "new":
            await query.edit_message_text("⏳ ইমেইল তৈরি হচ্ছে, অপেক্ষা করো...")
            email, token = await create_email_async()
            users[user_id] = token
            await query.edit_message_text(
                f"✅ **তোমার ইমেইল:**\n`{email}`",
                parse_mode="Markdown",
                reply_markup=get_keyboard()
            )

        elif query.data == "inbox":
            token = users.get(user_id)
            if not token:
                return await query.edit_message_text("❌ আগে ইমেইল তৈরি করো!", reply_markup=get_keyboard())

            headers = {"Authorization": f"Bearer {token}"}
            msgs = await make_request("GET", "https://api.mail.tm/messages", headers=headers)

            if not msgs.get("hydra:member"):
                return await query.edit_message_text("📭 ইনবক্স খালি।", reply_markup=get_keyboard())

            text = "📥 **সাম্প্রতিক ইনবক্স:**\n\n"
            for m in msgs["hydra:member"][:5]: # সর্বোচ্চ ৫টি মেসেজ দেখাবে
                text += f"👤 **From:** {m['from']['address']}\n📝 **Sub:** {m['subject']}\n\n"
            
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=get_keyboard())

        elif query.data == "otp":
            token = users.get(user_id)
            if not token: return
            
            headers = {"Authorization": f"Bearer {token}"}
            msgs = await make_request("GET", "https://api.mail.tm/messages", headers=headers)
            
            codes = []
            for m in msgs.get("hydra:member", []):
                found = re.findall(r"\b\d{4,8}\b", m.get("intro", ""))
                codes.extend(found)

            result = "🔑 **OTP গুলো:**\n" + "\n".join(codes) if codes else "❌ কোনো OTP মেলেনি।"
            await query.edit_message_text(result, reply_markup=get_keyboard())

    except Exception as e:
        await query.edit_message_text(f"⚠️ ত্রুটি: {e}", reply_markup=get_keyboard())

# -----------------------------
# Run Bot
# -----------------------------
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    
    print("🚀 বট পুরোদমে চলছে...")
    app.run_polling()
