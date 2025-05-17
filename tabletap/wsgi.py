# tabletap/wsgi.py
import os
import sys

from django.core.wsgi import get_wsgi_application

# Tambahkan path proyek ke Python path
path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if path not in sys.path:
    sys.path.append(path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tabletap.settings')

# Simple application
application = get_wsgi_application()

# Untuk Vercel
app = application