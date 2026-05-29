from time import monotonic

from fastapi import HTTPException, status
from redis.asyncio import Redis

from app.core import config


class AuthRateLimiter:
    _failures: dict[str, tuple[int, float]] = {}
    _redis: Redis | None = Redis.from_url(config.REDIS_URL, decode_responses=True) if config.REDIS_URL else None

    async def _get_failure_count(self, key: str) -> int:
        if self._redis:
            value = await self._redis.get(self._redis_key(key))
            return int(value or 0)

        now = monotonic()
        count, expires_at = self._failures.get(key, (0, 0))
        if expires_at <= now:
            self._failures.pop(key, None)
            return 0
        return count

    async def _set_failure_count(self, key: str, count: int) -> None:
        if self._redis:
            redis_key = self._redis_key(key)
            await self._redis.set(redis_key, count, ex=config.AUTH_RATE_LIMIT_WINDOW_SECONDS)
            return

        self._failures[key] = (count, monotonic() + config.AUTH_RATE_LIMIT_WINDOW_SECONDS)

    def _raise_limited(self) -> None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="요청 가능 횟수를 초과했습니다. 잠시 후 다시 시도해주세요.",
            headers={"Retry-After": str(config.AUTH_RATE_LIMIT_WINDOW_SECONDS)},
        )

    async def check_login_allowed(self, email: str, client_ip: str) -> None:
        email_key, ip_key = self._login_keys(email, client_ip)
        if await self._get_failure_count(email_key) >= config.AUTH_RATE_LIMIT_MAX_FAILURES:
            self._raise_limited()
        if await self._get_failure_count(ip_key) >= config.AUTH_RATE_LIMIT_MAX_IP_FAILURES:
            self._raise_limited()

    async def record_login_failure(self, email: str, client_ip: str) -> int:
        email_key, ip_key = self._login_keys(email, client_ip)
        email_count = await self._get_failure_count(email_key) + 1
        ip_count = await self._get_failure_count(ip_key) + 1

        await self._set_failure_count(email_key, email_count)
        await self._set_failure_count(ip_key, ip_count)

        remaining = config.AUTH_RATE_LIMIT_MAX_FAILURES - email_count

        if remaining <= 0 or ip_count >= config.AUTH_RATE_LIMIT_MAX_IP_FAILURES:
            self._raise_limited()
        return remaining

    async def reset_login_failures(self, email: str) -> None:
        if self._redis:
            await self._redis.delete(self._redis_key(f"login:email:{email.lower()}"))
            return

        self._failures.pop(f"login:email:{email.lower()}", None)

    def _login_keys(self, email: str, client_ip: str) -> tuple[str, str]:
        normalized_email = email.lower()
        return (f"login:email:{normalized_email}", f"login:ip:{client_ip}")

    def _redis_key(self, key: str) -> str:
        return f"auth-rate-limit:{key}"
