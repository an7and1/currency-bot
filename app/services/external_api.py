import asyncio
import logging

import aiohttp

from app.config import settings

logger = logging.getLogger(__name__)


class ExternalAPIError(Exception):
    pass


class ExternalAPI:
    def __init__(self) -> None:
        self._timeout = aiohttp.ClientTimeout(total=settings.api_timeout)
        self._headers = {"User-Agent": "IT-Jump-Currency-Bot/1.0"}
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self._timeout, headers=self._headers)
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def _get_json(self, url: str, retries: int = 2) -> dict:
        session = await self._get_session()
        last_exc: Exception | None = None
        for attempt in range(retries + 1):
            try:
                async with session.get(url) as resp:
                    if resp.status >= 400:
                        raise ExternalAPIError(f"HTTP {resp.status}")
                    return await resp.json()
            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                last_exc = exc
                logger.warning("API attempt %s failed: %s", attempt + 1, exc)
                if attempt < retries:
                    await asyncio.sleep(0.5 * (2 ** attempt))
            except ExternalAPIError:
                raise
        raise ExternalAPIError(f"network error: {last_exc}")

    async def get_rates(self, base: str = "USD") -> dict:
        url = f"https://open.er-api.com/v6/latest/{base.upper()}"
        data = await self._get_json(url)
        if data.get("result") != "success":
            raise ExternalAPIError("Failed to get rates")
        rates = data.get("rates")
        if not isinstance(rates, dict) or not rates:
            raise ExternalAPIError("Empty rates list")
        return {
            "base": data.get("base_code", base.upper()),
            "date": data.get("time_last_update_utc", ""),
            "rates": rates,
        }
