#!/usr/bin/env python3

# Test if we can import the module and see the route registration
import sys
sys.path.append('.')

try:
    from src.web.simple_chat_app import app
    print("Import successful!")
    print(f"App instance: {app}")
    print("Routes:")
    for route in app.routes:
        if hasattr(route, 'path'):
            print(f"  - {route.path}")
        elif hasattr(route, 'path_regex'):
            print(f"  - {route.path_regex.pattern}")
    multibot_routes = [r for r in app.routes if hasattr(r, 'path') and 'multibot-status' in r.path]
    print(f"Has multibot-status route: {len(multibot_routes) > 0}")
except ImportError as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()