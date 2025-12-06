from django.db import models
from django.utils import timezone
from itertools import combinations

# Room Model - Represents each room in the hotel
class Room(models.Model):
    room_number = models.IntegerField(unique=True, primary_key=True)
    floor = models.IntegerField()
    is_available = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['room_number']
    
    def __str__(self):
        return f"Room {self.room_number} (Floor {self.floor})"
    
    @staticmethod
    def get_floor_from_room_number(room_number):
        """Extract floor number from room number"""
        return room_number // 100
    
    @staticmethod
    def get_position_on_floor(room_number):
        """Get the position of room on its floor (1-10 or 1-7 for floor 10)"""
        return room_number % 100


# Booking Model - Represents a reservation
class Booking(models.Model):
    booking_id = models.AutoField(primary_key=True)
    guest_name = models.CharField(max_length=100)
    guest_email = models.EmailField()
    guest_phone = models.CharField(max_length=15)
    rooms = models.ManyToManyField(Room, related_name='bookings')
    check_in = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    total_travel_time = models.IntegerField(default=0)  # in minutes
    
    def __str__(self):
        room_numbers = ", ".join([str(r.room_number) for r in self.rooms.all()])
        return f"Booking {self.booking_id}: {self.guest_name} - Rooms: {room_numbers}"


# Room Reservation Logic
class RoomReservationSystem:
    """
    Handles the room reservation logic with travel time optimization.
    
    Building Structure:
    - Floors 1-9: 10 rooms each (101-110, 201-210, ..., 901-910)
    - Floor 10: 7 rooms (1001-1007)
    - Total: 97 rooms
    
    Travel Time:
    - Horizontal: 1 minute per room
    - Vertical: 2 minutes per floor
    """
    
    HORIZONTAL_TIME = 1  # minutes per room
    VERTICAL_TIME = 2    # minutes per floor
    MAX_ROOMS_PER_BOOKING = 5
    
    @staticmethod
    def initialize_rooms():
        """Initialize all 97 rooms in the hotel"""
        rooms_created = 0
        
        # Floors 1-9: 10 rooms each
        for floor in range(1, 10):
            for room in range(1, 11):
                room_number = floor * 100 + room
                Room.objects.get_or_create(
                    room_number=room_number,
                    defaults={'floor': floor, 'is_available': True}
                )
                rooms_created += 1
        
        # Floor 10: 7 rooms
        for room in range(1, 8):
            room_number = 1000 + room
            Room.objects.get_or_create(
                room_number=room_number,
                defaults={'floor': 10, 'is_available': True}
            )
            rooms_created += 1
        
        return rooms_created
    
    @staticmethod
    def calculate_travel_time(room1, room2):
        """
        Calculate travel time between two rooms.
        Horizontal: 1 min/room, Vertical: 2 min/floor
        """
        floor1 = room1.floor
        floor2 = room2.floor
        pos1 = Room.get_position_on_floor(room1.room_number)
        pos2 = Room.get_position_on_floor(room2.room_number)
        
        # Vertical travel time (between floors)
        vertical_time = abs(floor2 - floor1) * RoomReservationSystem.VERTICAL_TIME
        
        # Horizontal travel time (between room positions)
        horizontal_time = abs(pos2 - pos1) * RoomReservationSystem.HORIZONTAL_TIME
        
        return vertical_time + horizontal_time
    
    @staticmethod
    def calculate_total_travel_time(rooms):
        """
        Calculate total travel time for a set of rooms.
        This is the time from the first room to the last room in the booking.
        """
        if len(rooms) <= 1:
            return 0
        
        # Sort rooms by floor, then by position
        sorted_rooms = sorted(rooms, key=lambda r: (r.floor, r.room_number))
        
        # Calculate travel time from first to last room
        total_time = 0
        for i in range(len(sorted_rooms) - 1):
            total_time += RoomReservationSystem.calculate_travel_time(
                sorted_rooms[i], sorted_rooms[i + 1]
            )
        
        return total_time
    
    @staticmethod
    def get_available_rooms():
        """Get all available rooms"""
        return Room.objects.filter(is_available=True).order_by('floor', 'room_number')
    
    @staticmethod
    def get_available_rooms_by_floor():
        """Get available rooms grouped by floor"""
        available_rooms = RoomReservationSystem.get_available_rooms()
        floors = {}
        for room in available_rooms:
            if room.floor not in floors:
                floors[room.floor] = []
            floors[room.floor].append(room)
        return floors
    
    @staticmethod
    def find_optimal_rooms(num_rooms):
        """
        Find optimal rooms for booking based on minimizing travel time.
        
        Priority:
        1. Book rooms on the same floor first
        2. If not possible, minimize total travel time across floors
        
        Args:
            num_rooms: Number of rooms to book (1-5)
        
        Returns:
            tuple: (list of optimal rooms, total travel time) or (None, None) if not possible
        """
        if num_rooms < 1 or num_rooms > RoomReservationSystem.MAX_ROOMS_PER_BOOKING:
            return None, None
        
        available_rooms = list(RoomReservationSystem.get_available_rooms())
        
        if len(available_rooms) < num_rooms:
            return None, None
        
        if num_rooms == 1:
            # For single room, just return the first available (closest to stairs)
            return [available_rooms[0]], 0
        
        # Group rooms by floor
        floors = RoomReservationSystem.get_available_rooms_by_floor()
        
        best_rooms = None
        min_travel_time = float('inf')
        
        # Priority 1: Try to find rooms on the same floor
        for floor, rooms in floors.items():
            if len(rooms) >= num_rooms:
                # Find the best combination on this floor
                for combo in combinations(rooms, num_rooms):
                    travel_time = RoomReservationSystem.calculate_total_travel_time(list(combo))
                    if travel_time < min_travel_time:
                        min_travel_time = travel_time
                        best_rooms = list(combo)
        
        # If we found rooms on the same floor, return them
        if best_rooms is not None:
            return best_rooms, min_travel_time
        
        # Priority 2: Find rooms across floors with minimum travel time
        # For efficiency, we'll check combinations starting from lower floors
        # and prioritize adjacent floors
        
        # Get all combinations of available rooms
        # For large numbers, we need to be smart about this
        if len(available_rooms) <= 20:
            # For small number of available rooms, check all combinations
            for combo in combinations(available_rooms, num_rooms):
                travel_time = RoomReservationSystem.calculate_total_travel_time(list(combo))
                if travel_time < min_travel_time:
                    min_travel_time = travel_time
                    best_rooms = list(combo)
        else:
            # For larger numbers, use a greedy approach
            # Start from the floor with most available rooms
            sorted_floors = sorted(floors.items(), key=lambda x: -len(x[1]))
            
            # Try to fill from adjacent floors
            for start_floor, start_rooms in sorted_floors:
                candidate_rooms = list(start_rooms)
                
                # Add rooms from adjacent floors
                for offset in range(1, 11):
                    for floor_offset in [offset, -offset]:
                        adjacent_floor = start_floor + floor_offset
                        if adjacent_floor in floors:
                            candidate_rooms.extend(floors[adjacent_floor])
                        if len(candidate_rooms) >= num_rooms:
                            break
                    if len(candidate_rooms) >= num_rooms:
                        break
                
                if len(candidate_rooms) >= num_rooms:
                    # Find best combination from candidates
                    for combo in combinations(candidate_rooms[:min(len(candidate_rooms), num_rooms * 3)], num_rooms):
                        travel_time = RoomReservationSystem.calculate_total_travel_time(list(combo))
                        if travel_time < min_travel_time:
                            min_travel_time = travel_time
                            best_rooms = list(combo)
        
        return best_rooms, min_travel_time if best_rooms else (None, None)
    
    @staticmethod
    def book_rooms(guest_name, guest_email, guest_phone, num_rooms):
        """
        Book rooms for a guest.
        
        Args:
            guest_name: Name of the guest
            guest_email: Email of the guest
            guest_phone: Phone number of the guest
            num_rooms: Number of rooms to book (1-5)
        
        Returns:
            tuple: (Booking object, message) or (None, error message)
        """
        if num_rooms < 1:
            return None, "Please select at least 1 room."
        
        if num_rooms > RoomReservationSystem.MAX_ROOMS_PER_BOOKING:
            return None, f"Maximum {RoomReservationSystem.MAX_ROOMS_PER_BOOKING} rooms can be booked at a time."
        
        optimal_rooms, travel_time = RoomReservationSystem.find_optimal_rooms(num_rooms)
        
        if optimal_rooms is None:
            available_count = Room.objects.filter(is_available=True).count()
            return None, f"Not enough rooms available. Only {available_count} rooms are available."
        
        # Create booking
        booking = Booking.objects.create(
            guest_name=guest_name,
            guest_email=guest_email,
            guest_phone=guest_phone,
            total_travel_time=travel_time
        )
        
        # Mark rooms as booked and add to booking
        for room in optimal_rooms:
            room.is_available = False
            room.save()
            booking.rooms.add(room)
        
        booking.save()
        
        room_numbers = [r.room_number for r in optimal_rooms]
        return booking, f"Successfully booked rooms: {room_numbers}. Total travel time: {travel_time} minutes."
    
    @staticmethod
    def cancel_booking(booking_id):
        """
        Cancel a booking and release the rooms.
        
        Args:
            booking_id: ID of the booking to cancel
        
        Returns:
            tuple: (success boolean, message)
        """
        try:
            booking = Booking.objects.get(booking_id=booking_id)
            
            # Release all rooms
            for room in booking.rooms.all():
                room.is_available = True
                room.save()
            
            # Delete booking
            booking.delete()
            
            return True, f"Booking {booking_id} has been cancelled successfully."
        except Booking.DoesNotExist:
            return False, f"Booking {booking_id} not found."
    
    @staticmethod
    def get_room_status():
        """Get status of all rooms grouped by floor"""
        all_rooms = Room.objects.all().order_by('floor', 'room_number')
        floors = {}
        
        for room in all_rooms:
            if room.floor not in floors:
                floors[room.floor] = []
            floors[room.floor].append({
                'room_number': room.room_number,
                'is_available': room.is_available,
                'position': Room.get_position_on_floor(room.room_number)
            })
        
        return floors
    
    @staticmethod
    def get_statistics():
        """Get hotel statistics"""
        total_rooms = Room.objects.count()
        available_rooms = Room.objects.filter(is_available=True).count()
        booked_rooms = total_rooms - available_rooms
        total_bookings = Booking.objects.count()
        
        return {
            'total_rooms': total_rooms,
            'available_rooms': available_rooms,
            'booked_rooms': booked_rooms,
            'occupancy_rate': round((booked_rooms / total_rooms * 100), 1) if total_rooms > 0 else 0,
            'total_bookings': total_bookings
        }