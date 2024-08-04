from time import time
from django.http import JsonResponse
from django.core.exceptions import ImproperlyConfigured

import redis


try:
    redis_client = redis.Redis(
        host="rate-limit-redis",
        port=6379,
        db=1,
    )
    redis_client.ping()
except (redis.ConnectionError, ImproperlyConfigured, Exception) as e:
    print("Redis import error: ", str(e))
    raise ImproperlyConfigured("Redis is not properly configured.")


class FixedWindowRateLimitRedisMiddleware:
    """Implementation of Fixed Window Rate Limit using Django Middleware.

    Rules:
        @param: windowMs - Window size in Milisecond
        @param: max_capacity - total capacity
    """

    window_size = {
        "windowMs": 1 * 60 * 1000,  #  1 minute window size in ms
        "max_capacity": 5,  # requests per window
    }

    def __init__(self, get_response) -> None:
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

        if x_forwarded_for:
            ip_addr = x_forwarded_for.split(",")[0]
        else:
            ip_addr = request.META.get("REMOTE_ADDR")

        return ip_addr

    def process_view(self, request, view_func, view_args, view_kwargs):
        """Request phase hook. Will be active just before the actual view is called."""

        client_ip = self.get_client_ip(request=request)

        # however use more comlex and unique key such as user id, session key, or auth key, etc.
        rate_limit_key = f"{client_ip}:1234"

        print("\nrate limit key: ", rate_limit_key)

        curr_time = int(time() * 1000)  # in ms

        try:
            window = redis_client.get(rate_limit_key)
            if window:
                window = eval(window)
        except redis.exceptions.RedisError as e:
            print("Redis Error: ", str(e))
            raise ImproperlyConfigured("Redis is not configured properly.")
        except (redis.ConnectionError, ImproperlyConfigured, Exception) as e:
            print("Redis Error: ", str(e))
            raise ImproperlyConfigured("Redis is not configured properly.")

        # for the first request, no window will be available, assign a window.
        new_window = {"capacity": 1, "timestamp": curr_time}
        if window is None:
            redis_client.set(
                rate_limit_key,
                str(new_window),
                px=self.window_size["windowMs"],
            )

        # winddow was available, but the window size is exceeded. assign a new window.
        elif curr_time - window["timestamp"] > self.window_size["windowMs"]:
            redis_client.set(
                rate_limit_key,
                str(new_window),
                px=self.window_size["windowMs"],
            )

        else:

            # window availalbe, increemnt the capacity
            if window["capacity"] < self.window_size["max_capacity"]:
                window["capacity"] += 1
                redis_client.set(
                    rate_limit_key,
                    str(window),
                    px=self.window_size["windowMs"],
                )

            else:
                # capacity is exhausted.
                return JsonResponse(
                    {
                        "status_code": 429,
                        "status": "too-many-requests",
                    },
                    status=429,
                )

        return None
