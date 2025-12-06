from django import forms
from .models import Booking


class BookingForm(forms.Form):
    """Form for booking rooms"""
    guest_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your full name'
        })
    )
    guest_email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email'
        })
    )
    guest_phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your phone number'
        })
    )
    num_rooms = forms.ChoiceField(
        choices=[(i, f'{i} Room{"s" if i > 1 else ""}') for i in range(1, 6)],
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

