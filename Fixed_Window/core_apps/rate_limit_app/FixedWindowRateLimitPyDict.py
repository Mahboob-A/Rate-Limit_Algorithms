from time import time
from django.http import JsonResponse


class FixedWindowRateLimitMiddleware:
    """Implementation of Fixed Window Rate Limit using Django Middleware.

    Rules:
        @param: windowMs - Window size in Milisecond
        @param: max_capacity - total capacity
    """

    window_size = {
            "windowMs": 1 * 60 * 1000,  #  1 minute window size in ms
            "max_capacity": 5,  # requests per window
        }   

    # Thick of redis!
    rlimit_window = {}

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
        window = self.rlimit_window.get(rate_limit_key)

        # for the first request, no window will be available, assign a window.
        if window is None:
            self.rlimit_window[rate_limit_key] = {"capacity": 1, "timestamp": curr_time}

        # winddow was available, but the window size is exceeded. assign a new window.
        elif curr_time - window["timestamp"] > self.window_size["windowMs"]:
            self.rlimit_window[rate_limit_key] = {"capacity": 1, "timestamp": curr_time}

        else:

            # window availalbe, increemnt the capacity
            if window["capacity"] < self.window_size["max_capacity"]:
                window["capacity"] += 1

            else:
                # capacity is exhausted.
                return JsonResponse(
                    {
                        "status_code": 429,
                        "status": "too-many-requests",
                    },
                    status=429,
                )

        print("\n window : ", self.rlimit_window[rate_limit_key])
        return None
