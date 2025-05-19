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

# Utility function to get restaurant for a user
def get_restaurant_for_user(user):
    """Get restaurant for a user based on their role"""
    restaurant = None
    
    # Check if user has a valid role
    if not hasattr(user, 'role'):
        return None
    
    # Check if user is restaurant owner
    if user.role == 'restaurant_owner':
        # Restaurant owners should have their own restaurant
        restaurant = Restaurant.objects.filter(owner=user).first()
        
    # Check if user is admin or staff
    elif user.role in ['admin', 'staff']:
        # First check if the admin is also an owner
        owner_restaurant = Restaurant.objects.filter(owner=user).first()
        if owner_restaurant:
            return owner_restaurant
            
        # Otherwise check if they're in the staff list
        restaurant = Restaurant.objects.filter(staff=user).first()
    
    return restaurant

# restaurants/views.py
@login_required
def user_management(request):
    """View untuk manajemen user (admin dan staff)"""
    # Tambahkan print statement untuk debugging
    print("USER MANAGEMENT VIEW CALLED")
    
    # Pastikan user adalah restaurant owner
    if not hasattr(request.user, 'role') or request.user.role != 'restaurant_owner':
        messages.error(request, "You don't have permission to access this page.")
        return redirect('restaurants:dashboard')
    
    # Dapatkan restaurant milik user saat ini
    restaurant = Restaurant.objects.filter(owner=request.user).first()
    if not restaurant:
        messages.error(request, "No restaurant found for your account.")
        return redirect('restaurants:dashboard')
    
    # Get tab yang aktif
    tab = request.GET.get('tab', 'admins')
    
    # Ambil admin users yang terkait dengan restaurant ini
    admin_users = User.objects.filter(
        role='admin',
        staffed_restaurants=restaurant  # Only get admins linked to this restaurant via staff relationship
    )
    
    # Ambil staff users dari relasi ManyToMany yang hanya staff, bukan admin
    staff_users = restaurant.staff.filter(role='staff')
    
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
    
    if not hasattr(request.user, 'role') or request.user.role != 'restaurant_owner':
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
    if role in ['admin', 'staff']:
        # Untuk admin dan staff user, tambahkan ke restaurant staff
        restaurant.staff.add(user)
    
    messages.success(request, f"{role.title()} user {email} has been created successfully.")
    return redirect('restaurants:user_management')

@login_required
def update_user(request, user_id):
    """Update data user"""
    if request.method != 'POST':
        return redirect('restaurants:user_management')
    
    if not hasattr(request.user, 'role') or request.user.role != 'restaurant_owner':
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
    
    if not hasattr(request.user, 'role') or request.user.role != 'restaurant_owner':
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
    if user_to_deactivate.role in ['admin', 'staff'] and restaurant.staff.filter(id=user_to_deactivate.id).exists():
        is_associated = True
    
    if not is_associated:
        messages.error(request, "This user is not associated with your restaurant.")
        return redirect('restaurants:user_management')
    
    # Nonaktifkan user
    user_to_deactivate.is_active = False
    user_to_deactivate.save()
    
    # Remove from restaurant staff list
    if user_to_deactivate.role in ['admin', 'staff']:
        restaurant.staff.remove(user_to_deactivate)
    
    messages.success(request, f"User {user_to_deactivate.email} has been deactivated.")
    return redirect('restaurants:user_management')

@login_required
def dashboard(request):
    """Dashboard view for restaurant owners & admins"""
    # Use the utility function to get restaurant for user
    restaurant = get_restaurant_for_user(request.user)
    
    if restaurant:
        tables = Table.objects.filter(restaurant=restaurant)
        categories = MenuCategory.objects.filter(restaurant=restaurant)
        
        context = {
            'restaurant': restaurant,
            'table_count': tables.count(),
            'category_count': categories.count(),
            'menu_item_count': MenuItem.objects.filter(category__restaurant=restaurant).count(),
        }
        return render(request, 'restaurants/dashboard.html', context)
    else:
        # Check if user has permission to create a restaurant
        if hasattr(request.user, 'role') and request.user.role in ['restaurant_owner', 'admin']:
            # Redirect to create restaurant page with a message
            messages.info(request, "You need to create a restaurant first.")
            return redirect('restaurants:create_restaurant')
        else:
            # For users who shouldn't create restaurants
            messages.error(request, "You don't have a restaurant assigned to your account. Please contact the administrator.")
            return redirect('account_login')
        
@login_required
def menu_categories(request):
    """View untuk mengelola kategori menu"""
    # Check if user has permission to manage menu categories
    if not hasattr(request.user, 'role') or request.user.role == 'staff':
        messages.error(request, "You don't have permission to manage menu categories.")
        return redirect('restaurants:dashboard')
    
    # Use the utility function to get restaurant for user
    restaurant = get_restaurant_for_user(request.user)
    
    if restaurant:
        categories = MenuCategory.objects.filter(restaurant=restaurant)
        context = {
            'restaurant': restaurant,
            'categories': categories,
        }
        return render(request, 'restaurants/menu_categories.html', context)
    else:
        # For users who should be able to create a restaurant
        if hasattr(request.user, 'role') and request.user.role in ['restaurant_owner', 'admin']:
            messages.info(request, "You need to create a restaurant first.")
            return redirect('restaurants:create_restaurant')
        else:
            # For users who shouldn't create restaurants
            messages.error(request, "You don't have a restaurant assigned to your account. Please contact the administrator.")
            return redirect('restaurants:dashboard')

@login_required
def menu_items(request):
    """View untuk mengelola item menu"""
    # Check if user has permission to manage menu items
    if not hasattr(request.user, 'role') or request.user.role == 'staff':
        messages.error(request, "You don't have permission to manage menu items.")
        return redirect('restaurants:dashboard')
    
    # Use the utility function to get restaurant for user
    restaurant = get_restaurant_for_user(request.user)
    
    if restaurant:
        categories = MenuCategory.objects.filter(restaurant=restaurant)
        menu_items = MenuItem.objects.filter(category__restaurant=restaurant)
        context = {
            'restaurant': restaurant,
            'categories': categories,
            'menu_items': menu_items,
        }
        return render(request, 'restaurants/menu_items.html', context)
    else:
        # For users who should be able to create a restaurant
        if hasattr(request.user, 'role') and request.user.role in ['restaurant_owner', 'admin']:
            messages.info(request, "You need to create a restaurant first.")
            return redirect('restaurants:create_restaurant')
        else:
            # For users who shouldn't create restaurants
            messages.error(request, "You don't have a restaurant assigned to your account. Please contact the administrator.")
            return redirect('restaurants:dashboard')

@login_required
def tables(request):
    """View untuk mengelola meja"""
    # Check if user has permission to manage tables
    if not hasattr(request.user, 'role') or request.user.role == 'staff':
        messages.error(request, "You don't have permission to manage tables.")
        return redirect('restaurants:dashboard')
    
    # Use the utility function to get restaurant for user
    restaurant = get_restaurant_for_user(request.user)
    
    if restaurant:
        tables = Table.objects.filter(restaurant=restaurant)
        context = {
            'restaurant': restaurant,
            'tables': tables,
        }
        return render(request, 'restaurants/tables.html', context)
    else:
        # Only restaurant owners should be redirected to create a new restaurant
        if hasattr(request.user, 'role') and request.user.role == 'restaurant_owner':
            # Check if they already have a restaurant but it wasn't found due to a different issue
            existing_restaurant = Restaurant.objects.filter(owner=request.user).first()
            if existing_restaurant:
                # They have a restaurant, but there was some other issue - maybe staff relationship wasn't set up
                messages.error(request, "There was an issue accessing your restaurant. Please contact support.")
                return redirect('restaurants:dashboard')
            else:
                # They need to create a restaurant
                messages.info(request, "You need to create a restaurant first.")
                return redirect('restaurants:create_restaurant')
        elif hasattr(request.user, 'role') and request.user.role == 'admin':
            # Admins should never be redirected to create restaurant - they should be associated with an existing one
            messages.error(request, "You don't have a restaurant assigned to your account. Please contact the restaurant owner.")
            return redirect('restaurants:dashboard')
        else:
            # For users who shouldn't create restaurants
            messages.error(request, "You don't have a restaurant assigned to your account. Please contact the administrator.")
            return redirect('restaurants:dashboard')

@login_required
def create_restaurant(request):
    """View untuk membuat restoran baru"""
    if request.method == 'POST':
        # Process form data
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        address = request.POST.get('address', '')
        contact_number = request.POST.get('contact_number', '')
        
        # Create the restaurant
        restaurant = Restaurant.objects.create(
            owner=request.user,
            name=name,
            description=description,
            address=address,
            contact_number=contact_number
        )
        
        # Only set the user's role to restaurant_owner if they are a customer
        # Admin users should remain as admins
        if hasattr(request.user, 'role'):
            if request.user.role == 'customer':
                request.user.role = 'restaurant_owner'
                request.user.save()
            elif request.user.role == 'admin':
                # If an admin creates a restaurant, add them to the restaurant's staff
                # so they can access it without being converted to restaurant_owner
                restaurant.staff.add(request.user)
            
        messages.success(request, f"Restaurant '{name}' created successfully!")
        return redirect('restaurants:dashboard')
    
    return render(request, 'restaurants/create_restaurant.html')

@login_required
def add_category(request):
    """Add a new menu category"""
    # Check if user has permission to manage menu categories
    if not hasattr(request.user, 'role') or request.user.role == 'staff':
        messages.error(request, "You don't have permission to manage menu categories.")
        return redirect('restaurants:dashboard')
    
    if request.method == 'POST':
        try:
            # Use the utility function to get restaurant for user
            restaurant = get_restaurant_for_user(request.user)
            if not restaurant:
                if request.user.role == 'restaurant_owner':
                    messages.info(request, "You need to create a restaurant first.")
                    return redirect('restaurants:create_restaurant')
                else:
                    messages.error(request, "No restaurant found for your account.")
                    return redirect('restaurants:dashboard')
                
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
            
            messages.success(request, f"Category {name} has been created successfully.")
            return redirect('restaurants:menu_categories')
        except Exception as e:
            messages.error(request, f"Error creating category: {str(e)}")
            return redirect('restaurants:menu_categories')
    return redirect('restaurants:menu_categories')

@login_required
def edit_category(request):
    """Edit an existing menu category"""
    # Check if user has permission to manage menu categories
    if not hasattr(request.user, 'role') or request.user.role == 'staff':
        messages.error(request, "You don't have permission to manage menu categories.")
        return redirect('restaurants:dashboard')
    
    if request.method == 'POST':
        try:
            # Use the utility function to get restaurant for user
            restaurant = get_restaurant_for_user(request.user)
            if not restaurant:
                messages.error(request, "No restaurant found for your account.")
                return redirect('restaurants:dashboard')
                
            category_id = request.POST.get('category_id')
            category = MenuCategory.objects.get(id=category_id, restaurant=restaurant)
            
            category.name = request.POST.get('name')
            category.description = request.POST.get('description', '')
            category.display_order = request.POST.get('display_order', 0)
            category.active = 'active' in request.POST
            category.save()
            
            messages.success(request, f"Category {category.name} has been updated successfully.")
            return redirect('restaurants:menu_categories')
        except (MenuCategory.DoesNotExist) as e:
            messages.error(request, f"Error updating category: {str(e)}")
            return redirect('restaurants:menu_categories')
    return redirect('restaurants:menu_categories')

@login_required
def delete_category(request):
    """Delete a menu category"""
    # Check if user has permission to manage menu categories
    if not hasattr(request.user, 'role') or request.user.role == 'staff':
        messages.error(request, "You don't have permission to manage menu categories.")
        return redirect('restaurants:dashboard')
    
    if request.method == 'POST':
        try:
            # Use the utility function to get restaurant for user
            restaurant = get_restaurant_for_user(request.user)
            if not restaurant:
                messages.error(request, "No restaurant found for your account.")
                return redirect('restaurants:dashboard')
                
            category_id = request.POST.get('category_id')
            category = MenuCategory.objects.get(id=category_id, restaurant=restaurant)
            category_name = category.name
            category.delete()
            
            messages.success(request, f"Category {category_name} has been deleted successfully.")
            return redirect('restaurants:menu_categories')
        except (MenuCategory.DoesNotExist) as e:
            messages.error(request, f"Error deleting category: {str(e)}")
            return redirect('restaurants:menu_categories')
    return redirect('restaurants:menu_categories')

@login_required
def add_menu_item(request):
    """Add a new menu item"""
    # Check if user has permission to manage menu items
    if not hasattr(request.user, 'role') or request.user.role == 'staff':
        messages.error(request, "You don't have permission to manage menu items.")
        return redirect('restaurants:dashboard')
    
    if request.method == 'POST':
        try:
            # Use the utility function to get restaurant for user
            restaurant = get_restaurant_for_user(request.user)
            if not restaurant:
                messages.error(request, "No restaurant found for your account.")
                return redirect('restaurants:dashboard')
                
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
            
            messages.success(request, f"Menu item {item.name} has been created successfully.")
            return redirect('restaurants:menu_items')
        except Exception as e:
            messages.error(request, f"Error creating menu item: {str(e)}")
            return redirect('restaurants:menu_items')
    return redirect('restaurants:menu_items')

@login_required
def edit_menu_item(request):
    """Edit an existing menu item"""
    # Check if user has permission to manage menu items
    if not hasattr(request.user, 'role') or request.user.role == 'staff':
        messages.error(request, "You don't have permission to manage menu items.")
        return redirect('restaurants:dashboard')
    
    if request.method == 'POST':
        try:
            # Use the utility function to get restaurant for user
            restaurant = get_restaurant_for_user(request.user)
            if not restaurant:
                messages.error(request, "No restaurant found for your account.")
                return redirect('restaurants:dashboard')
                
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
            
            messages.success(request, f"Menu item {item.name} has been updated successfully.")
            return redirect('restaurants:menu_items')
        except Exception as e:
            messages.error(request, f"Error updating menu item: {str(e)}")
            return redirect('restaurants:menu_items')
    return redirect('restaurants:menu_items')

@login_required
def delete_menu_item(request):
    """Delete a menu item"""
    if request.method == 'POST':
        try:
            # Use the utility function to get restaurant for user
            restaurant = get_restaurant_for_user(request.user)
            if not restaurant:
                messages.error(request, "No restaurant found for your account.")
                return redirect('restaurants:dashboard')
            
            item_id = request.POST.get('item_id')
            
            # Verify the item belongs to this restaurant
            item = MenuItem.objects.get(id=item_id, category__restaurant=restaurant)
            item.delete()
            
            messages.success(request, f"Menu item has been deleted successfully.")
            return redirect('restaurants:menu_items')
        except MenuItem.DoesNotExist:
            messages.error(request, "Menu item not found or you don't have permission to delete it.")
            return redirect('restaurants:menu_items')
    return redirect('restaurants:menu_items')

@login_required
def add_table(request):
    """Add a new table"""
    if request.method == 'POST':
        # Use the utility function to get the correct restaurant for this user
        restaurant = get_restaurant_for_user(request.user)
        
        if not restaurant:
            if request.user.role == 'restaurant_owner':
                messages.error(request, "You need to create a restaurant first.")
                return redirect('restaurants:create_restaurant')
            else:
                messages.error(request, "You don't have a restaurant assigned to your account.")
                return redirect('restaurants:dashboard')
        
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
    
    return redirect('restaurants:tables')

@login_required
def edit_table(request):
    """Edit an existing table"""
    if request.method == 'POST':
        try:
            # Use the utility function to get restaurant for user
            restaurant = get_restaurant_for_user(request.user)
            
            if not restaurant:
                if request.user.role == 'restaurant_owner':
                    messages.error(request, "You need to create a restaurant first.")
                    return redirect('restaurants:create_restaurant')
                else:
                    messages.error(request, "You don't have a restaurant assigned to your account.")
                    return redirect('restaurants:dashboard')
            
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
            
        except Table.DoesNotExist:
            messages.error(request, "Table not found or you don't have permission to edit it.")
            
    return redirect('restaurants:tables')

@login_required
def delete_table(request):
    """Delete a table"""
    if request.method == 'POST':
        try:
            # Use the utility function to get restaurant for user
            restaurant = get_restaurant_for_user(request.user)
            
            if not restaurant:
                if request.user.role == 'restaurant_owner':
                    messages.error(request, "You need to create a restaurant first.")
                    return redirect('restaurants:create_restaurant')
                else:
                    messages.error(request, "You don't have a restaurant assigned to your account.")
                    return redirect('restaurants:dashboard')
            
            table_id = request.POST.get('table_id')
            table = Table.objects.get(id=table_id, restaurant=restaurant)
            table_number = table.table_number
            
            table.delete()
            
            messages.success(request, f"Table #{table_number} has been deleted.")
            
        except Table.DoesNotExist:
            messages.error(request, "Table not found or you don't have permission to delete it.")
            
    return redirect('restaurants:tables')

@login_required
def generate_qr(request, table_id):
    """Generate QR code for a table"""
    try:
        table = Table.objects.get(id=table_id)
        restaurant = table.restaurant
        
        # Check if the user has access to this restaurant
        user_restaurant = get_restaurant_for_user(request.user)
        if user_restaurant is None or user_restaurant.id != restaurant.id:
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
