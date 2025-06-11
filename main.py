import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
import threading

# ✅ توكن البوت الجديد
API_TOKEN = '7384121018:AAHY2amkSb_36h3JS4kU_dfxJPPgkKNUBJ0'
CHANNEL_USERNAME = '@talabaksyria'
ADMIN_ID = 809571974

bot = telebot.TeleBot(API_TOKEN, skip_pending=True)
app = Flask(__name__)

# لتخزين الطلبات المعلقة
pending_orders = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "مرحبًا! 👋\n\n"
        "هذا البوت مخصص لاستلام طلبات البيع الخاصة بك.\n"
        "أرسل تفاصيل المنتج أو الخدمة، ثم اكتب /done عند الانتهاء.\n\n"
        "سيتم إرسال طلبك للموافقة، وبعدها يُنشر بالقناة.\n"
        "شكراً لاستخدامك بوت طلبك سوريا! 😊"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(content_types=['text', 'photo'])
def handle_user_message(message):
    user_id = message.from_user.id
    if user_id not in pending_orders:
        pending_orders[user_id] = []
    pending_orders[user_id].append(message)
    bot.reply_to(message, "تم استلام الطلب، أرسل باقي التفاصيل أو اكتب /done.")

@bot.message_handler(commands=['done'])
def done_collecting(message):
    user_id = message.from_user.id
    if user_id not in pending_orders or not pending_orders[user_id]:
        bot.reply_to(message, "لم يتم استلام أي تفاصيل بعد.")
        return

    order_msgs = pending_orders[user_id]
    del pending_orders[user_id]

    media_group = []
    text_parts = []

    for msg in order_msgs:
        if msg.content_type == 'photo':
            file_id = msg.photo[-1].file_id
            media_group.append(telebot.types.InputMediaPhoto(file_id))
        elif msg.content_type == 'text':
            text_parts.append(msg.text)

    preview_text = "\n".join(text_parts)
    preview_caption = f"طلب جديد من @{message.from_user.username or message.from_user.first_name}:\n\n{preview_text}\n\nهل توافق على نشر هذا الطلب؟"

    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("✅ انشر الطلب", callback_data=f"approve_{user_id}"),
        InlineKeyboardButton("❌ رفض الطلب", callback_data=f"reject_{user_id}")
    )

    if media_group:
        bot.send_media_group(ADMIN_ID, media_group)
        bot.send_message(ADMIN_ID, preview_caption, reply_markup=markup)
    else:
        bot.send_message(ADMIN_ID, preview_caption, reply_markup=markup)

    bot.reply_to(message, "تم إرسال الطلب للموافقة.")

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    data = call.data
    if data.startswith('approve_') or data.startswith('reject_'):
        action, user_id_str = data.split('_')
        user_id = int(user_id_str)

        if call.from_user.id != ADMIN_ID:
            bot.answer_callback_query(call.id, "أنت غير مخول باتخاذ هذا الإجراء.")
            return

        if action == 'approve':
            send_order_to_channel(user_id)
            bot.answer_callback_query(call.id, "✅ تم النشر.")
        elif action == 'reject':
            bot.send_message(user_id, "❌ تم رفض طلبك من قبل الإدارة.")
            bot.answer_callback_query(call.id, "❌ تم الرفض.")

        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

def send_order_to_channel(user_id):
    bot.send_message(CHANNEL_USERNAME, f"✅ تم نشر طلب جديد من المستخدم: {user_id}\n\n(الطلب هنا يحتاج تخزين مفصل لاحقاً)")

# 🟢 صفحة بسيطة لعرض حالة السيرفر
@app.route('/')
def home():
    return "بوت طلبك شغال ✅"

# 🔄 تشغيل البوت والسيرفر
def run():
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=10000)).start()
    bot.infinity_polling()

if __name__ == '__main__':
    run()