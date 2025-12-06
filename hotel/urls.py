"""
URL configuration for hotel project.
Hotel Room Reservation System
"""
from django.contrib import admin
from django.urls import path
from hotel_app import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Main pages
    path('', views.home, name='home'),
    path('book/', views.book_room, name='book_room'),
    path('booking/<int:booking_id>/', views.booking_confirmation, name='booking_confirmation'),
    path('rooms/', views.room_status, name='room_status'),
    path('bookings/', views.all_bookings, name='all_bookings'),
    path('cancel/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('initialize/', views.initialize_rooms, name='initialize_rooms'),
    
    # API endpoints
    path('api/room-status/', views.api_get_room_status, name='api_room_status'),
    path('api/find-rooms/', views.api_find_optimal_rooms, name='api_find_rooms'),
    path('api/quick-book/', views.api_quick_book, name='api_quick_book'),
    path('api/reset-all/', views.api_reset_all, name='api_reset_all'),
    path('api/random-occupancy/', views.api_random_occupancy, name='api_random_occupancy'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)