from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from restaurants.models import Restaurant, Table, MenuCategory, MenuItem
from orders.models import Order, OrderItem
from django.db.models import Sum

def menu(request, restaurant_id, table_id):
    """View menu for a restaurant table"""
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    table = get_object_or_404(Table, id=table_id, restaurant=restaurant)
    
    # Get all active categories and their items
    categories = MenuCategory.objects.filter(restaurant=restaurant, active=True)
    
    # Check for active orders for this table
    # Active orders are those with status not in 'completed' or 'cancelled'
    active_orders = Order.objects.filter(
        restaurant=restaurant,
        table=table,
        status__in=['pending', 'preparing', 'ready']
    ).order_by('-created_at')
    
    context = {
        'restaurant': restaurant,
        'table': table,
        'categories': categories,
        'active_orders': active_orders,
    }
    return render(request, 'customer/menu.html', context)

def add_to_cart(request, restaurant_id, table_id, menu_item_id):
    """Add item to cart (stored in session)"""
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    table = get_object_or_404(Table, id=table_id, restaurant=restaurant)
    menu_item = get_object_or_404(MenuItem, id=menu_item_id)
    
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        notes = request.POST.get('notes', '')
        
        # Initialize cart in session if it doesn't exist
        cart_key = f'cart_{restaurant_id}_{table_id}'
        if cart_key not in request.session:
            request.session[cart_key] = []
            
        # Check if item already in cart
        cart = request.session[cart_key]
        found = False
        for item in cart:
            if int(item.get('menu_item_id')) == menu_item_id:
                item['quantity'] += quantity
                found = True
                break
                
        if not found:
            cart.append({
                'menu_item_id': menu_item_id,
                'name': menu_item.name,
                'price': str(menu_item.price),
                'quantity': quantity,
                'notes': notes
            })
            
        request.session[cart_key] = cart
        request.session.modified = True
        
        # Calculate cart count
        cart_count = sum(item.get('quantity', 0) for item in cart)
        
        # Calculate new totals
        subtotal = sum(float(item.get('price', 0)) * item.get('quantity', 0) for item in cart)
        total = subtotal  # No service fee
        
        # Check if this is an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'cart_count': cart_count,
                'subtotal': f"{subtotal:.2f}",
                'total': f"{total:.2f}",
                'message': f'{quantity} item(s) added to cart'
            })
        
        # Regular form submission
        return redirect('customer:menu', restaurant_id=restaurant_id, table_id=table_id)
        
    # If not POST, redirect to menu
    return redirect('customer:menu', restaurant_id=restaurant_id, table_id=table_id)

def cart(request, restaurant_id, table_id):
    """View cart contents"""
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    table = get_object_or_404(Table, id=table_id, restaurant=restaurant)
    
    # Get cart from session
    cart_key = f'cart_{restaurant_id}_{table_id}'
    cart_items = request.session.get(cart_key, [])
    
    # Calculate total
    total = sum(float(item['price']) * item['quantity'] for item in cart_items)
    
    context = {
        'restaurant': restaurant,
        'table': table,
        'cart_items': cart_items,
        'total': total
    }
    return render(request, 'customer/cart.html', context)

# customer/views.py
def place_order(request, restaurant_id, table_id):
    """Place an order from cart"""
    if request.method == 'POST':
        restaurant = get_object_or_404(Restaurant, id=restaurant_id)
        table = get_object_or_404(Table, id=table_id, restaurant=restaurant)
        
        # Get cart from session
        cart_key = f'cart_{restaurant_id}_{table_id}'
        cart_items = request.session.get(cart_key, [])
        
        if not cart_items:
            return redirect('customer:menu', restaurant_id=restaurant_id, table_id=table_id)
            
        # Calculate total
        total = sum(float(item['price']) * item['quantity'] for item in cart_items)
        
        # Create order
        special_instructions = request.POST.get('special_instructions', '')
        order = Order.objects.create(
            restaurant=restaurant,
            table=table,
            status='pending',
            special_instructions=special_instructions,
            total_amount=total
        )
        
        # Create order items
        for item in cart_items:
            menu_item = MenuItem.objects.get(id=item['menu_item_id'])
            OrderItem.objects.create(
                order=order,
                menu_item=menu_item,
                quantity=item['quantity'],
                price=menu_item.price,
                notes=item['notes']
            )
            
        # Clear cart
        request.session[cart_key] = []
        request.session.modified = True
        
        # Redirect to order confirmation page instead of order status
        return redirect('customer:order_confirmation', order_id=order.id)
        
    return redirect('customer:cart', restaurant_id=restaurant_id, table_id=table_id)

def order_status(request, order_id):
    """View order status"""
    order = get_object_or_404(Order, id=order_id)
    
    context = {
        'order': order,
        'order_items': order.items.all()
    }
    return render(request, 'customer/order_status.html', context)

def update_cart_item(request, restaurant_id, table_id, menu_item_id):
    """Update quantity of an item in cart (AJAX)"""
    if request.method == 'POST':
        # Get cart from session
        cart_key = f'cart_{restaurant_id}_{table_id}'
        cart_items = request.session.get(cart_key, [])
        
        # Get new quantity from POST
        try:
            quantity = int(request.POST.get('quantity', 1))
            if quantity < 1:
                return JsonResponse({'success': False, 'error': 'Quantity must be at least 1'})
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Invalid quantity'})
        
        # Update the item quantity
        updated = False
        for item in cart_items:
            if int(item.get('menu_item_id')) == menu_item_id:
                item['quantity'] = quantity
                updated = True
                break
        
        if not updated:
            return JsonResponse({'success': False, 'error': 'Item not found in cart'})
        
        # Update session
        request.session[cart_key] = cart_items
        request.session.modified = True
        
        # Calculate new totals
        subtotal = sum(float(item['price']) * item['quantity'] for item in cart_items)
        total = subtotal  # No service fee
        cart_count = sum(item['quantity'] for item in cart_items)
        
        # Get the updated item's total
        item_total = 0
        for item in cart_items:
            if int(item.get('menu_item_id')) == menu_item_id:
                item_total = float(item['price']) * item['quantity']
                break
        
        # Return updated values
        return JsonResponse({
            'success': True,
            'subtotal': f"{subtotal:.2f}",
            'total': f"{total:.2f}",
            'item_total': f"{item_total:.2f}",
            'cart_count': cart_count,
            'quantity': quantity
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

# customer/views.py
# Add this new view
def order_confirmation(request, order_id):
    """Order confirmation page"""
    order = get_object_or_404(Order, id=order_id)
    
    context = {
        'order': order,
        'restaurant': order.restaurant,
        'table': order.table
    }
    return render(request, 'customer/order_confirmation.html', context)

def remove_from_cart(request, restaurant_id, table_id, menu_item_id):
    """Remove item from cart (AJAX)"""
    if request.method == 'POST':
        # Get cart from session
        cart_key = f'cart_{restaurant_id}_{table_id}'
        cart_items = request.session.get(cart_key, [])
        
        # Create a new cart without the item to be removed
        updated_cart = []
        for item in cart_items:
            if int(item.get('menu_item_id')) != menu_item_id:
                updated_cart.append(item)
        
        # Update session
        request.session[cart_key] = updated_cart
        request.session.modified = True
        
        # Calculate new totals
        subtotal = sum(float(item['price']) * item['quantity'] for item in updated_cart)
        total = subtotal  # No service fee
        cart_count = sum(item['quantity'] for item in updated_cart)
        
        # Return updated values
        return JsonResponse({
            'success': True,
            'subtotal': f"{subtotal:.2f}",
            'total': f"{total:.2f}",
            'cart_count': cart_count,
            'cart_empty': len(updated_cart) == 0
        })
    
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

