from django.urls import path

from core_apps.rate_limit_app.views import rlimit_test_view

urlpatterns = [
    path("rate-limit/", rlimit_test_view, name="rlimit_test_view"),
]
