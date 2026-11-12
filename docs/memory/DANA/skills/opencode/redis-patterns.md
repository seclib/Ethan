# Redis Patterns (redis-patterns)

**Source :** `/home/fatsio/.config/opencode/skills/redis-patterns/SKILL.md`  \n**Domaine :** Cache/Bus — Patterns  \n**Type :** Skill technique  \n**Niveau :** Indispensable (Niveau A)  \n

## Description

Redis data structure patterns, caching strategies, distributed locks, rate limiting, pub/sub. Essential for modern applications with caching or message bus needs. Covers Redis hashes, lists, sets, sorted sets, pub/sub patterns, distributed locks with Redlock.

## Main capabilities

- **Caching strategies**: Implements caching patterns (cache-aside, write-through, write-back) with Redis
- **Distributed locks**: Implements distributed locking with Redlock algorithm for coordination across multiple instances
- **Rate limiting**: Implements token bucket and sliding window rate limiting
- **Pub/sub patterns**: Implements publish/subscribe messaging for event-driven architectures
- **Data structure patterns**: Uses Redis hashes, lists, sets, sorted sets for various data types
- **Cache invalidation**: Implements TTL-based and event-driven cache invalidation

## What it can do

- Set up cache-aside pattern for transparent cache look-through
- Implement distributed locks with Redlock for mutual exclusion across services
- Configure rate limiting for API endpoint protection
- Set up Redis pub/sub for event notification systems
- Use Redis hashes for field-level data storage
- Implement sliding window rate limiting for API protection

## When it is useful

- Adding caching to reduce database load
- Implementing distributed coordination between microservices
- Protecting API endpoints from excessive traffic
- Building event-driven architectures with Redis channels
- Storing structured data with Redis hashes
- Implementing rate limiting for SaaS applications

## Practical examples

### Cache-aside pattern

```python
import redis
from django.conf import settings

cache = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)

def get_cached_user(user_id):
    """Get user with cache-aside pattern."""
    cache_key = f"user:{user_id}"
    user = cache.get(cache_key)
    if user is None:
        user = database_get_user(user_id)
        cache.setex(cache_key, 300, json.dumps(user))  # 5-minute TTL
    return user
```

### Distributed lock with Redlock

```python
from redlock import Redlock

redlock = Redlock([f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}"])

lock = redlock.acquire("resource_lock", timeout=30000)
if lock:
    try:
        # Critical section
        perform_operation()
    finally:
        redlock.release(lock)
```

### Rate limiting with sliding window

```python
import time
from collections import deque

class SlidingWindowRateLimiter:
    def __init__(self, rate, window_seconds):
        self.rate = rate  # max requests
        self.window = window_seconds  # time window in seconds
        self.timestamps = deque()
    
    def allow(self):
        now = time.time()
        # Remove timestamps outside the window
        while self.timestamps and self.timestamps[0] < now - self.window:
            self.timestamps.popleft()
        
        # Check if under rate limit
        if len(self.timestamps) < self.rate:
            self.timestamps.append(now)
            return True
        return False
```

## Original source path

`/home/fatsio/.config/opencode/skills/redis-patterns/SKILL.md`

## Classification

- **Domaines :** cache,Redis,distributed locks,rate limiting,pub/sub
- **Statut :** Indispensable (Niveau A)
- **Références :** `monitoring-expert`, `change-impact`, `error-handling`
- **Validé :** Oui (rapport d'analyse stratégique Niveau A)
- **Auteur :** OpenCode Analysis
