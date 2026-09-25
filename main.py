import asyncio
import logging
import sys
import json
from aiogram import Bot, Dispatcher, F, types
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = "8817022184:AAHXN8Y5JO4UQcoIpN6Dt_QOX-r7fSjfVgY"
DRIVER_GROUP_ID = -5044058539

# 🚗 БАЗА ДАНИХ АВТОМОБІЛІВ ТА КАРТОК ВОДІЇВ
DRIVER_INFO = {
    "suetolog_mak": {
        "car": "Honda (Ві8926ЕР)",
        "card": "4874070013052004",
        "name": "Макс"
    },
    "artur_grek4": {
        "car": "Renault (ВІ1393НР)",
        "card": "4441114417805692",
        "name": "Артур"
    }
}

bot = Bot(token=TOKEN)
dp = Dispatcher()

active_orders = {}

@dp.message(F.web_app_data)
async def handle_web_app_data(message: types.Message):
    user = message.from_user
    client_chat_id = user.id
    client_name = user.first_name or "Клієнт"

    try:
        data = json.loads(message.web_app_data.data)

        addr_from = data.get('address_from', '')
        addr_to = data.get('address_to', '')
        price = data.get('price', '')
        price_desc = data.get('price_desc', '')
        phone = data.get('phone', '')
        payment_method = data.get('payment_method', 'Готівка')

        price_full = f"{price} грн"
        if price_desc:
            price_full += f" ({price_desc})"

        order_text = (
            f"🚨 <b>НОВЕ ЗАМОВЛЕННЯ ТАКСІ</b> 🚨\n\n"
            f"📍 <b>Звідки:</b> {addr_from}\n"
            f"🏁 <b>Куди:</b> {addr_to}\n"
            f"💰 <b>Вартість:</b> {price_full}\n"
            f"💳 <b>Оплата:</b> {payment_method}\n"
            f"📞 <b>Телефон:</b> {phone}\n"
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

        active_orders[sent_message.message_id] = {
            "client_chat_id": client_chat_id,
            "price": price_full,
            "payment_method": payment_method
        }

        await message.answer("⏳ Очікуйте, шукаємо вільне авто...")

    except Exception as e:
        logging.error(f"Помилка обробки замовлення: {e}")
        await message.answer("❌ Сталася помилка при оформленні замовлення.")


@dp.callback_query(F.data.startswith("accept_"))
async def accept_order_callback(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    client_chat_id = int(parts[1])
    
    driver_user = callback.from_user
    driver_username = driver_user.username.lower() if driver_user.username else ""
    
    driver_data = DRIVER_INFO.get(driver_username, {
        "car": "Автомобіль уточнюється",
        "card": "Уточнюється",
        "name": driver_user.first_name or "Водій"
    })

    driver_name = driver_data["name"]
    car_info = driver_data["car"]
    card_number = driver_data["card"]

    order_info = active_orders.get(callback.message.message_id, {})
    price_str = order_info.get("price", "Уточнюється")
    payment_method = order_info.get("payment_method", "Готівка")

    try:
        base_text = callback.message.html_text.split("\n\n✅ <b>Статус:</b>")[0]
        updated_text = f"{base_text}\n\n✅ <b>Статус:</b> Замовлення прийняв водій {driver_name} ({car_info})"
        
        await bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=updated_text,
            parse_mode="HTML",
            reply_markup=None
        )

        # Формування повідомлення для клієнта залежно від способу оплати
        client_msg = (
            f"✅ <b>Ваше замовлення прийнято в роботу!</b>\n\n"
            f"🚗 <b>Водій:</b> {driver_name}\n"
            f"🚘 <b>Автомобіль:</b> {car_info}\n"
            f"💰 <b>Вартість:</b> {price_str}\n"
            f"💳 <b>Оплата:</b> {payment_method}\n"
        )

        if payment_method == "Картка":
            client_msg += f"\n💳 <b>Номер картки для оплати:</b>\n<code>{card_number}</code>\n"

        client_msg += "\nОчікуйте на автомобіль поруч із місцем посадки."

        await bot.send_message(
            chat_id=client_chat_id,
            text=client_msg,
            parse_mode="HTML"
        )

        await callback.answer("Ви успішно прийняли замовлення!")

    except Exception as e:
        logging.error(f"Помилка при прийнятті замовлення: {e}")
        await callback.answer("Помилка!", show_alert=True)


async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
