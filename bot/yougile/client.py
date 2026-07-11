import asyncio
import time
import httpx
import structlog
from typing import Any, Dict, Optional

logger = structlog.get_logger(__name__)

class YouGileAPIError(Exception):
    """Базовое исключение для ошибок API YouGile."""
    pass

class YouGileRateLimitError(YouGileAPIError):
    """Исключение при превышении лимита запросов."""
    pass

class YouGileClient:
    def __init__(self, api_key: str, base_url: str = "https://ru.yougile.com/api-v2"):
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self.headers,
            timeout=httpx.Timeout(15.0)
        )
        
        # Управление лимитами (не более 50 в минуту на компанию)
        self._request_timestamps = []
        self._rate_limit_lock = asyncio.Lock()

    async def _wait_for_rate_limit(self):
        """Алгоритм Sliding Window для соблюдения лимита 50 запросов в минуту."""
        async with self._rate_limit_lock:
            now = time.time()
            # Очищаем старые запросы (старше 60 секунд)
            self._request_timestamps = [ts for ts in self._request_timestamps if now - ts < 60]
            
            if len(self._request_timestamps) >= 49:
                sleep_time = 60 - (now - self._request_timestamps[0])
                if sleep_time > 0:
                    await logger.awarning("Rate limit reached, sleeping...", sleep_time=round(sleep_time, 2))
                    await asyncio.sleep(sleep_time)
            
            self._request_timestamps.append(time.time())

    async def request(self, method: str, endpoint: str, retries: int = 3, **kwargs) -> Dict[str, Any]:
        """Единый метод для всех запросов к API с retry-логикой."""
        attempt = 0
        while attempt < retries:
            try:
                await self._wait_for_rate_limit()
                
                response = await self._client.request(method, endpoint, **kwargs)
                
                # Обработка ошибок статусов 3xx, 4xx, 5xx
                if response.status_code >= 300:
                    error_data = response.json()
                    error_message = error_data.get("error", "Unknown API error")
                    
                    if response.status_code == 429:
                        raise YouGileRateLimitError(error_message)
                        
                    raise YouGileAPIError(f"HTTP {response.status_code}: {error_message}")
                
                # Для 204 No Content возвращаем пустой словарь
                if response.status_code == 204:
                    return {}
                    
                return response.json()
                
            except (httpx.TimeoutException, httpx.NetworkError) as e:
                attempt += 1
                await logger.aerror("Network error, retrying...", attempt=attempt, error=str(e))
                if attempt >= retries:
                    raise YouGileAPIError(f"Network failure after {retries} attempts") from e
                await asyncio.sleep(2 ** attempt)  # Экспоненциальная задержка
            except YouGileRateLimitError:
                await asyncio.sleep(5) # Если поймали 429 от самого сервера, ждем дольше

    async def close(self):
        await self._client.aclose()