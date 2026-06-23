import json
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

BOT_TOKEN = "8823680930:AAHzZ4SZnzpZ_igFPzX-QnwEmn2-LGtWtMk"

ADMIN_ID = 1160840346
GROUP_ID = -1004395048219

GROUP_LINK = "https://t.me/+XJIvFmwEZOFmMDk1"

QR_FILE_ID = "AgACAgUAAxkBAAM2ajo_rVW17znPZTRE4q440YJEetwAAocRaxsSkdFVHyMOCVnPgRABAAMCAAN5AAM8BA"

DATA_FILE = "approved_users.json"

pending_users = set()


def load_users():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save_users(users):
    with open(DATA_FILE, "w") as f:
        json.dump(users, f, indent=4)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_photo(
        photo=QR_FILE_ID,
        caption=(
            "💰 Pay ₹30/-\n\n"
            "Get unlimited background images and prompts every month.\n\n"
            "Payment complete chesi screenshot pampandi."
        )
    )


async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id in pending_users:
        await update.message.reply_text(
            "⏳ Payment already under review."
        )
        return

    pending_users.add(user_id)

    buttons = [[
        InlineKeyboardButton(
            "✅ Approve",
            callback_data=f"approve_{user_id}"
        ),
        InlineKeyboardButton(
            "❌ Reject",
            callback_data=f"reject_{user_id}"
        )
    ]]

    await context.bot.forward_message(
        chat_id=ADMIN_ID,
        from_chat_id=update.effective_chat.id,
        message_id=update.message.message_id
    )

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"Payment Screenshot\nUser ID: {user_id}",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

    await update.message.reply_text(
        "✅ Screenshot received. Wait for approval."
    )


async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = int(query.data.split("_")[1])

    users = load_users()

    if str(user_id) in users:
        old = datetime.strptime(
            users[str(user_id)]["expiry"],
            "%Y-%m-%d"
        )

        if old > datetime.now():
            expiry = old + timedelta(days=30)
        else:
            expiry = datetime.now() + timedelta(days=30)

    else:
        expiry = datetime.now() + timedelta(days=30)


    users[str(user_id)] = {
        "expiry": expiry.strftime("%Y-%m-%d")
    }

    save_users(users)

    pending_users.discard(user_id)


    await context.bot.send_message(
        chat_id=user_id,
        text=(
            "✅ Payment Verified!\n\n"
            f"Join Group:\n{GROUP_LINK}\n\n"
            f"Valid till: {expiry.strftime('%d-%m-%Y')}"
        )
    )

    await query.edit_message_text(
        "✅ Approved"
    )


async def reject(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = int(query.data.split("_")[1])

    pending_users.discard(user_id)

    await context.bot.send_message(
        chat_id=user_id,
        text="❌ Payment rejected."
    )

    await query.edit_message_text(
        "❌ Rejected"
    )


async def check_expiry(context: ContextTypes.DEFAULT_TYPE):

    users = load_users()
    today = datetime.now().date()

    for uid, data in list(users.items()):

        expiry = datetime.strptime(
            data["expiry"],
            "%Y-%m-%d"
        ).date()

        if expiry <= today:

            try:
                await context.bot.send_message(
                    chat_id=int(uid),
                    text=(
                        "⚠️ Subscription expired.\n\n"
                        "Renew ₹30/- to continue.\n"
                        "Type /start for QR."
                    )
                )

                await context.bot.ban_chat_member(
                    GROUP_ID,
                    int(uid)
                )

                await context.bot.unban_chat_member(
                    GROUP_ID,
                    int(uid)
                )

            except Exception as e:
                print(e)

            del users[uid]

    save_users(users)


app = Application.builder().token(BOT_TOKEN).build()


app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.PHOTO, photo))

app.add_handler(
    CallbackQueryHandler(
        approve,
        pattern="^approve_"
    )
)

app.add_handler(
    CallbackQueryHandler(
        reject,
        pattern="^reject_"
    )
)


app.job_queue.run_repeating(
    check_expiry,
    interval=86400,
    first=10
)


print("Bot is running...")

app.run_polling()