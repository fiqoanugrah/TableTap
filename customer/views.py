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
    
    context = {
        'restaurant': restaurant,
        'table': table,
        'categories': categories,
    }
    return render(request, 'customer/menu.html', context)

def add_to_cart(request, restaurant_id, table_id, menu_item_id):
    """Add item to cart (stored in session)"""
    if request.method == 'POST':
        restaurant = get_object_or_404(Restaurant, id=restaurant_id)
        table = get_object_or_404(Table, id=table_id, restaurant=restaurant)
        menu_item = get_object_or_404(MenuItem, id=menu_item_id)
        
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
            if item['menu_item_id'] == menu_item_id:
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
        
        # Return to menu
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
        
        # Redirect to order status page
        return redirect('customer:order_status', order_id=order.id)
        
    return redirect('customer:cart', restaurant_id=restaurant_id, table_id=table_id)

def order_status(request, order_id):
    """View order status"""
    order = get_object_or_404(Order, id=order_id)
    
    context = {
        'order': order,
        'order_items': order.items.all()
    }
    return render(request, 'customer/order_status.html', context)