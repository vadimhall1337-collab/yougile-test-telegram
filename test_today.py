import asyncio
from datetime import datetime

from bot.config.settings import config
from bot.yougile.client import YouGileClient


async def test():
    client = YouGileClient(api_key=config.YOUGILE_TOKEN)

    response = await client.request("GET", "/tasks?limit=1000")

    tasks = response["content"]
    today = datetime.now().date()

    print(f"Сегодня: {today}")
    print("-" * 60)

    found = False

    for task in tasks:
        deadline = task.get("deadline")

        if not deadline:
            continue

        timestamp = deadline.get("deadline")

        if not timestamp:
            continue

        deadline_date = datetime.fromtimestamp(timestamp / 1000).date()

        if deadline_date == today:
            found = True
            print(task["title"])
            print(f"Дедлайн: {deadline_date}")
            print(f"ID: {task['id']}")
            print("-" * 60)

    if not found:
        print("Сегодня задач с дедлайном нет.")


asyncio.run(test())