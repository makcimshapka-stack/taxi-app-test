import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Вставте сюди токен вашого Telegram-бота
TOKEN = "ВАШ_ТОКЕН_БОТА"

# ID вашої робочої групи водіїв (сюди надходитимуть замовлення)
DRIVER_GROUP_ID = -5044058539  # Замініть на реальний ID групи (має починатися з -100)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Словник для зберігання зв'язку між ID повідомлення в групі водіїв та chat_id клієнта
active_orders = {}

@dp.message(F.web_app_data)
async def handle_web_app_data(message: types.Message):
    client_chat_id = message.from.user.id  # Це chat_id клієнта
    client_name = message.from.user.first_name or "Клієнт"

    try:
        import json
        data = json.loads(message.web_app_data.data)

        # Формуємо текст замовлення для водіїв
        order_text = (
            f"🚨 <b>НОВЕ ЗАМОВЛЕННЯ ТАКСІ</b> 🚨\n\n"
            f"📍 <b>Звідки:</b> {data.get('address_from')}\n"
            f"🏁 <b>Куди:</b> {data.get('address_to')}\n"
            f"💰 <b>Вартість:</b> {data.get('price')} грн ({data.get('price_desc')})\n"
            f"📞 <b>Телефон:</b> {data.get('phone')}\n"
            f"👤 <b>Клієнт:</b> {client_name} (ID: {client_chat_id})"
        )

        # Створюємо кнопку "Прийняти" (зберігаємо client_chat_id у callback_data)
        builder = InlineKeyboardBuilder()
        builder.button(
            text="✅ Прийняти", 
            callback_data=f"accept_{client_chat_id}"
        )

        # Відправляємо замовлення у групу водіїв
        sent_message = await bot.send_message(
            chat_id=DRIVER_GROUP_ID,
            text=order_text,
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )

        # Зберігаємо зв'язок (якщо потрібно для розширеної логіки)
        active_orders[sent_message.message_id] = client_chat_id

        # Повідомляємо клієнту в його чаті з ботом
        await message.answer("⏳ Очікуйте, шукаємо вільне авто...")

    except Exception as e:
        logging.error(f"Помилка обробки замовлення: {e}")
        await message.answer("❌ Сталася помилка при оформленні замовлення. Спробуйте ще раз.")


@dp.callback_query(F.data.startswith("accept_"))
async def accept_order_callback(callback: types.CallbackQuery):
    # Витягуємо chat_id клієнта із callback_data
    client_chat_id = int(callback.data.split("_")[1])
    driver_name = callback.from_user.first_name or "Водій"

    try:
        # 1. Оновлюємо повідомлення у групі водіїв (додаємо статус, що замовлення прийнято)
        original_text = callback.message.html_text
        updated_text = f"{original_text}\n\n✅ <b>Статус:</b> Замовлення прийняв водій {driver_name}"
        
        await bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=updated_text,
            parse_mode="HTML",
            reply_markup=None # Прибираємо кнопку, оскільки замовлення вже прийняте
        )

        # 2. ВІДПРАВЛЯЄМО ПОВІДОМЛЕННЯ КЛІЄНТУ В ОСОБИСТИЙ ЧАТ
        await bot.send_message(
            chat_id=client_chat_id,
            text=(
                f"✅ <b>Ваше замовлення прийнято!</b>\n\n"
                f"🚗 Водій <b>{driver_name}</b> виїхав до Вас. Очікуйте автомобіль!"
            ),
            parse_mode="HTML"
        )

        # Підтверджуємо натискання кнопки для водія (щоб зникла крутилка)
        await callback.answer("Ви успішно прийняли замовлення!")

    except Exception as e:
        logging.error(f"Помилка при прийнятті замовлення: {e}")
        await callback.answer("Помилка! Можливо, замовлення вже прийняте іншим водієм.", show_alert=True)


async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
