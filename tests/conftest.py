"""
Set required environment variables and stub heavy optional imports so that
extract_transform_load.py can be imported in a lightweight test environment
without openmeteo_requests, requests_cache, or retry_requests installed.
"""
import os
import sys
from unittest.mock import MagicMock

# Required env vars before any module import
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("MONGO_INITDB_ROOT_USERNAME", "test")
os.environ.setdefault("MONGO_INITDB_ROOT_PASSWORD", "test")

# Stub the Open-Meteo / HTTP modules that are not needed by the pure unit tests
for _mod in ("openmeteo_requests", "requests_cache", "retry_requests"):
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()
