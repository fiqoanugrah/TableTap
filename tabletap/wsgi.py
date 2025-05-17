# tabletap/wsgi.py
import os
import sys

path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if path not in sys.path:
    sys.path.append(path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tabletap.settings')

# Initialize Django
try:
    import django
    django.setup()
    print("Django setup successful")
except Exception as e:
    print(f"Django setup error: {e}")

# Get application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# For Vercel
app = application