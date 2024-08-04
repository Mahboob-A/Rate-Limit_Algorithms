from django.shortcuts import render

from django.http import JsonResponse, HttpResponse


def rlimit_test_view(request): 
        return JsonResponse({"status": "OK"})
