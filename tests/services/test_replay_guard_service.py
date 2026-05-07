from app.services.replay_guard_service import InMemoryReplayStore, RedisReplayStore


def test_in_memory_replay_store_rejects_duplicates_until_expired():
    current_time = [100]

    def time_func():
        return current_time[0]

    store = InMemoryReplayStore(time_func=time_func)

    assert store.mark_seen("abc", 30) is True
    assert store.mark_seen("abc", 30) is False
    current_time[0] = 131
    assert store.mark_seen("abc", 30) is True


def test_redis_replay_store_uses_atomic_set_nx():
    calls = []
    values = [True, None]

    class FakeRedis:
        def set(self, name, value, ex=None, nx=None):
            calls.append(
                {
                    "name": name,
                    "value": value,
                    "ex": ex,
                    "nx": nx,
                }
            )
            return values.pop(0)

    store = RedisReplayStore(
        redis_url="redis://127.0.0.1:6379/0",
        client_factory=lambda redis_url: FakeRedis(),
    )

    assert store.mark_seen("abc", 30) is True
    assert store.mark_seen("abc", 30) is False
    assert calls[0]["name"] == "feishu:replay:abc"
    assert calls[0]["value"] == "1"
    assert calls[0]["ex"] == 30
    assert calls[0]["nx"] is True
