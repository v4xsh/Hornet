import os, sys
def resource_path(relative_path):
    """Get absolute path to resource for dev and PyInstaller"""
    if os.path.isabs(relative_path):
        return relative_path

    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    full_path = os.path.join(base_path, relative_path)
    full_path = os.path.abspath(full_path)  # ✅ Ensures proper C:\... style
    return full_path

