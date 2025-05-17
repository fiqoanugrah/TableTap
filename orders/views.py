from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Order, OrderItem
from restaurants.models import Restaurant, Table

@login_required
def staff_dashboard(request):
    """Dashboard for staff to view and manage orders"""
    # Get restaurant where user is staff
    # For simplicity, we'll assume staff can view all restaurants
    # In a real app, you'd have staff-restaurant relationships
    orders = Order.objects.all().order_by('-created_at')
    
    context = {
        'orders': orders,
        'pending_count': orders.filter(status='pending').count(),
        'preparing_count': orders.filter(status='preparing').count(),
        'ready_count': orders.filter(status='ready').count(),
    }
    return render(request, 'orders/staff_dashboard.html', context)

@login_required
def order_detail(request, order_id):
    """View order details"""
    order = get_object_or_404(Order, id=order_id)
    
    context = {
        'order': order,
        'order_items': order.items.all(),
    }
    return render(request, 'orders/order_detail.html', context)

@login_required
def update_order_status(request, order_id):
    """Update order status"""
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')
        
        if new_status in [s[0] for s in Order.STATUS_CHOICES]:
            order.status = new_status
            order.save()
            
    return redirect('orders:order_detail', order_id=order_id)