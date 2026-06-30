import subprocess

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

# ---------------------- تنظیمات ----------------------
BOT_TOKEN = "8875179274:AAHg3DDrTRG0JoQ6ChXx44OBwKkuxuHNz2U"        # از @BotFather بگیر
API_ID = 31830597                      # از my.telegram.org بگیر
API_HASH = "e46aa2127ada5dc6c18821ed95a59ca8"           # از my.telegram.org بگیر
# -------------------------------------------------------

PHONE, CODE, PASSWORD = range(3)

clients = {}  # نگهداری موقت کلاینت تلتون هر کاربر تا پایان لاگین


def code_keyboard(current: str = ""):
    rows = [
        ["1", "2", "3"],
        ["4", "5", "6"],
        ["7", "8", "9"],
        ["پاک کردن", "0", "تایید"],
    ]
    keyboard = [[InlineKeyboardButton(x, callback_data=f"code_{x}") for x in row] for row in rows]
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "شماره تلفن اکانتی که می‌خوای سلف روش فعال بشه رو با کد کشور وارد کن.\nمثال: 989123456789+"
    )
    return PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    context.user_data["phone"] = phone
    user_id = update.effective_user.id

    client = TelegramClient(f"session_{user_id}", API_ID, API_HASH)
    await client.connect()
    try:
        sent = await client.send_code_request(phone)
        context.user_data["phone_code_hash"] = sent.phone_code_hash
        clients[user_id] = client
    except Exception as e:
        await update.message.reply_text(f"خطا در ارسال کد: {e}")
        return ConversationHandler.END

    context.user_data["entered_code"] = ""
    await update.message.reply_text(
        "کدی که تلگرام برات فرستاد رو با دکمه‌های زیر وارد کن:",
        reply_markup=code_keyboard(),
    )
    return CODE


async def code_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.replace("code_", "")
    user_id = update.effective_user.id

    entered = context.user_data.get("entered_code", "")

    if data == "پاک کردن":
        entered = entered[:-1]
        context.user_data["entered_code"] = entered
        await query.edit_message_text(f"کد فعلی: {entered or '...'}", reply_markup=code_keyboard())
        return CODE

    if data == "تایید":
        phone = context.user_data["phone"]
        client = clients.get(user_id)
        try:
            await client.sign_in(
                phone,
                entered,
                phone_code_hash=context.user_data["phone_code_hash"],
            )
            await query.edit_message_text("ورود موفقیت‌آمیز بود ✅")
            await finish_login(context, user_id, client)
            return ConversationHandler.END
        except SessionPasswordNeededError:
            await query.edit_message_text("این اکانت رمز دومرحله‌ای داره. لطفاً رمزو پیام کن:")
            return PASSWORD
        except PhoneCodeInvalidError:
            context.user_data["entered_code"] = ""
            await query.edit_message_text("کد اشتباه بود، دوباره وارد کن:", reply_markup=code_keyboard())
            return CODE
        except Exception as e:
            await query.edit_message_text(f"خطا: {e}")
            return ConversationHandler.END

    entered += data
    context.user_data["entered_code"] = entered
    await query.edit_message_text(f"کد فعلی: {entered}", reply_markup=code_keyboard())
    return CODE


async def get_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text.strip()
    user_id = update.effective_user.id
    client = clients.get(user_id)
    try:
        await client.sign_in(password=password)
        await update.message.reply_text("ورود موفقیت‌آمیز بود ✅")
        await finish_login(context, user_id, client)
    except Exception as e:
        await update.message.reply_text(f"خطا: {e}")
    return ConversationHandler.END


async def finish_login(context, user_id, client):
    session_name = f"session_{user_id}"
    await client.disconnect()
    clients.pop(user_id, None)
    # اجرای سلف بات با همین سشن، به صورت پروسه‌ی جدا
    subprocess.Popen(["python3", "bot.py", session_name, str(API_ID), API_HASH])
    await context.bot.send_message(user_id, "سلف بات روی اکانتت فعال شد 🎉")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("لغو شد.")
    return ConversationHandler.END


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            CODE: [CallbackQueryHandler(code_button)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_password)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv)
    app.run_polling()


if __name__ == "__main__":
    main()
