"""
Views for the customer app
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST
from restaurants.models import Restaurant, Table, MenuItem, MenuCategory
from orders.models import Order, OrderItem

def menu_view(request, restaurant_id, table_id):
    """Display menu for customers"""
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    table = get_object_or_404(Table, id=table_id, restaurant=restaurant)
    
    categories = MenuCategory.objects.filter(restaurant=restaurant, active=True)
    menu_items = {}
    
    for category in categories:
        menu_items[category] = MenuItem.objects.filter(category=category, is_available=True)
    
    context = {
        'restaurant': restaurant,
        'table': table,
        'categories': categories,
        'menu_items': menu_items
    }
    
    return render(request, 'customer/menu.html', context)

def cart_view(request, restaurant_id, table_id):
    """Display cart for customer"""
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    table = get_object_or_404(Table, id=table_id, restaurant=restaurant)
    
    # Use the same cart key format
    cart_key = f'cart_{restaurant_id}_{table_id}'
    restaurant_cart = request.session.get(cart_key, {})
    
    cart_items = []
    total = 0
    
    for item_id, quantity in restaurant_cart.items():
        menu_item = get_object_or_404(MenuItem, id=int(item_id))
        subtotal = menu_item.price * quantity
        total += subtotal
        
        cart_items.append({
            'id': menu_item.id,
            'name': menu_item.name,
            'price': menu_item.price,
            'quantity': quantity,
            'subtotal': subtotal
        })
    
    context = {
        'restaurant': restaurant,
        'table': table,
        'cart_items': cart_items,
        'total': total
    }
    
    return render(request, 'customer/cart.html', context)

@require_POST
def add_to_cart(request, restaurant_id, table_id, item_id):
    """Add item to cart"""
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    table = get_object_or_404(Table, id=table_id, restaurant=restaurant)
    menu_item = get_object_or_404(MenuItem, id=item_id, category__restaurant=restaurant)
    
    # Get or initialize cart
    cart = request.session.get('cart', {})
    
    # Use a cart key specific to this restaurant and table
    cart_key = f'cart_{restaurant_id}_{table_id}'
    restaurant_cart = request.session.get(cart_key, {})
    
    # Add item to cart
    item_id_str = str(item_id)
    restaurant_cart[item_id_str] = restaurant_cart.get(item_id_str, 0) + 1
    
    # Save cart to session
    request.session[cart_key] = restaurant_cart
    request.session.modified = True
    
    # Return more detailed information for debugging
    return JsonResponse({
        'status': 'success', 
        'message': f'{menu_item.name} added to cart',
        'cart_key': cart_key,
        'cart_contents': restaurant_cart,
        'item_added': item_id_str
    })

@require_POST
def update_cart(request, restaurant_id, table_id, item_id):
    """Update cart item quantity"""
    quantity = int(request.POST.get('quantity', 1))
    
    # Use the same cart key format
    cart_key = f'cart_{restaurant_id}_{table_id}'
    restaurant_cart = request.session.get(cart_key, {})
    
    # Update quantity or remove if quantity is 0
    item_id_str = str(item_id)
    if quantity > 0:
        restaurant_cart[item_id_str] = quantity
    else:
        if item_id_str in restaurant_cart:
            del restaurant_cart[item_id_str]
    
    # Save cart to session
    request.session[cart_key] = restaurant_cart
    request.session.modified = True
    
    return redirect('cart_view', restaurant_id=restaurant_id, table_id=table_id)

@require_POST
def place_order(request, restaurant_id, table_id):
    """Place an order"""
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    table = get_object_or_404(Table, id=table_id, restaurant=restaurant)
    
    # Use the same cart key format
    cart_key = f'cart_{restaurant_id}_{table_id}'
    restaurant_cart = request.session.get(cart_key, {})
    
    if not restaurant_cart:
        messages.error(request, 'Your cart is empty')
        return redirect('cart_view', restaurant_id=restaurant_id, table_id=table_id)
    
    # Calculate total
    total = 0
    for item_id, quantity in restaurant_cart.items():
        menu_item = get_object_or_404(MenuItem, id=int(item_id))
        total += menu_item.price * quantity
    
    # Create order
    order = Order.objects.create(
        restaurant=restaurant,
        table=table,
        status='pending',
        total_amount=total
    )
    
    # Create order items
    for item_id, quantity in restaurant_cart.items():
        menu_item = get_object_or_404(MenuItem, id=int(item_id))
        subtotal = menu_item.price * quantity
        
        OrderItem.objects.create(
            order=order,
            menu_item=menu_item,
            quantity=quantity,
            subtotal=subtotal
        )
    
    # Clear cart
    request.session[cart_key] = {}
    request.session.modified = True
    
    # Redirect to order confirmation
    return redirect('order_confirmation', order_id=order.id)

def order_status(request, order_id):
    """Display order status"""
    order = get_object_or_404(Order, id=order_id)
    restaurant = order.restaurant
    table = order.table
    order_items = OrderItem.objects.filter(order=order)
    
    context = {
        'order': order,
        'restaurant': restaurant,
        'table': table,
        'order_items': order_items
    }
    
    return render(request, 'customer/order_status.html', context)

def order_confirmation(request, order_id):
    """Display order confirmation"""
    order = get_object_or_404(Order, id=order_id)
    restaurant = order.restaurant
    table = order.table
    order_items = OrderItem.objects.filter(order=order)
    
    context = {
        'order': order,
        'restaurant': restaurant,
        'table': table,
        'order_items': order_items
    }
    
    return render(request, 'customer/order_confirmation.html', context)

def table_entry(request, table_code):
    """Entry point for QR code scanning"""
    table = get_object_or_404(Table, qr_code=table_code)
    restaurant = table.restaurant
    
    return redirect('customer:menu_view', restaurant_id=restaurant.id, table_id=table.id)

@require_POST
def remove_from_cart(request, restaurant_id, table_id, item_id):
    """Remove item from cart"""
    # Use the same cart key format as in other views
    cart_key = f'cart_{restaurant_id}_{table_id}'
    restaurant_cart = request.session.get(cart_key, {})
    
    # Remove the item if it exists
    item_id_str = str(item_id)
    if item_id_str in restaurant_cart:
        del restaurant_cart[item_id_str]
        
    # Save updated cart to session
    request.session[cart_key] = restaurant_cart
    request.session.modified = True
    
    # Return success response for AJAX
    return JsonResponse({
        'status': 'success',
        'message': 'Item removed from cart',
        'cart_contents': restaurant_cart
    })