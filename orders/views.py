# orders/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count
from .models import Order
from restaurants.models import Restaurant

@login_required
def dashboard(request):
    """Staff dashboard view"""
    # Get the restaurant for the logged-in user
    restaurant = None
    if hasattr(request.user, 'restaurant'):
        restaurant = request.user.restaurant
    else:
        # If no restaurant is associated, redirect to a relevant page
        messages.error(request, "You don't have a restaurant associated with your account.")
        return redirect('restaurants:dashboard')  # Or another appropriate page
    
    # Count orders by status
    pending_count = Order.objects.filter(restaurant=restaurant, status='pending').count()
    preparing_count = Order.objects.filter(restaurant=restaurant, status='preparing').count()
    ready_count = Order.objects.filter(restaurant=restaurant, status='ready').count()
    
    # Get today's orders count
    today = timezone.now().date()
    today_count = Order.objects.filter(
        restaurant=restaurant,
        created_at__date=today
    ).count()
    
    # Get recent orders (last 10)
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
    
    return render(request, 'orders/dashboard.html', context)

@login_required
def order_list(request):
    """Display a list of orders with filtering options"""
    # Get the restaurant for the logged-in user
    restaurant = None
    if hasattr(request.user, 'restaurant'):
        restaurant = request.user.restaurant
    else:
        messages.error(request, "You don't have a restaurant associated with your account.")
        return redirect('restaurants:dashboard')  # Or another appropriate page
    
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
    # Get the restaurant for the logged-in user
    restaurant = None
    if hasattr(request.user, 'restaurant'):
        restaurant = request.user.restaurant
    else:
        messages.error(request, "You don't have a restaurant associated with your account.")
        return redirect('restaurants:dashboard')  # Or another appropriate page
    
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

# orders/views.py (lanjutan)
@login_required
def update_status(request, order_id):
    """Update the status of an order"""
    if request.method == 'POST':
        # Get the restaurant for the logged-in user
        restaurant = None
        if hasattr(request.user, 'restaurant'):
            restaurant = request.user.restaurant
        else:
            messages.error(request, "You don't have a restaurant associated with your account.")
            return redirect('restaurants:dashboard')  # Or another appropriate page
        
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
            if 'order_detail' in referer:
                return redirect('orders:order_detail', order_id=order.id)
            else:
                # Check if we should redirect to a specific status filter
                if old_status != new_status:
                    # If user changed the status, keep them on the same list
                    return redirect(referer)
                else:
                    # Otherwise, go to the list showing the new status
                    return redirect('orders:order_list', status=new_status)
        else:
            messages.error(request, f'Invalid status: {new_status}')
            return redirect('orders:order_detail', order_id=order.id)
    
    # If not a POST request, redirect to the order detail page
    return redirect('orders:order_detail', order_id=order_id)