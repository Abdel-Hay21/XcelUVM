import platform
import ctypes

def apply_dark_titlebar(window):
    """
    Applies the native dark mode and custom colors to the Windows title bar.
    This provides a seamless, native look without losing OS window snapping.
    """
    try:
        hwnd = int(window.winId())
        set_window_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
        
        # 1. Enable immersive dark mode (works on Windows 10 and 11)
        rendering_policy = ctypes.c_int(2) # 2 = Dark mode
        # Windows 11
        set_window_attribute(hwnd, 20, ctypes.byref(rendering_policy), ctypes.sizeof(rendering_policy))
        # Windows 10
        set_window_attribute(hwnd, 19, ctypes.byref(rendering_policy), ctypes.sizeof(rendering_policy))
        
        # 2. Windows 11 specific: Customize the exact title bar color
        # Platform version e.g. '10.0.22000' -> build 22000 is Windows 11
        if int(platform.version().split('.')[2]) >= 22000:
            # DWMWA_CAPTION_COLOR = 35
            # Color is specified as 0x00bbggrr (BGR format instead of RGB)
            # Background #0f1117: R=0x0f, G=0x11, B=0x17 => 0x0017110f
            bg_color = ctypes.c_int(0x0017110f)
            set_window_attribute(hwnd, 35, ctypes.byref(bg_color), ctypes.sizeof(bg_color))
            
            # DWMWA_TEXT_COLOR = 36
            # Text color #e2e8f0: R=0xe2, G=0xe8, B=0xf0 => 0x00f0e8e2
            text_color = ctypes.c_int(0x00f0e8e2)
            set_window_attribute(hwnd, 36, ctypes.byref(text_color), ctypes.sizeof(text_color))
            
    except Exception as e:
        # Fails silently on non-Windows or if unsupported
        pass
