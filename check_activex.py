
try:
    from PyQt5.QAxContainer import QAxWidget
    print("QAxContainer is available")
except ImportError:
    print("QAxContainer is NOT available")
except Exception as e:
    print(f"Error: {e}")
