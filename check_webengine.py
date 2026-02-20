
try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView
    print("QtWebEngineWidgets is available")
except ImportError:
    print("QtWebEngineWidgets is NOT available")
except Exception as e:
    print(f"Error: {e}")
