# Author: Sparsha Srinath
# Topic: Singleton Pattern — Logger
# Date: 2025-06-15
# Tags: design-patterns, singleton, low-level-design, logger, threading, dependency-injection
# Description:
#   A Logger class using the Singleton pattern to ensure all parts of the system
#   share one logger instance. Supports logging messages with severity levels
#   (INFO, WARNING, ERROR) and retrieving logs filtered by level. Uses __new__
#   to intercept object creation and return the same instance every time.
#   Includes thread-safe variant and dependency injection pattern.
#
# Key Concepts:
#   - __new__ hijacks object creation to enforce single instance
#   - _instance class variable stores the shared instance
#   - All logs collected in one place regardless of where Logger() is called
#   - get_logs supports optional level filtering
#
# Usage:
#   logger = Logger()
#   logger.log("INFO", "Server started")
#   logger.get_logs("ERROR")  # returns only ERROR level logs
#
# Interview Notes:
#   - Mention thread safety (double-checked locking) for multithreaded systems
#   - Mention dependency injection as an alternative for testability


# ====================
# 1. Regular Singleton Logger
# ====================

class Logger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.logs = []
        return cls._instance

    def log(self, level, message):
        entry = {"level": level, "message": message}
        self.logs.append(entry)
        print(f"[{level}]: {message}")

    def get_logs(self, level=None):
        if level is None:
            return self.logs
        return [log for log in self.logs if log['level'] == level]


# Anywhere in the system
logger = Logger()
logger.log("INFO", "Server started")
logger.log("WARNING", "Memory usage high")
logger.log("ERROR", "Database connection failed")
logger.log("INFO", "User logged in")

# Somewhere else entirely
logger2 = Logger()
logger2.log("ERROR", "Payment timeout")

# Same instance — all logs are together
print(logger.get_logs("ERROR"))
print(logger is logger2)  # True


# ====================
# 2. Thread-Safe Variant — add a lock with double-checked locking
# ====================

import threading

class ThreadSafeLogger(Logger):
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.logs = []
        return cls._instance


# ====================
# 3. Dependency Injection — pass logger instead of grabbing singleton
# ====================

class PaymentService:
    def __init__(self, logger):
        self.logger = logger

    def process(self, amount):
        self.logger.log("INFO", f"Processing ${amount}")

# Production
service = PaymentService(Logger())

# Testing — swap in a fake
class FakeLogger:
    def __init__(self):
        self.logs = []
    def log(self, level, message):
        self.logs.append({"level": level, "message": message})

test_service = PaymentService(FakeLogger())
