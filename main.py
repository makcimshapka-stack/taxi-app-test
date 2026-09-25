import json
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# Токен вашого Telegram-бота
API_TOKEN = 'СТАВТЕ_СВІЙ_БОТ_ТОКЕН_ТУТ'

# Ваш реальний ID чату водіїв
DRIVER_CHAT_ID = -5044058539

# Словник з картками водіїв
DRIVER_CARDS = {
    "Макс": "4874070013052004",
    "Артур": "4441114417805692"
}

# ПОТОЧНИЙ ВОДІЙ (змініть на "Артур", коли зміну бере Артур)
CURRENT_DRIVER = "Макс"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Команда /start для відкриття WebApp
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    markup = types.InlineKeyboardMarkup()
    # Замініть посилання на адресу вашого сайту/хостингу, де лежить index.html
    web_app_info = types.WebAppInfo(url="https://ваш-сайт.com/index.html")
    markup.add(types.InlineKeyboardButton(text="🚗 Замовити таксі (Кобеляки)", web_app=web_app_info))
    
    await message.answer(
        "👋 Вітаємо у службі таксі Кобеляки!\nНатисніть кнопку нижче, щоб відкрити карту та оформити замовлення:",
        reply_markup=markup
    )

# Отримання даних із WebApp (index.html)
@dp.message_handler(content_types=['web_app_data'])
async def handle_web_app_data(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)
        
        address_from = data.get('address_from', 'Не вказано')
        address_to = data.get('address_to', 'Не вказано')
        phone = data.get('phone', 'Не вказано')
        payment_method = data.get('payment_method', 'Готівка')
        price = data.get('price', 100)
        price_desc = data.get('price_desc', '')

        # Формуємо повідомлення для водіїв
        order_text = (
            f"🚨 **НОВЕ ЗАМОВЛЕННЯ ТАКСІ!** 🚨\n\n"
            f"📍 **Звідки:** {address_from}\n"
            f"🏁 **Куди:** {address_to}\n"
            f"📞 **Телефон клієнта:** `{phone}`\n"
            f"💳 **Оплата:** {payment_method}\n"
            f"💰 **Вартість:** {price} грн _{price_desc}_\n"
            f"🚗 **Водій на зміні:** {CURRENT_DRIVER}"
        )

        # Якщо клієнт обрав оплату карткою, додаємо номер картки поточного водія
        if payment_method == 'Картка':
            card_num = DRIVER_CARDS.get(CURRENT_DRIVER, "4874070013052004")
            order_text += f"\n\n💳 **Реквізити для оплати карткою:**\n`{card_num}`"

        # 1. Надсилаємо підтвердження клієнту
        client_reply = (
            f"✅ **Ваше замовлення прийнято в роботу!**\n\n"
            f"📍 **Звідки:** {address_from}\n"
            f"🏁 **Куди:** {address_to}\n"
            f"💰 **Сума до сплати:** {price} грн ({payment_method})"
        )
        if payment_method == 'Картка':
            card_num = DRIVER_CARDS.get(CURRENT_DRIVER, "4874070013052004")
            client_reply += f"\n\n💳 **Номер картки для оплати:**\n`{card_num}`"

        await message.answer(client_reply, parse_mode="Markdown")

        # 2. Намагаємося надіслати в чат водіїв і виводимо результат у термінал
        try:
            await bot.send_message(DRIVER_CHAT_ID, order_text, parse_mode="Markdown")
            print("✅ Замовлення успішно відправлено у чат водіїв!")
        except Exception as err:
            print(f"❌ ПОМИЛКА відправки у чат водіїв (-5044058539): {err}")

    except Exception as e:
        logging.error(f"Помилка обробки замовлення: {e}")
        await message.answer("❌ Сталася помилка при оформленні замовлення. Спробуйте ще раз.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
