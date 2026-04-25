import time
from collections import defaultdict, deque

REQUEST_LOG = defaultdict(deque)

WINDOW_SECONDS = 60
MAX_REQUESTS_PER_WINDOW = 15


def is_rate_limited(client_id: str) -> bool:
    now = time.time()
    bucket = REQUEST_LOG[client_id]

    # išvalom senus requestus
    while bucket and now - bucket[0] > WINDOW_SECONDS:
        bucket.popleft()

    if len(bucket) >= MAX_REQUESTS_PER_WINDOW:
        return True

    bucket.append(now)
    return False