from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Restaurant, Table, MenuCategory, MenuItem

@login_required
def dashboard(request):
    """Dashboard view for restaurant owners"""
    # Cek apakah user memiliki restoran
    try:
        restaurant = Restaurant.objects.get(owner=request.user)
        tables = Table.objects.filter(restaurant=restaurant)
        categories = MenuCategory.objects.filter(restaurant=restaurant)
        
        context = {
            'restaurant': restaurant,
            'table_count': tables.count(),
            'category_count': categories.count(),
            'menu_item_count': MenuItem.objects.filter(category__restaurant=restaurant).count(),
        }
        return render(request, 'restaurants/dashboard.html', context)
    except Restaurant.DoesNotExist:
        # Jika user belum memiliki restoran, redirect ke halaman create restaurant
        return redirect('restaurants:create_restaurant')
        
@login_required
def menu_categories(request):
    """View untuk mengelola kategori menu"""
    try:
        restaurant = Restaurant.objects.get(owner=request.user)
        categories = MenuCategory.objects.filter(restaurant=restaurant)
        context = {
            'restaurant': restaurant,
            'categories': categories,
        }
        return render(request, 'restaurants/menu_categories.html', context)
    except Restaurant.DoesNotExist:
        return redirect('restaurants:create_restaurant')

@login_required
def menu_items(request):
    """View untuk mengelola item menu"""
    try:
        restaurant = Restaurant.objects.get(owner=request.user)
        categories = MenuCategory.objects.filter(restaurant=restaurant)
        menu_items = MenuItem.objects.filter(category__restaurant=restaurant)
        context = {
            'restaurant': restaurant,
            'categories': categories,
            'menu_items': menu_items,
        }
        return render(request, 'restaurants/menu_items.html', context)
    except Restaurant.DoesNotExist:
        return redirect('restaurants:create_restaurant')

@login_required
def tables(request):
    """View untuk mengelola meja"""
    try:
        restaurant = Restaurant.objects.get(owner=request.user)
        tables = Table.objects.filter(restaurant=restaurant)
        context = {
            'restaurant': restaurant,
            'tables': tables,
        }
        return render(request, 'restaurants/tables.html', context)
    except Restaurant.DoesNotExist:
        return redirect('restaurants:create_restaurant')

@login_required
def create_restaurant(request):
    """View untuk membuat restoran baru"""
    if request.method == 'POST':
        # Process form data
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        address = request.POST.get('address', '')
        contact_number = request.POST.get('contact_number', '')
        
        restaurant = Restaurant.objects.create(
            owner=request.user,
            name=name,
            description=description,
            address=address,
            contact_number=contact_number
        )
        return redirect('restaurants:dashboard')
    
    return render(request, 'restaurants/create_restaurant.html')

@login_required
def generate_qr(request, table_id):
    """Generate QR code for a table"""
    try:
        table = Table.objects.get(id=table_id)
        if table.restaurant.owner != request.user:
            # Security check to prevent accessing other restaurants' tables
            return redirect('restaurants:tables')
            
        qr_code = table.generate_qr_code(request.build_absolute_uri('/')[:-1])
        context = {
            'table': table,
            'qr_code': qr_code,
        }
        return render(request, 'restaurants/qr_code.html', context)
    except Table.DoesNotExist:
        return redirect('restaurants:tables')