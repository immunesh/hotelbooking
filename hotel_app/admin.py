from django.contrib import admin
from .models import Room, Booking


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_number', 'floor', 'is_available')
    list_filter = ('floor', 'is_available')
    search_fields = ('room_number',)
    ordering = ('floor', 'room_number')


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_id', 'guest_name', 'guest_email', 'guest_phone', 'total_travel_time', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('guest_name', 'guest_email', 'guest_phone')
    ordering = ('-created_at',)
    filter_horizontal = ('rooms',)