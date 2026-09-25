import asyncio
import logging
import sys
import json
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = "8817022184:AAHXN8Y5JO4UQcoIpN6Dt_QOX-r7fSjfVgY"
DRIVER_GROUP_ID = -5044058539

bot = Bot(token=TOKEN)
dp = Dispatcher()

active_orders = {}

@dp.message(F.web_app_data)
async def handle_web_app_data(message: types.Message):
    client_chat_id = message.from.user.id
    client_name = message.from.user.first_name or "Клієнт"

    try:
        data = json.loads(message.web_app_data.data)

        order_text = (
            f"🚨 <b>НОВЕ ЗАМОВЛЕННЯ ТАКСІ</b> 🚨\n\n"
            f"📍 <b>Звідки:</b> {data.get('address_from')}\n"
            f"🏁 <b>Куди:</b> {data.get('address_to')}\n"
            f"💰 <b>Вартість:</b> {data.get('price')} грн ({data.get('price_desc')})\n"
            f"📞 <b>Телефон:</b> {data.get('phone')}\n"
            f"👤 <b>Клієнт:</b> {client_name} (ID: {client_chat_id})"
        )

        builder = InlineKeyboardBuilder()
        builder.button(
            text="✅ Прийняти", 
            callback_data=f"accept_{client_chat_id}"
        )

        sent_message = await bot.send_message(
            chat_id=DRIVER_GROUP_ID,
            text=order_text,
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )

        active_orders[sent_message.message_id] = client_chat_id
        await message.answer("⏳ Очікуйте, шукаємо вільне авто...")

    except Exception as e:
        logging.error(f"Помилка обробки замовлення: {e}")
        await message.answer("❌ Сталася помилка при оформленні замовлення. Спробуйте ще раз.")


@dp.callback_query(F.data.startswith("accept_"))
async def accept_order_callback(callback: types.CallbackQuery):
    client_chat_id = int(callback.data.split("_")[1])
    driver_name = callback.from_user.first_name or "Водій"

    try:
        original_text = callback.message.html_text
        updated_text = f"{original_text}\n\n✅ <b>Статус:</b> Замовлення прийняв водій {driver_name}"
        
        await bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=updated_text,
            parse_mode="HTML",
            reply_markup=None
        )

        await bot.send_message(
            chat_id=client_chat_id,
            text=(
                f"✅ <b>Ваше замовлення прийнято!</b>\n\n"
                f"🚗 Водій <b>{driver_name}</b> виїхав до Вас. Очікуйте автомобіль!"
            ),
            parse_mode="HTML"
        )

        await callback.answer("Ви успішно прийняли замовлення!")

    except Exception as e:
        logging.error(f"Помилка при прийнятті замовлення: {e}")
        await callback.answer("Помилка! Можливо, замовлення вже прийняте іншим водієм.", show_alert=True)


async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
