from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Restaurant, Table, MenuCategory, MenuItem
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
import base64
from io import BytesIO
import qrcode
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from .models import Restaurant

User = get_user_model()

# restaurants/views.py
@login_required
def user_management(request):
    """View untuk manajemen user (admin dan staff)"""
    # Tambahkan print statement untuk debugging
    print("USER MANAGEMENT VIEW CALLED")
    
    # Pastikan user adalah admin (owner) dari restaurant
    if not hasattr(request.user, 'role') or request.user.role != 'admin':
        messages.error(request, "You don't have permission to access this page.")
        return redirect('restaurants:dashboard')
    
    # Dapatkan restaurant milik user saat ini
    restaurant = Restaurant.objects.filter(owner=request.user).first()
    if not restaurant:
        messages.error(request, "No restaurant found for your account.")
        return redirect('restaurants:dashboard')
    
    # Get tab yang aktif
    tab = request.GET.get('tab', 'admins')
    
    # Ambil admin users (selain user saat ini)
    admin_users = User.objects.filter(
        role='admin'
    ).exclude(id=request.user.id)
    
    # Ambil staff users dari relasi ManyToMany
    staff_users = restaurant.staff.all()
    
    context = {
        'restaurant': restaurant,
        'tab': tab,
        'admin_users': admin_users if tab == 'admins' else [],
        'staff_users': staff_users if tab == 'staff' else [],
    }
    
    print("Rendering user_management.html")
    return render(request, 'restaurants/user_management.html', context)

@login_required
def add_user(request):
    """Tambah user admin atau staff baru"""
    if request.method != 'POST':
        return redirect('restaurants:user_management')
    
    if not hasattr(request.user, 'role') or request.user.role != 'admin':
        messages.error(request, "You don't have permission to add users.")
        return redirect('restaurants:dashboard')
    
    # Dapatkan restaurant milik user saat ini
    restaurant = Restaurant.objects.filter(owner=request.user).first()
    if not restaurant:
        messages.error(request, "No restaurant found for your account.")
        return redirect('restaurants:dashboard')
    
    # Ambil data dari form
    role = request.POST.get('role', 'staff')
    first_name = request.POST.get('first_name', '')
    last_name = request.POST.get('last_name', '')
    email = request.POST.get('email', '')
    phone = request.POST.get('phone', '')
    password1 = request.POST.get('password1', '')
    password2 = request.POST.get('password2', '')
    
    # Validasi data
    if not (first_name and last_name and email and password1 and password2):
        messages.error(request, "All fields are required.")
        return redirect('restaurants:user_management')
    
    if password1 != password2:
        messages.error(request, "Passwords do not match.")
        return redirect('restaurants:user_management')
    
    # Cek apakah email sudah digunakan
    if User.objects.filter(email=email).exists():
        messages.error(request, f"User with email {email} already exists.")
        return redirect('restaurants:user_management')
    
    # Buat username dari email (sebelum karakter @)
    username = email.split('@')[0]
    counter = 1
    original_username = username
    while User.objects.filter(username=username).exists():
        username = f"{original_username}{counter}"
        counter += 1
    
    # Buat user
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password1,
        first_name=first_name,
        last_name=last_name,
        role=role,
        phone=phone
    )
    
    # Hubungkan user dengan restaurant
    if role == 'admin':
        # Untuk admin user, buat relasi dengan restaurant sebagai owner
        # Jika dalam model saat ini hanya ada satu owner, mungkin perlu dipertimbangkan lagi
        # Alternatifnya, kita bisa membuat relasi baru untuk admin tambahan
        restaurant.owner = user
        restaurant.save()
    elif role == 'staff':
        # Untuk staff user, tambahkan ke restaurant staff
        restaurant.staff.add(user)
    
    messages.success(request, f"{role.title()} user {email} has been created successfully.")
    return redirect('restaurants:user_management')

@login_required
def update_user(request, user_id):
    """Update data user"""
    if request.method != 'POST':
        return redirect('restaurants:user_management')
    
    if not hasattr(request.user, 'role') or request.user.role != 'admin':
        messages.error(request, "You don't have permission to update users.")
        return redirect('restaurants:dashboard')
    
    # Dapatkan restaurant milik user saat ini
    restaurant = Restaurant.objects.filter(owner=request.user).first()
    if not restaurant:
        messages.error(request, "No restaurant found for your account.")
        return redirect('restaurants:dashboard')
    
    # Ambil user yang akan diupdate
    user_to_update = get_object_or_404(User, id=user_id)
    
    # Periksa apakah user terhubung dengan restaurant ini
    is_associated = False
    if user_to_update.role == 'admin' and restaurant.owner == user_to_update:
        is_associated = True
    elif user_to_update.role == 'staff' and restaurant.staff.filter(id=user_to_update.id).exists():
        is_associated = True
    
    if not is_associated:
        messages.error(request, "This user is not associated with your restaurant.")
        return redirect('restaurants:user_management')
    
    # Ambil data dari form
    first_name = request.POST.get('first_name', '')
    last_name = request.POST.get('last_name', '')
    email = request.POST.get('email', '')
    phone = request.POST.get('phone', '')
    
    # Validasi data
    if not (first_name and last_name and email):
        messages.error(request, "All fields are required.")
        return redirect('restaurants:user_management')
    
    # Periksa jika email diubah dan sudah ada di sistem
    if email != user_to_update.email and User.objects.filter(email=email).exists():
        messages.error(request, f"User with email {email} already exists.")
        return redirect('restaurants:user_management')
    
    # Update user
    user_to_update.first_name = first_name
    user_to_update.last_name = last_name
    user_to_update.email = email
    user_to_update.phone = phone
    user_to_update.save()
    
    messages.success(request, f"User {email} has been updated successfully.")
    return redirect('restaurants:user_management')

@login_required
def deactivate_user(request, user_id):
    """Nonaktifkan user"""
    if request.method != 'POST':
        return redirect('restaurants:user_management')
    
    if not hasattr(request.user, 'role') or request.user.role != 'admin':
        messages.error(request, "You don't have permission to deactivate users.")
        return redirect('restaurants:dashboard')
    
    # Dapatkan restaurant milik user saat ini
    restaurant = Restaurant.objects.filter(owner=request.user).first()
    if not restaurant:
        messages.error(request, "No restaurant found for your account.")
        return redirect('restaurants:dashboard')
    
    # Jangan izinkan user menonaktifkan diri sendiri
    if str(user_id) == str(request.user.id):
        messages.error(request, "You cannot deactivate your own account.")
        return redirect('restaurants:user_management')
    
    # Ambil user yang akan dinonaktifkan
    user_to_deactivate = get_object_or_404(User, id=user_id)
    
    # Periksa apakah user terhubung dengan restaurant ini
    is_associated = False
    if user_to_deactivate.role == 'admin' and restaurant.owner == user_to_deactivate:
        is_associated = True
    elif user_to_deactivate.role == 'staff' and restaurant.staff.filter(id=user_to_deactivate.id).exists():
        is_associated = True
    
    if not is_associated:
        messages.error(request, "This user is not associated with your restaurant.")
        return redirect('restaurants:user_management')
    
    # Nonaktifkan user
    user_to_deactivate.is_active = False
    user_to_deactivate.save()
    
    # Jika user adalah staff, hapus dari restaurant
    if user_to_deactivate.role == 'staff':
        restaurant.staff.remove(user_to_deactivate)
    
    messages.success(request, f"User {user_to_deactivate.email} has been deactivated.")
    return redirect('restaurants:user_management')
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
    
@login_required
def add_category(request):
    """Add a new menu category"""
    if request.method == 'POST':
        try:
            restaurant = Restaurant.objects.get(owner=request.user)
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            display_order = request.POST.get('display_order', 0)
            active = 'active' in request.POST
            
            MenuCategory.objects.create(
                restaurant=restaurant,
                name=name,
                description=description,
                display_order=display_order,
                active=active
            )
            
            # Could add message here
            
            return redirect('restaurants:menu_categories')
        except Restaurant.DoesNotExist:
            return redirect('restaurants:create_restaurant')
    return redirect('restaurants:menu_categories')

@login_required
def edit_category(request):
    """Edit an existing menu category"""
    if request.method == 'POST':
        try:
            restaurant = Restaurant.objects.get(owner=request.user)
            category_id = request.POST.get('category_id')
            category = MenuCategory.objects.get(id=category_id, restaurant=restaurant)
            
            category.name = request.POST.get('name')
            category.description = request.POST.get('description', '')
            category.display_order = request.POST.get('display_order', 0)
            category.active = 'active' in request.POST
            category.save()
            
            # Could add message here
            
            return redirect('restaurants:menu_categories')
        except (Restaurant.DoesNotExist, MenuCategory.DoesNotExist):
            # Could add error message here
            pass
    return redirect('restaurants:menu_categories')

@login_required
def delete_category(request):
    """Delete a menu category"""
    if request.method == 'POST':
        try:
            restaurant = Restaurant.objects.get(owner=request.user)
            category_id = request.POST.get('category_id')
            category = MenuCategory.objects.get(id=category_id, restaurant=restaurant)
            category.delete()
            
            # Could add message here
            
            return redirect('restaurants:menu_categories')
        except (Restaurant.DoesNotExist, MenuCategory.DoesNotExist):
            # Could add error message here
            pass
    return redirect('restaurants:menu_categories')

@login_required
def add_menu_item(request):
    """Add a new menu item"""
    if request.method == 'POST':
        try:
            restaurant = Restaurant.objects.get(owner=request.user)
            category_id = request.POST.get('category')
            category = MenuCategory.objects.get(id=category_id, restaurant=restaurant)
            
            # Create menu item
            item = MenuItem(
                category=category,
                name=request.POST.get('name'),
                description=request.POST.get('description', ''),
                price=request.POST.get('price'),
                is_available='is_available' in request.POST
            )
            item.save()
            
            # Handle image if uploaded
            if 'image' in request.FILES:
                item.save_image_base64(request.FILES['image'])
            
            # Could add success message here
            
            return redirect('restaurants:menu_items')
        except (Restaurant.DoesNotExist, MenuCategory.DoesNotExist):
            # Could add error message here
            pass
    return redirect('restaurants:menu_items')

@login_required
def edit_menu_item(request):
    """Edit an existing menu item"""
    if request.method == 'POST':
        try:
            restaurant = Restaurant.objects.get(owner=request.user)
            item_id = request.POST.get('item_id')
            category_id = request.POST.get('category')
            
            # Verify the item and category belong to this restaurant
            category = MenuCategory.objects.get(id=category_id, restaurant=restaurant)
            item = MenuItem.objects.get(id=item_id, category__restaurant=restaurant)
            
            # Update item fields
            item.category = category
            item.name = request.POST.get('name')
            item.description = request.POST.get('description', '')
            item.price = request.POST.get('price')
            item.is_available = 'is_available' in request.POST
            item.save()
            
            # Handle image if uploaded
            if 'image' in request.FILES:
                item.save_image_base64(request.FILES['image'])
            
            # Could add success message here
            
            return redirect('restaurants:menu_items')
        except (Restaurant.DoesNotExist, MenuCategory.DoesNotExist, MenuItem.DoesNotExist):
            # Could add error message here
            pass
    return redirect('restaurants:menu_items')

@login_required
def delete_menu_item(request):
    """Delete a menu item"""
    if request.method == 'POST':
        try:
            restaurant = Restaurant.objects.get(owner=request.user)
            item_id = request.POST.get('item_id')
            
            # Verify the item belongs to this restaurant
            item = MenuItem.objects.get(id=item_id, category__restaurant=restaurant)
            item.delete()
            
            # Could add success message here
            
            return redirect('restaurants:menu_items')
        except (Restaurant.DoesNotExist, MenuItem.DoesNotExist):
            # Could add error message here
            pass
    return redirect('restaurants:menu_items')

@login_required
def add_table(request):
    """Add a new table"""
    if request.method == 'POST':
        try:
            restaurant = Restaurant.objects.get(owner=request.user)
            table_number = request.POST.get('table_number')
            seats = request.POST.get('seats', 2)
            status = request.POST.get('status', 'available')
            
            # Check if table number already exists for this restaurant
            if Table.objects.filter(restaurant=restaurant, table_number=table_number).exists():
                messages.error(request, f"Table #{table_number} already exists.")
                return redirect('restaurants:tables')
            
            # Create new table
            Table.objects.create(
                restaurant=restaurant,
                table_number=table_number,
                seats=seats,
                status=status
            )
            
            messages.success(request, f"Table #{table_number} has been added.")
            
        except Restaurant.DoesNotExist:
            return redirect('restaurants:create_restaurant')
    
    return redirect('restaurants:tables')

@login_required
def edit_table(request):
    """Edit an existing table"""
    if request.method == 'POST':
        try:
            restaurant = Restaurant.objects.get(owner=request.user)
            table_id = request.POST.get('table_id')
            table = Table.objects.get(id=table_id, restaurant=restaurant)
            
            new_table_number = request.POST.get('table_number')
            
            # Check if table number already exists for another table
            if (Table.objects.filter(restaurant=restaurant, table_number=new_table_number)
                    .exclude(id=table_id).exists()):
                messages.error(request, f"Table #{new_table_number} already exists.")
                return redirect('restaurants:tables')
            
            # Update table fields
            table.table_number = new_table_number
            table.seats = request.POST.get('seats', 2)
            table.status = request.POST.get('status', 'available')
            table.save()
            
            messages.success(request, f"Table #{new_table_number} has been updated.")
            
        except (Restaurant.DoesNotExist, Table.DoesNotExist):
            messages.error(request, "Table not found or you don't have permission to edit it.")
            
    return redirect('restaurants:tables')

@login_required
def delete_table(request):
    """Delete a table"""
    if request.method == 'POST':
        try:
            restaurant = Restaurant.objects.get(owner=request.user)
            table_id = request.POST.get('table_id')
            table = Table.objects.get(id=table_id, restaurant=restaurant)
            table_number = table.table_number
            
            table.delete()
            
            messages.success(request, f"Table #{table_number} has been deleted.")
            
        except (Restaurant.DoesNotExist, Table.DoesNotExist):
            messages.error(request, "Table not found or you don't have permission to delete it.")
            
    return redirect('restaurants:tables')

@login_required
def generate_qr(request, table_id):
    """Generate QR code for a table"""
    try:
        table = Table.objects.get(id=table_id)
        restaurant = table.restaurant
        
        # Security check to prevent accessing other restaurants' tables
        if restaurant.owner != request.user:
            messages.error(request, "You don't have permission to access this table.")
            return redirect('restaurants:tables')
            
        # Generate QR code
        base_url = request.build_absolute_uri('/')[:-1]  # Get base URL without trailing slash
        menu_url = f"{base_url}/menu/{restaurant.id}/{table.id}/"
        
        import qrcode
        from io import BytesIO
        import base64
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(menu_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        
        # Save QR code to table
        table.qr_code = qr_code_base64
        table.qr_code_url = menu_url
        table.save()
        
        # If this is an AJAX request, return JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'qr_code': qr_code_base64,
                'qr_code_url': menu_url
            })
            
        # Check if we need to show QR code page or download directly
        if 'download' in request.GET:
            # Set up response for download
            response = HttpResponse(base64.b64decode(qr_code_base64), content_type='image/png')
            response['Content-Disposition'] = f'attachment; filename="table_{table.table_number}_qr.png"'
            return response
        
        # Show QR code page
        context = {
            'table': table,
            'restaurant': restaurant,
            'qr_code': qr_code_base64,
            'menu_url': menu_url
        }
        return render(request, 'restaurants/qr_code.html', context)
        
    except Table.DoesNotExist:
        messages.error(request, "Table not found.")
        return redirect('restaurants:tables')
    
