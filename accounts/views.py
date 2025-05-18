# accounts/views.py
from django.shortcuts import redirect

def home_view(request):
    if not request.user.is_authenticated:
        return redirect('account_login')
    
    # Jika user adalah pemilik restoran
    if hasattr(request.user, 'role') and request.user.role == 'admin':
        return redirect('restaurants:dashboard')
    
    # Jika user adalah staff
    if hasattr(request.user, 'role') and request.user.role == 'staff':
        return redirect('orders:staff_dashboard')
    
    # Default
    return redirect('account_login')