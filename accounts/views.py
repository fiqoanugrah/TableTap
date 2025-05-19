from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.http import HttpResponse
from allauth.account.views import LoginView
from restaurants.models import Restaurant

def home_view(request):
    """Redirect user based on authentication status and role"""
    print("HOME VIEW CALLED")
    print(f"User authenticated: {request.user.is_authenticated}")
    
    if not request.user.is_authenticated:
        return redirect('landing')
    
    # Debug info
    print(f"User: {request.user}")
    print(f"User role: {getattr(request.user, 'role', 'unknown')}")
    
    # Jika user adalah pemilik restoran (admin)
    if hasattr(request.user, 'role') and request.user.role == 'admin':
        try:
            # Cek apakah user memiliki restaurant
            has_restaurant = Restaurant.objects.filter(owner=request.user).exists()
            print(f"User has restaurant: {has_restaurant}")
            
            if has_restaurant:
                return redirect('restaurants:dashboard')
            else:
                # Jika admin tidak memiliki restaurant, redirect ke halaman pembuatan restaurant
                messages.info(request, "You need to create a restaurant first.")
                return redirect('restaurants:create_restaurant')
        except Exception as e:
            print(f"Error checking restaurant: {e}")
            return HttpResponse("Error finding your restaurant. Please contact support.")
    
    # Jika user adalah staff
    if hasattr(request.user, 'role') and request.user.role == 'staff':
        try:
            # Cek apakah user adalah staff di restaurant manapun
            has_restaurant = Restaurant.objects.filter(staff=request.user).exists()
            if has_restaurant:
                return redirect('orders:dashboard')
            else:
                messages.info(request, "You are not assigned to any restaurant yet.")
                return HttpResponse("You are not assigned to any restaurant. Please contact restaurant owner.")
        except Exception as e:
            print(f"Error checking staff restaurant: {e}")
            return HttpResponse("Error finding your restaurant. Please contact support.")
    
    # Default - redirect to landing page
    return redirect('landing')

def landing_view(request):
    """Simple landing page view with check for authenticated users"""
    # If the user is authenticated but doesn't have a restaurant
    # won't force redirect them here - this breaks the loop
    # Just showing different content based on authentication status
    is_authenticated = request.user.is_authenticated
    
    try:
        has_restaurant = False
        if is_authenticated and hasattr(request.user, 'role') and request.user.role == 'admin':
            has_restaurant = Restaurant.objects.filter(owner=request.user).exists()
    except:
        has_restaurant = False
        
    context = {
        'is_authenticated': is_authenticated,
        'has_restaurant': has_restaurant,
    }
    
    return render(request, 'accounts/landing.html', context)

class CustomLoginView(LoginView):
    """Custom login view with role selection"""
    template_name = 'accounts/login.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add roles to context
        context['roles'] = [
            {'value': 'admin', 'name': 'Restaurant Owner'},
            {'value': 'staff', 'name': 'Restaurant Staff'},
        ]
        return context
    
def form_valid(self, form):
    # Get the selected role from the form
    role = self.request.POST.get('role')
    print(f"Selected role: {role}")
    
    # If role isn't submitted, default to 'admin' for now
    if not role:
        role = 'admin'
    
    # Check if user has the selected role
    if not hasattr(form.user, 'role') or form.user.role != role:
        # If user doesn't have a role yet, assign it (for new users)
        # or if we're permissive about role switching:
        form.user.role = role
        form.user.save()
    
    # Login the user
    login(self.request, form.user)
    
    # Redirect based on role
    if role == 'admin':
        # Check if admin has a restaurant
        has_restaurant = Restaurant.objects.filter(owner=form.user).exists()
        if has_restaurant:
            return redirect('restaurants:dashboard')
        else:
            messages.info(self.request, "You need to create a restaurant first.")
            return redirect('restaurants:create_restaurant')
    elif role == 'staff':
        return redirect('orders:dashboard')
    
    return super(CustomLoginView, self).form_valid(form)

def change_role(request):
    """View untuk mengubah role user (untuk testing)"""
    if not request.user.is_authenticated:
        return redirect('account_login')
    
    role = request.GET.get('role', 'admin')
    if role in ['admin', 'staff', 'customer']:
        request.user.role = role
        request.user.save()
        messages.success(request, f"Your role has been changed to {role}.")
    
    return redirect('home')