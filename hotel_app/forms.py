from django import forms
from .models import Hotel
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

# signup form
class CustomSignupForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=15)

    class Meta:
        model = CustomUser
        fields = ['email', 'phone_number', 'password1', 'password2']

# login form
class CustomLoginForm(forms.Form):
    identifier = forms.CharField(label="Email or Phone")
    password = forms.CharField(widget=forms.PasswordInput)

# hotel admin deshboard
class HotelForm(forms.ModelForm):
    class Meta:
        model = Hotel
        fields = ['image', 'name', 'email', 'phone', 'country', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your Hotel name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email id'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your phone number'}),
            'country': forms.Select(attrs={'class': 'form-select'}, choices=[('USA', 'USA'), ('Paris', 'Paris'), ('India', 'India'), ('UK', 'UK')]),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter your Address'}),

        }

