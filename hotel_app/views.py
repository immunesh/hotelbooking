from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .models import Room, Booking, RoomReservationSystem
import json
import random


def home(request):
    """Home page with hotel overview and statistics"""
    # Initialize rooms if not already done
    if Room.objects.count() == 0:
        RoomReservationSystem.initialize_rooms()
    
    stats = RoomReservationSystem.get_statistics()
    room_status = RoomReservationSystem.get_room_status()
    
    # Convert room_status to JSON-serializable format
    room_status_json = json.dumps(room_status)
    
    context = {
        'stats': stats,
        'room_status': room_status_json,
    }
    return render(request, 'index.html', context)


def book_room(request):
    """Room booking page"""
    if request.method == 'POST':
        guest_name = request.POST.get('guest_name', '').strip()
        guest_email = request.POST.get('guest_email', '').strip()
        guest_phone = request.POST.get('guest_phone', '').strip()
        num_rooms = request.POST.get('num_rooms', 1)
        
        try:
            num_rooms = int(num_rooms)
        except ValueError:
            messages.error(request, 'Invalid number of rooms.')
            return redirect('book_room')
        
        # Validate inputs
        if not guest_name or not guest_email or not guest_phone:
            messages.error(request, 'Please fill in all required fields.')
            return redirect('book_room')
        
        # Attempt to book rooms
        booking, message = RoomReservationSystem.book_rooms(
            guest_name, guest_email, guest_phone, num_rooms
        )
        
        if booking:
            messages.success(request, message)
            return redirect('booking_confirmation', booking_id=booking.booking_id)
        else:
            messages.error(request, message)
            return redirect('book_room')
    
    # GET request - show booking form
    stats = RoomReservationSystem.get_statistics()
    context = {
        'stats': stats,
        'max_rooms': RoomReservationSystem.MAX_ROOMS_PER_BOOKING,
    }
    return render(request, 'book_room.html', context)


def booking_confirmation(request, booking_id):
    """Booking confirmation page"""
    try:
        booking = Booking.objects.get(booking_id=booking_id)
        rooms = booking.rooms.all().order_by('floor', 'room_number')
        
        context = {
            'booking': booking,
            'rooms': rooms,
        }
        return render(request, 'booking_confirmation.html', context)
    except Booking.DoesNotExist:
        messages.error(request, 'Booking not found.')
        return redirect('home')


def room_status(request):
    """Display room availability status"""
    # Initialize rooms if not already done
    if Room.objects.count() == 0:
        RoomReservationSystem.initialize_rooms()
    
    room_status = RoomReservationSystem.get_room_status()
    stats = RoomReservationSystem.get_statistics()
    
    context = {
        'room_status': room_status,
        'stats': stats,
    }
    return render(request, 'room_status.html', context)


def all_bookings(request):
    """View all bookings"""
    bookings = Booking.objects.all().order_by('-created_at')
    stats = RoomReservationSystem.get_statistics()
    
    context = {
        'bookings': bookings,
        'stats': stats,
    }
    return render(request, 'all_bookings.html', context)


def cancel_booking(request, booking_id):
    """Cancel a booking"""
    if request.method == 'POST':
        success, message = RoomReservationSystem.cancel_booking(booking_id)
        
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)
    
    return redirect('all_bookings')


def initialize_rooms(request):
    """Initialize or reset all rooms"""
    if request.method == 'POST':
        # Reset all rooms to available
        Room.objects.all().delete()
        Booking.objects.all().delete()
        
        count = RoomReservationSystem.initialize_rooms()
        messages.success(request, f'Successfully initialized {count} rooms.')
    
    return redirect('room_status')


# API endpoints for AJAX requests
def api_get_room_status(request):
    """API endpoint to get room status"""
    room_status = RoomReservationSystem.get_room_status()
    stats = RoomReservationSystem.get_statistics()
    
    return JsonResponse({
        'room_status': room_status,
        'stats': stats,
    })


def api_find_optimal_rooms(request):
    """API endpoint to find optimal rooms without booking"""
    num_rooms = request.GET.get('num_rooms', 1)
    
    try:
        num_rooms = int(num_rooms)
    except ValueError:
        return JsonResponse({'error': 'Invalid number of rooms'}, status=400)
    
    optimal_rooms, travel_time = RoomReservationSystem.find_optimal_rooms(num_rooms)
    
    if optimal_rooms:
        return JsonResponse({
            'success': True,
            'rooms': [{'room_number': r.room_number, 'floor': r.floor} for r in optimal_rooms],
            'travel_time': travel_time,
        })
    else:
        available_count = Room.objects.filter(is_available=True).count()
        return JsonResponse({
            'success': False,
            'message': f'Not enough rooms available. Only {available_count} rooms available.',
        })


@csrf_exempt
def api_quick_book(request):
    """API endpoint for quick booking (just number of rooms)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            num_rooms = int(data.get('num_rooms', 1))
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)
        
        # Quick booking with default guest info
        booking, message = RoomReservationSystem.book_rooms(
            guest_name=f'Guest_{random.randint(1000, 9999)}',
            guest_email=f'guest{random.randint(1000, 9999)}@hotel.com',
            guest_phone=f'+1{random.randint(1000000000, 9999999999)}',
            num_rooms=num_rooms
        )
        
        if booking:
            booked_rooms = [r.room_number for r in booking.rooms.all()]
            return JsonResponse({
                'success': True,
                'message': message,
                'booking_id': booking.booking_id,
                'rooms': booked_rooms,
                'travel_time': booking.total_travel_time
            })
        else:
            return JsonResponse({'success': False, 'message': message})
    
    return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)


@csrf_exempt
def api_reset_all(request):
    """API endpoint to reset all bookings and rooms"""
    if request.method == 'POST':
        # Delete all bookings
        Booking.objects.all().delete()
        
        # Reset all rooms to available
        Room.objects.all().update(is_available=True)
        
        stats = RoomReservationSystem.get_statistics()
        return JsonResponse({
            'success': True,
            'message': 'All bookings have been reset. All 97 rooms are now available.',
            'stats': stats
        })
    
    return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)


@csrf_exempt
def api_random_occupancy(request):
    """API endpoint to generate random room occupancy"""
    if request.method == 'POST':
        # First reset all rooms
        Booking.objects.all().delete()
        Room.objects.all().update(is_available=True)
        
        # Randomly book some rooms (30-70% occupancy)
        all_rooms = list(Room.objects.all())
        occupancy_rate = random.uniform(0.3, 0.7)
        num_rooms_to_book = int(len(all_rooms) * occupancy_rate)
        
        # Randomly select rooms to mark as booked
        rooms_to_book = random.sample(all_rooms, num_rooms_to_book)
        
        # Create random bookings
        booking_count = 0
        i = 0
        while i < len(rooms_to_book):
            # Random booking size (1-5 rooms)
            booking_size = min(random.randint(1, 5), len(rooms_to_book) - i)
            booking_rooms = rooms_to_book[i:i + booking_size]
            
            # Create booking
            booking = Booking.objects.create(
                guest_name=f'Guest_{random.randint(1000, 9999)}',
                guest_email=f'guest{random.randint(1000, 9999)}@hotel.com',
                guest_phone=f'+1{random.randint(1000000000, 9999999999)}',
                total_travel_time=random.randint(0, 20)
            )
            
            for room in booking_rooms:
                room.is_available = False
                room.save()
                booking.rooms.add(room)
            
            booking.save()
            booking_count += 1
            i += booking_size
        
        stats = RoomReservationSystem.get_statistics()
        return JsonResponse({
            'success': True,
            'message': f'Generated random occupancy: {stats["booked_rooms"]} rooms booked across {booking_count} bookings.',
            'stats': stats
        })
    
    return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)
