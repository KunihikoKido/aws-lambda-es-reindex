import logging

DEBUG = False

LOG_LEVEL = logging.INFO

TIMEOUT = 30

DEFAULT_SCROLL = '5m'

DEFAULT_SCAN_OPTIONS = {
    "size": 500
}

DEFAULT_BULK_OPTIONS = {
    "chunk_size": 500
}

try:
    from local_settings import *
except ImportError:
    pass
