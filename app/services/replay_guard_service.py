import time

from redis import Redis


class InMemoryReplayStore:
    def __init__(self, time_func=None):
        self.time_func = time_func or time.time
        self._expires_at = {}

    def mark_seen(self, replay_key, ttl_seconds):
        now = int(self.time_func())
        self._cleanup(now)
        expires_at = self._expires_at.get(replay_key)
        if expires_at is not None and expires_at > now:
            return False
        self._expires_at[replay_key] = now + ttl_seconds
        return True

    def _cleanup(self, now):
        expired_keys = [replay_key for replay_key, expires_at in self._expires_at.items() if expires_at <= now]
        for replay_key in expired_keys:
            self._expires_at.pop(replay_key, None)


class RedisReplayStore:
    def __init__(self, redis_url, key_prefix="feishu:replay", client_factory=None):
        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self.client_factory = client_factory or self._default_client_factory
        self._client = None

    def mark_seen(self, replay_key, ttl_seconds):
        client = self._get_client()
        created = client.set(self._build_key(replay_key), "1", ex=ttl_seconds, nx=True)
        return bool(created)

    def _get_client(self):
        if self._client is None:
            self._client = self.client_factory(self.redis_url)
        return self._client

    def _build_key(self, replay_key):
        return "{0}:{1}".format(self.key_prefix, replay_key)

    def _default_client_factory(self, redis_url):
        return Redis.from_url(redis_url, decode_responses=True)
