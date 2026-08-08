import os
import time
import signal
import subprocess
from pathlib import Path
from datetime import datetime

from database import Database

# =====================================================
# CONFIG
# =====================================================

BASE_DIR = Path(__file__).resolve().parent
CAPTURE_DIR = Base_DiR / "captures"
CAPTURE_DIR.mkdir(exist_ok=True)

db = Database()

