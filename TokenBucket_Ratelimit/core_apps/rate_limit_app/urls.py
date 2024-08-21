
from django.urls import path 

from core_apps.rate_limit_app.views import demo_view

urlpatterns = [
        path("test/", demo_view, name="demo_view"), 
]

