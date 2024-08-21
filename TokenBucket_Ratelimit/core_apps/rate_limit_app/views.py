from django.shortcuts import render
from django.http.response import JsonResponse
from random import randint

# Create your views here.


def demo_view(request):
    if request.method == "GET":
        return JsonResponse({"status": "success", "value": randint(1, 10000)}, status=200)
