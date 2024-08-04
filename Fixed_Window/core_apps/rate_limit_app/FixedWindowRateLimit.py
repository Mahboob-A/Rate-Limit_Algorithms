from time import time
from django.http import JsonResponse


class FixedWindowRateLimitMiddleware:
    """Implementation of Fixed Window Rate Limit using Django Middleware.

    Rules:
        @param: windowMs - Window size in Milisecond
        @param: capacity - current capacity
        @param: max_capacity - total capacity
    """

    window_size = {
        "windowMs": 1 * 60 * 1000,  #  1 minute window size in ms 
        "max_capacity": 5,  # requests per window
    }

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

        # chack window availability
        client_ip = self.get_client_ip(request=request)

        # however use more comlex and unique key
        rate_limit_key = f"{client_ip}:1234"
        curr_time = int(time() * 1000)       
        print("curr time: ", curr_time)
        window = self.rlimit_window.get(rate_limit_key)

        print("\nwindow up: ", window)

        if window is None:
            print("\nin first if block")
            self.rlimit_window[rate_limit_key] = {
                "capacity": 1, 
                "timestamp": curr_time
            }
            print("\n new window: ", self.rlimit_window[rate_limit_key])
        elif curr_time - window["timestamp"] > self.window_size["windowMs"]:
            print("\nin elif block")
            print("time in window: ", window["timestamp"])
            self.rlimit_window[rate_limit_key] = {
                "capacity": 1, 
                "timestamp": curr_time
            }
            print("\n elif new window: ", self.rlimit_window[rate_limit_key])
        else: 

            if window["capacity"] < self.window_size["max_capacity"]:
                print("\nin if block of 2nd else ")
                window["capacity"] += 1 
                print("\n new 2nd else block window: ", self.rlimit_window[rate_limit_key])
            else: 
                print("\nrate limit caught => to - many - requests")
                return JsonResponse(
                        {
                            "status_code": 429,
                            "status": "to-many-requests",
                        },
                        status=429,
                    )

        print("\nwindow down: ", self.rlimit_window[rate_limit_key])
        print("\nrate limit passed.")
        return None
