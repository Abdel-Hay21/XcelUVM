import os
import sys

if getattr(sys, 'frozen', False):
    # Running as a PyInstaller EXE — everything lives next to the .exe
    _APP_DIR = os.path.dirname(sys.executable)
else:
    # Running from source — go two levels up from core/ → UVM_tool/
    _APP_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

BACKEND_DIR      = os.path.join(_APP_DIR, "Backend", "Backend_tcl")
BACKEND_AI_DIR   = os.path.join(_APP_DIR, "Backend", "Backend_AI")
BACKEND_SELF_DIR = os.path.join(_APP_DIR, "Backend", "Backend_self")
FRONTEND_DIR     = _APP_DIR if getattr(sys, 'frozen', False) else os.path.join(_APP_DIR, "Frontend")
IMAGE_DIR        = os.path.join(FRONTEND_DIR, "image")

import tempfile

def get_run_tcl():
    return os.path.join(tempfile.gettempdir(), "run.tcl").replace("\\", "/")

def get_image_path(filename):
    """Return the absolute path to an image file — works in both dev and EXE modes."""
    return os.path.join(IMAGE_DIR, filename).replace("\\", "/")

LOGO_PATH = get_image_path("Logo.png")
