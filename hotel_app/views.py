from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib import messages
from .forms import HotelForm, CustomLoginForm, CustomSignupForm
from .models import CustomUser
import random
import requests
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import urllib.parse  # For safely encoding template names



# Home Page View
class HomePage(TemplateView):
    template_name = 'index.html'

# Account Profile View
def account_profile(request):    
    return render(request, 'account-profile.html')



# Hotel admin View
def hotel_dashboard(request):
    if request.method == 'POST':
        form = HotelForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('hotel-admin')  # redirect to same page or success page
    else:
        form = HotelForm()

    return render(request, 'hotel-admin.html', {'form': form})


# Signup View
def signup_view(request):
    if request.method == 'POST':
        form = CustomSignupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Signup successful! Please log in.')
            return redirect('login')
    else:
        form = CustomSignupForm()
    return render(request, 'signup.html', {'form': form})


# Login View
def login_view(request):
    if request.method == 'POST':
        form = CustomLoginForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data.get('identifier')
            password = form.cleaned_data.get('password')

            try:
                user = CustomUser.objects.get(email=identifier)
            except CustomUser.DoesNotExist:
                try:
                    user = CustomUser.objects.get(phone_number=identifier)
                except CustomUser.DoesNotExist:
                    user = None

            if user and user.check_password(password):
                login(request, user)
                messages.success(request, 'Login successful!')
                return redirect('home')
            else:
                messages.error(request, 'Invalid credentials.')
    else:
        form = CustomLoginForm()
    return render(request, 'login.html', {'form': form})

# Logout View
def logout_view(request):
    logout(request)
    messages.info(request, 'You have successfully logged out.')
    return redirect('login')  # ✅ Redirect to login after logout

# forget-password View
User = get_user_model()

# Send SMS using 2Factor AUTOGEN API
def send_sms_via_2factor(phone):
    api_key = settings.TWO_FACTOR_API_KEY
    template_name = urllib.parse.quote("OTP for Login")  # make sure this matches exactly

    url = f"https://2factor.in/API/V1/{api_key}/SMS/{phone}/AUTOGEN"
    print("OTP URL:", url)  # Debug

    response = requests.get(url)
    print("2FACTOR SMS RESPONSE:", response.json())
    return response.json()


# Verify OTP using 2Factor API
def verify_otp_via_2factor(session_id, otp):
    api_key = settings.TWO_FACTOR_API_KEY
    url = f"https://2factor.in/API/V1/{api_key}/SMS/VERIFY/{session_id}/{otp}"

    response = requests.get(url)
    print("2FACTOR VERIFY RESPONSE:", response.json())  # Debugging
    return response.json()

# Forgot Password View
def forgot_password(request):
    context = {}

    if request.method == "POST":
        identifier = request.POST.get("identifier")
        otp = request.POST.get("otp")
        context["identifier"] = identifier  # Pre-fill in form

        if "send_otp" in request.POST:
            try:
                user = User.objects.get(email=identifier) if "@" in identifier else User.objects.get(phone_number=identifier)
                request.session["user_id"] = user.id
                context["otp_sent"] = True

                # Set expiry timestamp
                otp_expiry = (timezone.now() + timedelta(minutes=5)).timestamp()
                request.session["otp_expiry"] = otp_expiry

                if "@" in identifier:
                    # Generate and send email OTP
                    generated_otp = str(random.randint(100000, 999999))
                    request.session["otp"] = generated_otp

                    send_mail(
                        "Your OTP for Login",
                        f"Your OTP is: {generated_otp}\nNote: This OTP will expire in 5 minutes.",
                        settings.EMAIL_HOST_USER,
                        [user.email],
                        fail_silently=False,
                    )
                else:
                    # Send OTP via SMS using 2Factor
                    sms_response = send_sms_via_2factor(user.phone_number)
                    if sms_response.get("Status") != "Success":
                        context["error"] = "SMS sending failed. Try again."
                        return render(request, "forgot-password.html", context)

                    request.session["session_id"] = sms_response.get("Details")

                messages.success(request, "OTP sent successfully.")
            except User.DoesNotExist:
                context["error"] = "User not found."
                return render(request, "forgot-password.html", context)

        elif "verify_otp" in request.POST:
            user_id = request.session.get("user_id")
            otp_expiry = request.session.get("otp_expiry")

            # Expiry check
            if otp_expiry and timezone.now().timestamp() > otp_expiry:
                context["error"] = "OTP has expired. Please request a new one."
                return render(request, "forgot-password.html", context)

            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                context["error"] = "Session expired. Please try again."
                return render(request, "forgot-password.html", context)

            if user.email and user.email == identifier:
                stored_otp = request.session.get("otp")
                if otp == stored_otp:
                    login(request, user)
                    # Invalidate OTP after use
                    for key in ["otp", "otp_expiry", "user_id"]:
                        request.session.pop(key, None)
                    messages.success(request, "Login successful via OTP!")
                    return redirect("home")
                else:
                    context["error"] = "Invalid OTP. Try again."
            else:
                session_id = request.session.get("session_id")
                verify_response = verify_otp_via_2factor(session_id, otp)
                if verify_response.get("Status") == "Success":
                    login(request, user)
                    # Invalidate session after use
                    for key in ["session_id", "otp_expiry", "user_id"]:
                        request.session.pop(key, None)
                    messages.success(request, "Login successful via OTP!")
                    return redirect("home")
                else:
                    context["error"] = "Invalid OTP. Try again."

    return render(request, "forgot-password.html", context)
