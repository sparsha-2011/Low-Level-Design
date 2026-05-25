# Author: Sparsha Srinath
# Topic: Vending Machine — Factory + State + Singleton
# Date: 2025-06-15
# Tags: design-patterns, factory, state, singleton, low-level-design
#
# Description:
#   A Vending Machine that sells different products. Uses Factory to create
#   products, State pattern for machine behavior (idle → has_money →
#   dispensing), and Singleton for the machine itself.
#
# Patterns:
#   - Factory: create_product() builds the right product
#   - State: machine behavior changes based on current state
#     idle: only accepts money
#     has_money: can select product or get refund
#     dispensing: gives product and change
#   - Singleton: one vending machine


# ====================
# 1. Factory — different product types
# ====================

class Product:
    def __init__(self, name, price):
        self.name = name
        self.price = price

    def __repr__(self):
        return f"{self.name} (${self.price})"

def create_product(product_type):
    products = {
        "coke": Product("Coke", 1.50),
        "pepsi": Product("Pepsi", 1.50),
        "water": Product("Water", 1.00),
        "chips": Product("Chips", 2.00),
        "candy": Product("Candy", 0.75),
    }
    if product_type not in products:
        raise ValueError(f"Unknown product: {product_type}")
    return products[product_type]


# ====================
# 2. State — machine behaves differently based on state
#    Each state is a class with the same methods
#    But each handles them differently
# ====================

class State:
    def insert_money(self, machine, amount):
        pass
    def select_product(self, machine, product_type):
        pass
    def dispense(self, machine):
        pass
    def refund(self, machine):
        pass


class IdleState(State):
    # only accepts money in idle state
    def insert_money(self, machine, amount):
        machine.balance = amount
        print(f"Inserted ${amount}")
        machine.state = HasMoneyState()

    def select_product(self, machine, product_type):
        print("Insert money first")

    def refund(self, machine):
        print("No money to refund")


class HasMoneyState(State):
    # can select product or get refund
    def insert_money(self, machine, amount):
        machine.balance += amount
        print(f"Added ${amount} — Balance: ${machine.balance}")

    def select_product(self, machine, product_type):
        try:
            product = create_product(product_type)
        except ValueError as e:
            print(e)
            return

        if machine.balance < product.price:
            print(f"Not enough money. Need ${product.price}, have ${machine.balance}")
            return

        if product_type not in machine.inventory or machine.inventory[product_type] == 0:
            print(f"{product_type} is out of stock")
            return

        machine.selected_product = product
        machine.selected_type = product_type
        machine.state = DispensingState()
        machine.state.dispense(machine)

    def refund(self, machine):
        print(f"Refunded ${machine.balance}")
        machine.balance = 0
        machine.state = IdleState()


class DispensingState(State):
    # gives product and change
    def dispense(self, machine):
        product = machine.selected_product
        machine.inventory[machine.selected_type] -= 1
        change = round(machine.balance - product.price, 2)
        machine.balance = 0
        print(f"Dispensed {product.name}")
        if change > 0:
            print(f"Change: ${change}")
        machine.selected_product = None
        machine.selected_type = None
        machine.state = IdleState()

    def insert_money(self, machine, amount):
        print("Please wait — dispensing")

    def select_product(self, machine, product_type):
        print("Please wait — dispensing")


# ====================
# 3. Vending Machine — Singleton + delegates to current state
# ====================

class VendingMachine:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.state = IdleState()
        self.balance = 0
        self.selected_product = None
        self.selected_type = None
        self.inventory = {
            "coke": 5,
            "pepsi": 3,
            "water": 10,
            "chips": 4,
            "candy": 8,
        }

    # these just delegate to the current state
    # same method call, different behavior depending on state
    def insert_money(self, amount):
        self.state.insert_money(self, amount)

    def select_product(self, product_type):
        self.state.select_product(self, product_type)

    def refund(self):
        self.state.refund(self)

    def show_inventory(self):
        for item, count in self.inventory.items():
            product = create_product(item)
            print(f"  {product.name}: ${product.price} ({count} left)")


# ====================
# Demo
# ====================

vm = VendingMachine()
vm.show_inventory()

vm.select_product("coke")    # Insert money first
vm.insert_money(2.00)        # Inserted $2.00
vm.select_product("coke")    # Dispensed Coke, Change: $0.50

vm.insert_money(0.50)        # Inserted $0.50
vm.select_product("chips")   # Not enough money. Need $2.0, have $0.5
vm.refund()                  # Refunded $0.50
