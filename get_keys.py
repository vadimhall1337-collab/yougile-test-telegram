import asyncio
import httpx

# Базовый URL YouGile API
API_URL = "https://ru.yougile.com/api-v2"

async def main():
    print("=== Утилита настройки YouGile API ===\n")
    print("Ваш ID компании можно найти в адресной строке браузера, когда вы открываете YouGile.")
    print("Например, в URL https://ru.yougile.com/board/1a2b3c4d... ID компании — это набор символов после /board/ или /team/.\n")
    
    company_id = input("Введите ID вашей компании: ").strip()
    login = input("Введите логин (email): ").strip()
    password = input("Введите пароль: ").strip()

    async with httpx.AsyncClient(base_url=API_URL) as client:
        # 1. Получение токена API
        print("\n⏳ Получаем API ключ...")
        auth_response = await client.post(
            "/auth/keys",
            json={"companyId": company_id, "login": login, "password": password}
        )

        if auth_response.status_code != 201 and auth_response.status_code != 200:
            print(f"❌ Ошибка авторизации: {auth_response.text}")
            return

        api_key = auth_response.json().get("key")
        print(f"✅ ВАШ YOUGILE_TOKEN:\n{api_key}\n")

        # 2. Получение списка колонок для поиска "Входящих"
        print("⏳ Загружаем список колонок...")
        columns_response = await client.get(
            "/columns",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        )

        if columns_response.status_code == 200:
            columns = columns_response.json().get("content", [])
            print("✅ Доступные колонки (скопируйте ID нужной для YOUGILE_INBOX_COLUMN_ID):\n")
            for col in columns[:20]:  # Выводим первые 20 для краткости
                print(f"ID: {col.get('id')} | Название: {col.get('title')}")
            if len(columns) > 20:
                print("... и другие.")
        else:
            print(f"❌ Не удалось получить колонки: {columns_response.text}")

if __name__ == "__main__":
    asyncio.run(main())