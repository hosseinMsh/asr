from django.shortcuts import render

def landing(request): return render(request, "pages/landing.html")
def test_page(request): return render(request, "pages/test.html")
def login_page(request): return render(request, "pages/login.html")
def register_page(request): return render(request, "pages/register.html")
def pricing(request): return render(request, "pages/pricing.html")
def dashboard(request): return render(request, "pages/dashboard.html")
def history(request): return render(request, "pages/history.html")
def account(request): return render(request, "pages/account.html")
def asr_ui(request): return render(request, "pages/asr_recorder.html")
