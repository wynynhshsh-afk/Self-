import sys

from telethon import TelegramClient, events

# آرگومان‌ها از telbot.py پاس داده می‌شن:
# session_name, api_id, api_hash
session_name = sys.argv[1]
api_id = int(sys.argv[2])
api_hash = sys.argv[3]

client = TelegramClient(session_name, api_id, api_hash)


@client.on(events.NewMessage(outgoing=True, pattern="^سلف روشن$"))
async def turn_on(event):
    await event.edit("سلف بات روشن شد")


@client.on(events.NewMessage(outgoing=True, pattern="^سلف خاموش$"))
async def turn_off(event):
    await event.edit("سلف بات خاموش شد")


if __name__ == "__main__":
    print("سلف بات اجرا شد...")
    client.start()
    client.run_until_disconnected()
