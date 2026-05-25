# Author: Sparsha Srinath
# Topic: Configuration Manager — Singleton + Strategy + Facade
# Date: 2025-06-15
# Tags: design-patterns, singleton, strategy, facade, low-level-design
#
# Description:
#   A Configuration Manager that reads settings from multiple sources
#   (environment variables, config files, CLI arguments) and provides
#   a unified interface. Uses Singleton to ensure one shared config,
#   Strategy for different source types, and Facade to hide complexity.
#   Sources are loaded with priority: CLI > env vars > file.
#   Later sources override earlier ones via dict.update().
#
# Patterns Used:
#   - Singleton: one shared ConfigManager across the system (__new__ + _instance)
#   - Strategy: each source implements load() differently (file reads JSON,
#     env reads os.environ, CLI reads sys.argv) — same interface, different behavior
#   - Facade: ConfigManager.get() hides the complexity of multiple sources
#
#   Note: This is Strategy, NOT Factory.
#   - Factory decides WHICH class to create based on input
#   - Strategy lets you swap HOW something behaves (different load algorithms)
#
# Priority System:
#   Load order determines priority. Each load_source() calls dict.update(),
#   which overwrites existing keys. So load in this order:
#     1. File   (lowest priority — default settings)
#     2. Env    (overrides file — different per environment)
#     3. CLI    (overrides everything — quick one-time overrides)
#
#   Example: db_host exists in all three sources:
#     File: "localhost" → Env: "production.db" → CLI: "staging.db"
#     Final value: "staging.db" (CLI wins because it loaded last)
#
# Key Python Concepts Used:
#   - dict.get(key, default): returns default if key missing instead of crashing
#   - dict.update(other): merges other dict in, overwriting matching keys
#   - dict.copy(): returns a shallow copy to prevent external mutation
#   - str.split("=", 1): splits only on first "=" so values containing "=" aren't broken
#   - os.environ: dict of all environment variables set in the OS/terminal
#   - sys.argv: list of command line arguments passed when running the script
#   - raise NotImplementedError: makes load() an abstract method subclasses must implement
#
# Usage:
#   config = ConfigManager()
#   config.load_source(FileSource("config.json"))
#   config.load_source(EnvSource(prefix="APP_"))
#   config.load_source(CLISource())
#   config.get("db_host")             # returns value or None
#   config.get("db_port", 5432)       # returns value or 5432 as fallback
#   config.get_all()                  # returns a safe copy of all settings
#
# Interview Notes:
#   - Mention thread safety (double-checked locking) for multithreaded systems
#   - Mention dependency injection as an alternative for testability
#   - .get() is safer than [] for config — missing key returns None instead of KeyError
#   - get_all() returns a copy so external code can't corrupt the shared config


import json
import os
import sys


# ====================
# 1. Strategy — each source loads config differently
#    ConfigSource is the abstract interface (like a base class)
#    Each subclass implements load() its own way
# ====================

class ConfigSource:
    def load(self):
        # Abstract method — subclasses MUST override this
        # Calling this directly raises an error
        raise NotImplementedError


# --- File Source ---
# Reads from a JSON config file committed with your code
# Contains default settings
# Example config.json: {"db_host": "localhost", "db_port": 5432}

class FileSource(ConfigSource):
    def __init__(self, filepath):
        self.filepath = filepath

    def load(self):
        with open(self.filepath, 'r') as f:
            return json.load(f)  # parses JSON file into a dict


# --- Env Source ---
# Reads from environment variables set in the OS/terminal
# Set via: export APP_DB_HOST=production.db.com
# Prefix "APP_" filters only your app's vars from all system vars
# APP_DB_HOST becomes db_host (prefix stripped, lowercased)

class EnvSource(ConfigSource):
    def __init__(self, prefix="APP_"):
        self.prefix = prefix

    def load(self):
        settings = {}
        for key, value in os.environ.items():
            if key.startswith(self.prefix):
                # APP_DB_HOST → db_host
                clean_key = key[len(self.prefix):].lower()
                settings[clean_key] = value
        return settings


# --- CLI Source ---
# Reads from command line arguments passed when running the script
# Run via: python app.py --db_host=staging.db.com --debug=true
# sys.argv = ["app.py", "--db_host=staging.db.com", "--debug=true"]
# sys.argv[1:] skips the script name
# split("=", 1) splits only on first "=" so values with "=" aren't broken
#   e.g. "--message=hello=world" → key="message", value="hello=world"

class CLISource(ConfigSource):
    def load(self):
        settings = {}
        for arg in sys.argv[1:]:
            if arg.startswith("--") and "=" in arg:
                key, value = arg[2:].split("=", 1)
                settings[key] = value
        return settings


# ====================
# 2. Singleton + Facade — one config, simple interface
#    __new__ ensures only one instance exists
#    load_source() merges configs using dict.update() (later wins)
#    get() provides safe access with optional default
#    get_all() returns a copy to prevent external mutation
# ====================

class ConfigManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.settings = {}
        return cls._instance

    def load_source(self, source):
        # update() merges new dict into settings
        # matching keys get overwritten — that's how priority works
        self.settings.update(source.load())

    def get(self, key, default=None):
        # .get() returns None (or default) if key missing — no crash
        # safer than self.settings[key] which raises KeyError
        return self.settings.get(key, default)

    def get_all(self):
        # returns a copy so external code can't modify the original
        # without copy: external changes would corrupt shared config
        return self.settings.copy()


# ====================
# 3. Demo
# ====================

config = ConfigManager()

# Load sources in priority order (lowest first, highest last)
# config.load_source(FileSource("config.json"))   # defaults
# config.load_source(EnvSource(prefix="APP_"))     # env overrides file
# config.load_source(CLISource())                  # CLI overrides everything

# Access config anywhere — same instance
# config.get("db_host")             # value or None
# config.get("db_port", 5432)       # value or 5432 fallback
# config.get_all()                  # safe copy of all settings

# Verify singleton
config2 = ConfigManager()
print(config is config2)  # True — same instance
