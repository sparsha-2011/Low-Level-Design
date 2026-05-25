# Author: Sparsha Srinath
# Topic: Connection Pool — Singleton + Object Pool Pattern
# Date: 2026-05-24
# Tags: design-patterns, singleton, object-pool, low-level-design, threading
#
# Description:
#   A Connection Pool that manages reusable database connections.
#   Creates connections upfront and lends them out on demand.
#   When code is done, it returns the connection instead of destroying it.
#   Uses Singleton so the entire system shares one pool.
#
# Why:
#   Creating a DB connection is expensive (network, auth, memory).
#   Without a pool: every request creates + destroys a connection.
#   With a pool: connections are created once and reused.
#   Analogy: a library — books are bought once, borrowed and returned, not
#   bought new every time someone wants to read and burned when done.
#
# Patterns:
#   - Singleton: one shared pool across the system
#   - Object Pool: reuse expensive objects instead of creating new ones
#
# Key Methods:
#   - acquire(): borrow a connection from the pool
#   - release(conn): return a connection to the pool
#   - available_count(): how many connections are free right now
#   - get_connection(): context manager for auto-release
#
# Two Locks — Two Jobs:
#   - _lock (class level): protects singleton creation
#     prevents two threads from creating two separate pools
#   - _pool_lock (instance level): protects pool operations
#     prevents two threads from grabbing the same connection
#
# Key Python Concepts:
#   - Connection._counter: class variable shared by ALL instances (global ID tracker)
#   - self.id: instance variable unique to each connection, accessible in all methods via self
#   - __repr__: controls what prints when you print the object (readability/debugging)
#   - _initialized flag: prevents __init__ from resetting the pool on every ConnectionPool() call
#     because __new__ returns the same instance but __init__ runs every time
#   - context manager (__enter__/__exit__): auto-releases connection when block ends
#     so you can never forget to release
#
# Interview Notes:
#   - Mention thread safety — multiple threads acquiring at the same time
#   - Mention max pool size — what happens when all connections are in use
#   - Mention connection validation — what if a returned connection is stale/broken
#   - Mention context manager — prevents forgetting to release


import threading


# ====================
# 1. Connection — simulates a database connection
# ====================

class Connection:
    # class variable — shared by ALL instances
    # acts as a global ID tracker, increments with each new connection
    # Connection._counter = shared, self.id = per instance
    _counter = 0

    def __init__(self):
        Connection._counter += 1          # increment the shared counter
        self.id = Connection._counter     # assign unique id to this instance

    def query(self, sql):
        print(f"[Connection {self.id}] Executing: {sql}")

    # __repr__ controls what prints when you print the object
    # without it: <Connection object at 0x7f...> (useless)
    # with it: Connection(1) (useful for debugging)
    def __repr__(self):
        return f"Connection({self.id})"


# ====================
# 2. Connection Pool — Singleton + Object Pool
# ====================

class ConnectionPool:
    _instance = None

    # _lock protects singleton CREATION
    # prevents two threads from creating two separate pools
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:                         # double-checked locking
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, max_connections=5):
        # _initialized flag prevents __init__ from resetting the pool
        # __new__ returns the same instance but __init__ runs every time
        # without this flag: ConnectionPool() would reset all connections
        if self._initialized:
            return
        self._initialized = True
        self.max_connections = max_connections
        self._available = []
        self._in_use = []

        # _pool_lock protects pool OPERATIONS (acquire/release)
        # prevents two threads from grabbing the same connection
        # different from _lock which only protects singleton creation
        self._pool_lock = threading.Lock()

        # create all connections upfront
        for _ in range(max_connections):
            self._available.append(Connection())

    def acquire(self):
        # lock ensures only one thread modifies the pool at a time
        # without lock: two threads could see the same connection
        # and both grab it → broken
        with self._pool_lock:
            if not self._available:
                raise Exception("No connections available")
            conn = self._available.pop()
            conn.in_use = True
            self._in_use.append(conn)
            return conn

    def release(self, conn):
        with self._pool_lock:
            if conn not in self._in_use:
                raise Exception("Connection not from this pool")
            conn.in_use = False
            self._in_use.remove(conn)
            self._available.append(conn)

    def available_count(self):
        return len(self._available)

    def in_use_count(self):
        return len(self._in_use)

    # ====================
    # Context Manager — auto-release so you can never forget
    # Usage: with pool.get_connection() as conn:
    #            conn.query("SELECT ...")
    #        # conn is automatically released here
    # ====================

    class _ConnectionContext:
        def __init__(self, pool):
            self.pool = pool
            self.conn = None

        # __enter__ runs when "with" block starts — acquires connection
        def __enter__(self):
            self.conn = self.pool.acquire()
            return self.conn

        # __exit__ runs when "with" block ends — releases connection
        # runs even if an error occurred inside the block
        def __exit__(self, exc_type, exc_val, exc_tb):
            self.pool.release(self.conn)

    def get_connection(self):
        return self._ConnectionContext(self)


# ====================
# 3. Demo
# ====================

pool = ConnectionPool(max_connections=3)
print(f"Available: {pool.available_count()}")  # 3

# Borrow two connections
conn1 = pool.acquire()
conn2 = pool.acquire()
print(f"Available: {pool.available_count()}")  # 1
print(f"In use: {pool.in_use_count()}")        # 2

# Use the connection
conn1.query("SELECT * FROM users")

# Return one
pool.release(conn1)
print(f"Available: {pool.available_count()}")  # 2

# Context manager — auto-release
with pool.get_connection() as conn:
    conn.query("SELECT * FROM orders")
# conn is automatically released here

# Pool is empty test
conn3 = pool.acquire()
conn4 = pool.acquire()
conn5 = pool.acquire()
try:
    conn6 = pool.acquire()
except Exception as e:
    print(f"Error: {e}")  # No connections available

# Verify singleton
pool2 = ConnectionPool()
print(pool is pool2)  # True — same pool
