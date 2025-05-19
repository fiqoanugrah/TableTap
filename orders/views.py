from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count
from django.http import HttpResponse
from .models import Order
from restaurants.models import Restaurant

@login_required
def dashboard(request):
    """Staff dashboard view"""
    # Debug info
    print("ORDERS DASHBOARD CALLED")
    print(f"User: {request.user}, Role: {getattr(request.user, 'role', 'unknown')}")
    
    # Verifikasi user adalah admin atau staff
    if not hasattr(request.user, 'role') or (request.user.role != 'admin' and request.user.role != 'staff'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('account_login')
    
    # Mendapatkan restaurant berdasarkan peran user
    restaurant = None
    
    try:
        # Untuk admin/owner, cari restaurant yang dimiliki
        if request.user.role == 'admin':
            restaurant = Restaurant.objects.filter(owner=request.user).first()
            print(f"Found restaurant for admin: {restaurant}")
        # Untuk staff, cari restaurant tempat mereka bekerja
        elif request.user.role == 'staff':
            # Pastikan ManyToMany relationship sudah dikonfigurasi
            restaurant = Restaurant.objects.filter(staff=request.user).first()
            print(f"Found restaurant for staff: {restaurant}")
    except Exception as e:
        print(f"Error finding restaurant: {e}")
    
    # Jika restaurant tidak ditemukan, ambil restaurant pertama untuk sementara (untuk testing)
    if not restaurant:
        restaurant = Restaurant.objects.first()
        print(f"Using first restaurant as fallback: {restaurant}")
    
    if not restaurant:
        messages.error(request, "No restaurant found. Please contact administrator.")
        # PENTING: Jangan redirect ke restaurants:dashboard, ini penyebab loop
        return HttpResponse("No restaurant found. Please contact administrator.")
    
    # Hitung pesanan berdasarkan status
    pending_count = Order.objects.filter(restaurant=restaurant, status='pending').count()
    preparing_count = Order.objects.filter(restaurant=restaurant, status='preparing').count()
    ready_count = Order.objects.filter(restaurant=restaurant, status='ready').count()
    
    # Ambil pesanan hari ini
    today = timezone.now().date()
    today_count = Order.objects.filter(
        restaurant=restaurant,
        created_at__date=today
    ).count()
    
    # Ambil pesanan terbaru (10 terakhir)
    recent_orders = Order.objects.filter(
        restaurant=restaurant
    ).order_by('-created_at')[:10]
    
    context = {
        'restaurant': restaurant,
        'pending_count': pending_count,
        'preparing_count': preparing_count,
        'ready_count': ready_count,
        'today_count': today_count,
        'recent_orders': recent_orders,
        'active_menu': 'dashboard'
    }
    
    print("Rendering orders/dashboard.html")
    return render(request, 'orders/dashboard.html', context)

@login_required
def order_list(request):
    """Display a list of orders with filtering options"""
    # Verifikasi user adalah admin atau staff
    if not hasattr(request.user, 'role') or (request.user.role != 'admin' and request.user.role != 'staff'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('account_login')
    
    # Mendapatkan restaurant berdasarkan peran user
    restaurant = None
    
    try:
        # Untuk admin/owner, cari restaurant yang dimiliki
        if request.user.role == 'admin':
            restaurant = Restaurant.objects.filter(owner=request.user).first()
        # Untuk staff, cari restaurant tempat mereka bekerja
        elif request.user.role == 'staff':
            restaurant = Restaurant.objects.filter(staff=request.user).first()
    except Exception as e:
        print(f"Error finding restaurant: {e}")
    
    # Jika restaurant tidak ditemukan, ambil restaurant pertama untuk sementara
    if not restaurant:
        restaurant = Restaurant.objects.first()
    
    if not restaurant:
        messages.error(request, "No restaurant found. Please contact administrator.")
        return HttpResponse("No restaurant found. Please contact administrator.")
    
    # Get filter parameters
    status = request.GET.get('status', 'pending')
    date_filter = request.GET.get('date', None)
    
    # Base query
    orders = Order.objects.filter(restaurant=restaurant)
    
    # Apply filters
    active_menu = 'all'
    status_display = 'All'
    
    if date_filter == 'today':
        today = timezone.now().date()
        orders = orders.filter(created_at__date=today)
        status_display = "Today's"
    elif status != 'all':
        orders = orders.filter(status=status)
        active_menu = status
        # Get the display name of the status
        for status_code, status_label in Order.STATUS_CHOICES:
            if status_code == status:
                status_display = status_label
    
    # Sort orders
    orders = orders.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(orders, 25)  # 25 orders per page
    page = request.GET.get('page', 1)
    
    try:
        orders_page = paginator.page(page)
    except PageNotAnInteger:
        orders_page = paginator.page(1)
    except EmptyPage:
        orders_page = paginator.page(paginator.num_pages)
    
    context = {
        'restaurant': restaurant,
        'orders': orders_page,
        'status': status,
        'date': date_filter,
        'status_display': status_display,
        'active_menu': active_menu
    }
    
    return render(request, 'orders/order_list.html', context)

@login_required
def order_detail(request, order_id):
    """Display details for a specific order"""
    # Verifikasi user adalah admin atau staff
    if not hasattr(request.user, 'role') or (request.user.role != 'admin' and request.user.role != 'staff'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('account_login')
    
    # Mendapatkan restaurant berdasarkan peran user
    restaurant = None
    
    try:
        # Untuk admin/owner, cari restaurant yang dimiliki
        if request.user.role == 'admin':
            restaurant = Restaurant.objects.filter(owner=request.user).first()
        # Untuk staff, cari restaurant tempat mereka bekerja
        elif request.user.role == 'staff':
            restaurant = Restaurant.objects.filter(staff=request.user).first()
    except Exception as e:
        print(f"Error finding restaurant: {e}")
    
    # Jika restaurant tidak ditemukan, ambil restaurant pertama untuk sementara
    if not restaurant:
        restaurant = Restaurant.objects.first()
    
    if not restaurant:
        messages.error(request, "No restaurant found. Please contact administrator.")
        return HttpResponse("No restaurant found. Please contact administrator.")
    
    # Get the order, ensuring it belongs to the user's restaurant
    order = get_object_or_404(Order, id=order_id, restaurant=restaurant)
    
    # Determine the active menu item based on order status
    active_menu = order.status
    
    context = {
        'restaurant': restaurant,
        'order': order,
        'active_menu': active_menu
    }
    
    return render(request, 'orders/order_detail.html', context)

@login_required
def update_status(request, order_id):
    """Update the status of an order"""
    if request.method != 'POST':
        return redirect('orders:order_detail', order_id=order_id)
    
    # Verifikasi user adalah admin atau staff
    if not hasattr(request.user, 'role') or (request.user.role != 'admin' and request.user.role != 'staff'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('account_login')
    
    # Mendapatkan restaurant berdasarkan peran user
    restaurant = None
    
    try:
        # Untuk admin/owner, cari restaurant yang dimiliki
        if request.user.role == 'admin':
            restaurant = Restaurant.objects.filter(owner=request.user).first()
        # Untuk staff, cari restaurant tempat mereka bekerja
        elif request.user.role == 'staff':
            restaurant = Restaurant.objects.filter(staff=request.user).first()
    except Exception as e:
        print(f"Error finding restaurant: {e}")
    
    # Jika restaurant tidak ditemukan, ambil restaurant pertama untuk sementara
    if not restaurant:
        restaurant = Restaurant.objects.first()
    
    if not restaurant:
        messages.error(request, "No restaurant found. Please contact administrator.")
        return HttpResponse("No restaurant found. Please contact administrator.")
    
    # Get the order, ensuring it belongs to the user's restaurant
    order = get_object_or_404(Order, id=order_id, restaurant=restaurant)
    
    # Get the new status from the form
    new_status = request.POST.get('status')
    
    # Ensure the status is valid
    valid_statuses = [status[0] for status in Order.STATUS_CHOICES]
    if new_status in valid_statuses:
        # Update the order status
        old_status = order.status
        order.status = new_status
        order.save()
        
        # Add a success message
        status_display = dict(Order.STATUS_CHOICES)[new_status]
        messages.success(request, f'Order #{order.id} has been updated to {status_display}.')
        
        # Get the referer URL to determine where to redirect
        referer = request.META.get('HTTP_REFERER')
        
        # Redirect back to the order detail page or to the order list page if coming from there
        if referer and 'order_detail' in referer:
            return redirect('orders:order_detail', order_id=order.id)
        else:
            # Check if we should redirect to a specific status filter
            if old_status != new_status:
                # If user changed the status, keep them on the same list
                if referer:
                    return redirect(referer)
                else:
                    return redirect('orders:order_list')
            else:
                # Otherwise, go to the list showing the new status
                return redirect('orders:order_list')
    else:
        messages.error(request, f'Invalid status: {new_status}')
        return redirect('orders:order_detail', order_id=order.id)