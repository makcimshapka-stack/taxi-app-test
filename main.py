import json
import logging
import asyncio
from aiogram import Bot, Dispatcher, types

API_TOKEN = '8817022184:AAGD3M8scpb6U7Ndwa4N4RlO0jLj1PTpkw4'
DRIVER_CHAT_ID = -5044058539

# Словник з картками водіїв
DRIVER_CARDS = {
    "Макс": "4874070013052004",
    "Артур": "4441114417805692",
    "Artut": "4441114417805692"
}

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(lambda message: message.text and message.text.startswith('/start'))
async def send_welcome(message: types.Message):
    markup = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="🚗 Замовити таксі (Кобеляки)",
                    web_app=types.WebAppInfo(url="https://ваш-сайт.com/index.html")
                )
            ]
        ]
    )
    await message.answer(
        "👋 Вітаємо у службі таксі Кобеляки!\nНатисніть кнопку нижче, щоб відкрити карту та оформити замовлення:",
        reply_markup=markup
    )

@dp.message(lambda message: message.web_app_data is not None)
async def handle_web_app_data(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)
        
        address_from = data.get('address_from', 'Не вказано')
        address_to = data.get('address_to', 'Не вказано')
        phone = data.get('phone', 'Не вказано')
        payment_method = data.get('payment_method', 'Готівка')
        price = data.get('price', 100)
        price_desc = data.get('price_desc', '')

        await message.answer("⏳ **Очікуйте, передаємо замовлення водіям...**", parse_mode="Markdown")

        order_text = (
            f"🚨 **НОВЕ ЗАМОВЛЕННЯ ТАКСІ!** 🚨\n\n"
            f"📍 **Звідки:** {address_from}\n"
            f"🏁 **Куди:** {address_to}\n"
            f"📞 **Телефон клієнта:** `{phone}`\n"
            f"💳 **Оплата:** {payment_method}\n"
            f"💰 **Вартість:** {price} грн _{price_desc}_\n"
        )

        # Передаємо всі дані через callback_data (надійно і без збоїв)
        # Формат: accept_IDКлієнта_Ціна_Оплата
        callback_data_str = f"accept_{message.from_user.id}_{price}_{payment_method}"

        markup = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="🚗 Взяти замовлення", callback_data=callback_data_str)]
            ]
        )

        await bot.send_message(DRIVER_CHAT_ID, order_text, reply_markup=markup, parse_mode="Markdown")

    except Exception as e:
        logging.error(f"Помилка відправки замовлення: {e}")
        await message.answer("❌ Сталася помилка при оформленні замовлення.")

@dp.callback_query(lambda c: c.data.startswith('accept_'))
async def process_accept(callback: types.CallbackQuery):
    try:
        parts = callback.data.split('_')
        client_id = int(parts[1])
        price = parts[2]
        payment_method = parts[3]
        
        driver_name = callback.from_user.first_name or "Водій"
        card_num = DRIVER_CARDS.get(driver_name, "4874070013052004")

        # Оновлюємо повідомлення у водійському чаті
        await callback.message.edit_text(
            callback.message.text + f"\n\n✅ **Замовлення прийняв(la): {driver_name}**",
            reply_markup=None,
            parse_mode="Markdown"
        )

        # Формуємо підтвердження клієнту
        client_reply = (
            f"✅ **Ваше замовлення прийнято в роботу!**\n\n"
            f"🚗 **Водій:** {driver_name}\n"
            f"💰 **Сума до сплати:** {price} грн ({payment_method})"
        )
        if payment_method == 'Картка':
            client_reply += f"\n\n💳 **Номер картки для оплати ({driver_name}):**\n`{card_num}`"

        await bot.send_message(client_id, client_reply, parse_mode="Markdown")
        await callback.answer("Ви успішно прийняли замовлення!")

    except Exception as e:
        logging.error(f"Помилка обробки натискання: {e}")
        await callback.answer("❌ Помилка при прийнятті замовлення.", show_alert=True)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
