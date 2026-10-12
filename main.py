import os, re, random, asyncio
from datetime import datetime, timedelta, timezone
from telethon import TelegramClient
from telethon.sessions import StringSession

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
SESSION = os.environ["SESSION"]
MY_CHANNEL = int(os.environ["MY_CHANNEL"])
TARGET = os.environ["TARGET"]
if TARGET.lstrip("-").isdigit():
    TARGET = int(TARGET)

CMD = re.compile(r"^/#(\S+)\s+(\d+)\s*r\s+(\d+)\s*m", re.I)


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


async def main():
    client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
    await client.start()
    await client.get_dialogs()

    msgs = [m async for m in client.iter_messages(MY_CHANNEL, limit=50) if m.text]
    catalog = [m.text for m in msgs if "/#" not in m.text]

    for m in msgs:
        match = CMD.match(m.text)
        if not match:
            continue
        tag, repeats, minutes = match.groups()
        repeats, minutes = min(int(repeats), 100), int(minutes)

        text = ""
        for c in catalog:
            text = extract_block(c, tag)
            if text:
                break

        if not text:
            await m.edit("❌ тег не найден: " + m.text)
            continue

        base = max(m.date, datetime.now(timezone.utc)) + timedelta(seconds=90)
        for i in range(repeats):
            jitter = random.randint(-15, 15)
            when = base + timedelta(minutes=minutes * i, seconds=jitter)
            await client.send_message(TARGET, text, schedule=when)

        await m.edit("✅ " + m.text)

    await client.disconnect()


asyncio.run(main())
