# Author: Sparsha Srinath
# Topic: Parking Lot — Factory + Strategy + Singleton
# Date: 2025-06-15
# Tags: design-patterns, factory, strategy, singleton, low-level-design
#
# Description:
#   A Parking Lot system that supports multiple vehicle types (car, bike, truck),
#   each requiring different spot sizes. Uses Factory to create vehicles,
#   Strategy for pricing per vehicle type, and Singleton for the parking lot.
#
# Patterns:
#   - Factory: create_vehicle() decides which vehicle class to instantiate
#   - Strategy: each vehicle type has its own pricing logic
#   - Singleton: one parking lot shared across the system


from datetime import datetime


# ====================
# 1. Factory — create different vehicle types
# ====================

class Vehicle:
    def __init__(self, license_plate):
        self.license_plate = license_plate
        self.spot_size = None
        self.rate_per_hour = None

class Car(Vehicle):
    def __init__(self, license_plate):
        super().__init__(license_plate)
        self.spot_size = "medium"
        self.rate_per_hour = 10

class Bike(Vehicle):
    def __init__(self, license_plate):
        super().__init__(license_plate)
        self.spot_size = "small"
        self.rate_per_hour = 5

class Truck(Vehicle):
    def __init__(self, license_plate):
        super().__init__(license_plate)
        self.spot_size = "large"
        self.rate_per_hour = 20

# Factory method — client says "car", gets a Car object
# doesn't need to know Car, Bike, Truck classes exist
def create_vehicle(vehicle_type, license_plate):
    if vehicle_type == "car": return Car(license_plate)
    if vehicle_type == "bike": return Bike(license_plate)
    if vehicle_type == "truck": return Truck(license_plate)
    raise ValueError(f"Unknown vehicle type: {vehicle_type}")


# ====================
# 2. Parking Spot
# ====================

class ParkingSpot:
    def __init__(self, spot_id, size):
        self.spot_id = spot_id
        self.size = size            # "small", "medium", "large"
        self.vehicle = None

    def is_available(self):
        return self.vehicle is None

    def park(self, vehicle):
        self.vehicle = vehicle

    def unpark(self):
        vehicle = self.vehicle
        self.vehicle = None
        return vehicle


# ====================
# 3. Parking Ticket — tracks time for pricing
# ====================

class ParkingTicket:
    def __init__(self, vehicle, spot):
        self.vehicle = vehicle
        self.spot = spot
        self.entry_time = datetime.now()

    def get_cost(self):
        duration = (datetime.now() - self.entry_time).seconds / 3600
        hours = max(1, round(duration))  # minimum 1 hour
        return hours * self.vehicle.rate_per_hour


# ====================
# 4. Parking Lot — Singleton
# ====================

class ParkingLot:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, small=5, medium=5, large=5):
        if self._initialized:
            return
        self._initialized = True
        self.spots = []
        self.active_tickets = {}  # license_plate → ticket

        # create spots of each size
        spot_id = 1
        for _ in range(small):
            self.spots.append(ParkingSpot(spot_id, "small"))
            spot_id += 1
        for _ in range(medium):
            self.spots.append(ParkingSpot(spot_id, "medium"))
            spot_id += 1
        for _ in range(large):
            self.spots.append(ParkingSpot(spot_id, "large"))
            spot_id += 1

    def _find_spot(self, size):
        # find first available spot of the right size
        for spot in self.spots:
            if spot.size == size and spot.is_available():
                return spot
        return None

    def park(self, vehicle):
        spot = self._find_spot(vehicle.spot_size)
        if not spot:
            print(f"No {vehicle.spot_size} spot available")
            return None
        spot.park(vehicle)
        ticket = ParkingTicket(vehicle, spot)
        self.active_tickets[vehicle.license_plate] = ticket
        print(f"Parked {vehicle.license_plate} in spot {spot.spot_id}")
        return ticket

    def unpark(self, license_plate):
        if license_plate not in self.active_tickets:
            print(f"{license_plate} not found")
            return None
        ticket = self.active_tickets.pop(license_plate)
        ticket.spot.unpark()
        cost = ticket.get_cost()
        print(f"Unparked {license_plate} — Cost: ${cost}")
        return cost

    def available_spots(self):
        counts = {"small": 0, "medium": 0, "large": 0}
        for spot in self.spots:
            if spot.is_available():
                counts[spot.size] += 1
        return counts


# ====================
# Demo
# ====================

lot = ParkingLot(small=2, medium=2, large=1)
print(lot.available_spots())  # {'small': 2, 'medium': 2, 'large': 1}

# Factory creates vehicles — client doesn't know which class
car = create_vehicle("car", "ABC-123")
bike = create_vehicle("bike", "XYZ-789")
truck = create_vehicle("truck", "TRK-456")

lot.park(car)     # Parked ABC-123 in spot 3
lot.park(bike)    # Parked XYZ-789 in spot 1
lot.park(truck)   # Parked TRK-456 in spot 5

print(lot.available_spots())  # {'small': 1, 'medium': 1, 'large': 0}

lot.unpark("ABC-123")  # Unparked ABC-123 — Cost: $10
