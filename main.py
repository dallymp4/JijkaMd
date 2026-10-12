import os, re, random, asyncio
from datetime import datetime, timedelta, timezone
from telethon import TelegramClient, functions, types
from telethon.sessions import StringSession

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
SESSION = os.environ["SESSION"]
MY_CHANNEL = int(os.environ["MY_CHANNEL"])

TARGET = os.environ["TARGET"].strip()
if TARGET.lstrip("-").isdigit():
    TARGET = int(TARGET)

TOPIC = os.environ.get("TOPIC", "").strip()
TOPIC = int(TOPIC) if TOPIC else None

DELAY = 240  # секунд до первого сообщения (можно уменьшить, например до 90)

CMD = re.compile(r"^/#(\S+)\s+(\d+)\s*r\s+(\d+)\s*m(?:\s+(me))?", re.I)


def extract_block(text, tag):
    out, inside = [], False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("#"):
            if inside:
                break
            if s.lower() == "#" + tag.lower().lstrip("#"):
                inside = True
        if inside:
            out.append(line)
    return "\n".join(out).strip()


async def send_scheduled(client, chat, text, when, topic):
    peer = await client.get_input_entity(chat)
    kwargs = {}
    if topic:
        kwargs["reply_to"] = types.InputReplyToMessage(
            reply_to_msg_id=topic, top_msg_id=topic
        )
    await client(functions.messages.SendMessageRequest(
        peer=peer,
        message=text,
        random_id=random.getrandbits(63),
        schedule_date=when,
        **kwargs,
    ))


async def main():
    print("TOPIC =", TOPIC)
    client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
    await client.start()
    await client.get_dialogs()

    msgs = [m async for m in client.iter_messages(MY_CHANNEL, limit=50) if m.text]
    catalog = [m.text for m in msgs if "/#" not in m.text]

    for m in msgs:
        match = CMD.match(m.text)
        if not match:
            continue
        tag, repeats, minutes, test = match.groups()
        repeats, minutes = min(int(repeats), 100), int(minutes)

        text = ""
        for c in catalog:
            text = extract_block(c, tag)
            if text:
                break
        if not text:
            await m.edit("❌ тег не найден: " + m.text)
            continue

        chat = "me" if test else TARGET
        topic = None if test else TOPIC
        print("send to", chat, "topic", topic, "x", repeats)

        base = max(m.date, datetime.now(timezone.utc)) + timedelta(seconds=DELAY)
        try:
            for i in range(repeats):
                jitter = random.randint(-15, 15)
                when = base + timedelta(minutes=minutes * i, seconds=jitter)
                await send_scheduled(client, chat, text, when, topic)
                await asyncio.sleep(0.5)
        except Exception as e:
            await m.edit("❌ ошибка: " + str(e)[:100] + " | " + m.text)
            continue

        await m.edit("✅ " + m.text)

    await client.disconnect()


asyncio.run(main())
