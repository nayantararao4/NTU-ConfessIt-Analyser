from telethon.sync import TelegramClient

api_id = 21661232
api_hash = 'b1c24a8435a740471f39701e18890c63'

with TelegramClient("anon", api_id, api_hash) as client:
    print("✅ Session saved!")