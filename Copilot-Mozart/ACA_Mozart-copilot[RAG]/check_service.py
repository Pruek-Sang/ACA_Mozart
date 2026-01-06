
try:
    import sys
    import os
    sys.path.append(os.getcwd())
    
    from app.service import RagService
    print("✅ Successfully imported RagService")
except ImportError as e:
    print(f"❌ ImportError: {e}")
    import app.service
    print(f"Available in app.service: {dir(app.service)}")
