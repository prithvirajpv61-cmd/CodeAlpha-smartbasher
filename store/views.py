from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Category, Product, CartItem, Order, OrderItem
from .forms import UserRegisterForm, UserLoginForm, CheckoutForm


# ==========================================
# Cart Helper Utilities
# ==========================================

def get_or_create_session_key(request):
    """Ensures a session key exists for anonymous cart tracking."""
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def get_user_cart_items(request):
    """Returns queryset of CartItems for the current user or guest session."""
    if request.user.is_authenticated:
        return CartItem.objects.filter(user=request.user).select_related('product')
    else:
        session_key = get_or_create_session_key(request)
        return CartItem.objects.filter(session_key=session_key).select_related('product')


def merge_session_cart_to_user(session_key, user):
    """Merges anonymous session cart items into the authenticated user's cart."""
    if not session_key or not user.is_authenticated:
        return

    session_items = CartItem.objects.filter(session_key=session_key)
    for s_item in session_items:
        existing = CartItem.objects.filter(user=user, product=s_item.product).first()
        if existing:
            # Add quantities up to available product stock
            new_qty = min(existing.quantity + s_item.quantity, s_item.product.stock)
            existing.quantity = max(new_qty, 1)
            existing.save()
            s_item.delete()
        else:
            s_item.user = user
            s_item.session_key = None
            s_item.save()


# ==========================================
# Store & Catalog Views
# ==========================================

def home(request):
    """Modern home page showcasing featured products, categories, and hero banner."""
    categories = Category.objects.all()
    featured_products = Product.objects.filter(is_available=True, is_featured=True)[:8]
    if not featured_products.exists():
        featured_products = Product.objects.filter(is_available=True)[:8]

    latest_products = Product.objects.filter(is_available=True).order_by('-created_at')[:8]

    context = {
        'categories': categories,
        'featured_products': featured_products,
        'latest_products': latest_products,
    }
    return render(request, 'home.html', context)


def product_list(request):
    """Product catalog with searching, category filtering, stock filtering, and sorting."""
    products = Product.objects.filter(is_available=True)
    categories = Category.objects.all()

    category_slug = request.GET.get('category', '').strip()
    search_query = request.GET.get('q', '').strip()
    sort_option = request.GET.get('sort', '').strip()
    in_stock_only = request.GET.get('in_stock', '').strip()

    active_category = None
    if category_slug:
        active_category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=active_category)

    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )

    if in_stock_only == '1':
        products = products.filter(stock__gt=0)

    # Sorting options
    if sort_option == 'price_asc':
        products = products.order_by('price')
    elif sort_option == 'price_desc':
        products = products.order_by('-price')
    elif sort_option == 'name':
        products = products.order_by('name')
    elif sort_option == 'newest':
        products = products.order_by('-created_at')
    else:
        products = products.order_by('-created_at')

    total_count = products.count()

    context = {
        'products': products,
        'categories': categories,
        'active_category': active_category,
        'search_query': search_query,
        'sort_option': sort_option,
        'in_stock_only': in_stock_only,
        'total_count': total_count,
    }
    return render(request, 'product_list.html', context)


def product_detail(request, slug):
    """Detailed view for a specific product with quantity selector and related items."""
    product = get_object_or_404(Product, slug=slug)
    related_products = Product.objects.filter(
        category=product.category,
        is_available=True
    ).exclude(id=product.id)[:4]

    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'product_detail.html', context)


# ==========================================
# Shopping Cart Views
# ==========================================

def cart_view(request):
    """Displays cart items, subtotals, grand total, and delivery fees."""
    cart_items = get_user_cart_items(request)
    
    # Calculate subtotal strictly using current database product prices
    subtotal = Decimal('0.00')
    has_stock_issues = False

    for item in cart_items:
        # Check if requested quantity exceeds current stock
        if item.quantity > item.product.stock:
            item.stock_warning = f"Only {item.product.stock} available in stock!"
            has_stock_issues = True
        subtotal += item.subtotal

    shipping_threshold = Decimal('999.00')
    standard_shipping = Decimal('99.00')
    shipping_fee = Decimal('0.00') if subtotal >= shipping_threshold or subtotal == 0 else standard_shipping
    grand_total = subtotal + shipping_fee

    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping_fee': shipping_fee,
        'shipping_threshold': shipping_threshold,
        'grand_total': grand_total,
        'has_stock_issues': has_stock_issues,
    }
    return render(request, 'cart.html', context)


@require_POST
def add_to_cart(request, product_id):
    """Adds a product to the cart with server-side quantity and stock validation."""
    product = get_object_or_404(Product, id=product_id)

    if not product.is_in_stock:
        messages.error(request, f"Sorry, '{product.name}' is currently out of stock.")
        return redirect(request.META.get('HTTP_REFERER', 'product_list'))

    try:
        requested_qty = int(request.POST.get('quantity', 1))
        if requested_qty < 1:
            requested_qty = 1
    except ValueError:
        requested_qty = 1

    # Get user or session identifier
    if request.user.is_authenticated:
        cart_item, created = CartItem.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={'quantity': requested_qty}
        )
    else:
        session_key = get_or_create_session_key(request)
        cart_item, created = CartItem.objects.get_or_create(
            session_key=session_key,
            product=product,
            defaults={'quantity': requested_qty}
        )

    if not created:
        new_quantity = cart_item.quantity + requested_qty
        if new_quantity > product.stock:
            cart_item.quantity = product.stock
            cart_item.save()
            messages.warning(request, f"Quantity adjusted to maximum available stock ({product.stock}) for '{product.name}'.")
        else:
            cart_item.quantity = new_quantity
            cart_item.save()
            messages.success(request, f"Updated quantity for '{product.name}' in your cart.")
    else:
        if cart_item.quantity > product.stock:
            cart_item.quantity = product.stock
            cart_item.save()
        messages.success(request, f"'{product.name}' was added to your cart!")

    # Check if AJAX request
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        cart_items = get_user_cart_items(request)
        total_count = sum(item.quantity for item in cart_items)
        return JsonResponse({
            'status': 'success',
            'message': f"Added '{product.name}' to cart.",
            'cart_count': total_count
        })

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or 'cart'
    return redirect(next_url)


@require_POST
def update_cart(request, item_id):
    """Updates item quantity (increase, decrease, or set) with stock enforcement."""
    if request.user.is_authenticated:
        cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
    else:
        session_key = get_or_create_session_key(request)
        cart_item = get_object_or_404(CartItem, id=item_id, session_key=session_key)

    action = request.POST.get('action')

    if action == 'increase':
        if cart_item.quantity < cart_item.product.stock:
            cart_item.quantity += 1
            cart_item.save()
            messages.success(request, f"Increased quantity for {cart_item.product.name}.")
        else:
            messages.warning(request, f"Maximum available stock for {cart_item.product.name} reached.")
    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
            messages.info(request, f"Decreased quantity for {cart_item.product.name}.")
        else:
            cart_item.delete()
            messages.info(request, f"Removed {cart_item.product.name} from your cart.")
    elif action == 'set':
        try:
            new_qty = int(request.POST.get('quantity', 1))
            if new_qty <= 0:
                cart_item.delete()
                messages.info(request, f"Removed {cart_item.product.name} from your cart.")
            elif new_qty > cart_item.product.stock:
                cart_item.quantity = cart_item.product.stock
                cart_item.save()
                messages.warning(request, f"Set to max stock ({cart_item.product.stock}) for {cart_item.product.name}.")
            else:
                cart_item.quantity = new_qty
                cart_item.save()
        except ValueError:
            pass

    return redirect('cart')


@require_POST
def remove_from_cart(request, item_id):
    """Removes an item completely from the cart."""
    if request.user.is_authenticated:
        cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
    else:
        session_key = get_or_create_session_key(request)
        cart_item = get_object_or_404(CartItem, id=item_id, session_key=session_key)

    product_name = cart_item.product.name
    cart_item.delete()
    messages.info(request, f"Removed '{product_name}' from your cart.")
    return redirect('cart')


# ==========================================
# Checkout & Order Processing
# ==========================================

def buy_now_view(request, product_id):
    """
    Direct Buy Now handler:
    Validates product availability and stock, preserves selection in session & URL,
    and forwards user immediately to checkout (handling login redirect with full state preservation).
    """
    product = get_object_or_404(Product, id=product_id)

    if not product.is_in_stock:
        messages.error(request, f"Sorry, '{product.name}' is currently out of stock.")
        return redirect(request.META.get('HTTP_REFERER') or 'product_list')

    try:
        qty = int(request.POST.get('quantity') or request.GET.get('quantity') or 1)
        if qty < 1:
            qty = 1
    except (ValueError, TypeError):
        qty = 1

    if qty > product.stock:
        messages.warning(request, f"Requested quantity exceeds available stock. Adjusted to {product.stock}.")
        qty = product.stock

    # Store Buy Now intent in session to guarantee preservation across redirects/logins
    request.session['buy_now_item'] = {
        'product_id': product.id,
        'quantity': qty
    }

    checkout_url = reverse('checkout') + f"?buy_now=1&product_id={product.id}&quantity={qty}"

    if not request.user.is_authenticated:
        messages.info(request, "Please sign in to complete your instant purchase.")
        login_url = reverse('login') + f"?next={checkout_url}"
        return redirect(login_url)

    return redirect(checkout_url)


@login_required
def checkout_view(request):
    """
    Checkout page that computes totals on the server and executes
    atomic order creation with stock validation and inventory deduction.
    Supports both:
    1) Direct 'Buy Now' instant purchase for a selected product
    2) Standard multi-item shopping cart checkout
    """
    # Determine if this checkout is a Buy Now flow
    is_buy_now = (
        request.POST.get('buy_now') == '1' or 
        request.GET.get('buy_now') == '1' or 
        ('buy_now_item' in request.session and not request.GET.get('cart') == '1')
    )

    buy_now_product = None
    buy_now_qty = 1

    if is_buy_now:
        p_id = (
            request.POST.get('product_id') or 
            request.GET.get('product_id') or 
            request.session.get('buy_now_item', {}).get('product_id')
        )
        q_val = (
            request.POST.get('quantity') or 
            request.GET.get('quantity') or 
            request.session.get('buy_now_item', {}).get('quantity') or 1
        )
        try:
            buy_now_product = Product.objects.get(id=int(p_id))
            buy_now_qty = max(1, int(q_val))
        except (Product.DoesNotExist, ValueError, TypeError):
            is_buy_now = False
            buy_now_product = None

    shipping_threshold = Decimal('999.00')

    # ==========================================
    # Branch A: Direct Buy Now Checkout
    # ==========================================
    if is_buy_now and buy_now_product:
        if not buy_now_product.is_in_stock:
            messages.error(request, f"Sorry, '{buy_now_product.name}' is out of stock.")
            request.session.pop('buy_now_item', None)
            return redirect('product_detail', slug=buy_now_product.slug)

        if buy_now_qty > buy_now_product.stock:
            messages.warning(request, f"Quantity adjusted to available stock ({buy_now_product.stock}) for '{buy_now_product.name}'.")
            buy_now_qty = buy_now_product.stock

        subtotal = Decimal(buy_now_product.price) * buy_now_qty
        shipping_fee = Decimal('0.00') if subtotal >= shipping_threshold else Decimal('99.00')
        grand_total = subtotal + shipping_fee

        checkout_items = [{
            'product': buy_now_product,
            'quantity': buy_now_qty,
            'formatted_subtotal': f"₹{subtotal:,.2f}",
        }]

        if request.method == 'POST':
            form = CheckoutForm(request.POST)
            if form.is_valid():
                try:
                    with transaction.atomic():
                        # Select product for update to lock row
                        prod = Product.objects.select_for_update().get(id=buy_now_product.id)
                        if not prod.is_available or prod.stock < buy_now_qty:
                            raise ValueError(
                                f"Insufficient stock for '{prod.name}'. Only {prod.stock} unit(s) available."
                            )

                        verified_subtotal = Decimal(prod.price) * buy_now_qty
                        verified_shipping = Decimal('0.00') if verified_subtotal >= shipping_threshold else Decimal('99.00')
                        final_total = verified_subtotal + verified_shipping

                        order = form.save(commit=False)
                        order.user = request.user
                        order.order_reference = Order.generate_reference()
                        order.total_amount = final_total

                        if order.payment_method == 'simulated':
                            order.payment_status = 'Completed'
                            order.order_status = 'Processing'
                        else:
                            order.payment_status = 'Pending'
                            order.order_status = 'Pending'

                        order.save()

                        # Create OrderItem preserving price
                        OrderItem.objects.create(
                            order=order,
                            product=prod,
                            product_name=prod.name,
                            price=prod.price,
                            quantity=buy_now_qty
                        )

                        # Decrement stock safely
                        prod.stock -= buy_now_qty
                        prod.save(update_fields=['stock'])

                        # Clear buy now session item
                        request.session.pop('buy_now_item', None)
                        # NOTE: Existing CartItems in database/session are deliberately untouched!

                    messages.success(request, f"Order #{order.order_reference} placed successfully! Thank you for shopping with ShopEase.")
                    return redirect('order_confirmation', order_reference=order.order_reference)

                except ValueError as e:
                    messages.error(request, str(e))
                    return redirect('product_detail', slug=buy_now_product.slug)
                except Exception as e:
                    messages.error(request, f"An unexpected error occurred during checkout: {str(e)}")
                    return redirect('checkout')
        else:
            initial_data = {
                'full_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
                'email': request.user.email,
            }
            form = CheckoutForm(initial=initial_data)

        context = {
            'form': form,
            'cart_items': checkout_items,
            'subtotal': subtotal,
            'shipping_fee': shipping_fee,
            'grand_total': grand_total,
            'is_buy_now': True,
            'buy_now_product': buy_now_product,
            'buy_now_qty': buy_now_qty,
        }
        return render(request, 'checkout.html', context)

    # ==========================================
    # Branch B: Standard Cart Checkout
    # ==========================================
    cart_items = CartItem.objects.filter(user=request.user).select_related('product')

    if not cart_items.exists():
        messages.warning(request, "Your cart is empty. Please add items before checking out.")
        return redirect('product_list')

    # Pre-calculate subtotal and shipping
    subtotal = sum(item.subtotal for item in cart_items)
    shipping_fee = Decimal('0.00') if subtotal >= shipping_threshold else Decimal('99.00')
    grand_total = subtotal + shipping_fee

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Lock cart items and products for update to prevent race conditions
                    locked_cart_items = CartItem.objects.select_for_update().filter(user=request.user)
                    if not locked_cart_items.exists():
                        messages.error(request, "Your cart is empty.")
                        return redirect('cart')

                    # 1. Re-validate stock and recalculate total securely
                    recalculated_subtotal = Decimal('0.00')
                    products_to_update = []

                    for item in locked_cart_items:
                        prod = Product.objects.select_for_update().get(id=item.product.id)
                        if not prod.is_available or prod.stock < item.quantity:
                            raise ValueError(
                                f"Insufficient stock for '{prod.name}'. Only {prod.stock} unit(s) available. Please adjust your cart."
                            )

                        recalculated_subtotal += (Decimal(prod.price) * item.quantity)
                        products_to_update.append((prod, item.quantity))

                    verified_shipping = Decimal('0.00') if recalculated_subtotal >= shipping_threshold else Decimal('99.00')
                    final_total = recalculated_subtotal + verified_shipping

                    # 2. Create the Order
                    order = form.save(commit=False)
                    order.user = request.user
                    order.order_reference = Order.generate_reference()
                    order.total_amount = final_total

                    if order.payment_method == 'simulated':
                        order.payment_status = 'Completed'
                        order.order_status = 'Processing'
                    else:
                        order.payment_status = 'Pending'
                        order.order_status = 'Pending'

                    order.save()

                    # 3. Create OrderItems & Deduct Stock
                    for prod, qty in products_to_update:
                        OrderItem.objects.create(
                            order=order,
                            product=prod,
                            product_name=prod.name,
                            price=prod.price,  # Preserves purchase price
                            quantity=qty
                        )
                        prod.stock -= qty
                        prod.save(update_fields=['stock'])

                    # 4. Clear the user's cart
                    locked_cart_items.delete()

                messages.success(request, f"Order #{order.order_reference} placed successfully! Thank you for shopping with ShopEase.")
                return redirect('order_confirmation', order_reference=order.order_reference)

            except ValueError as e:
                messages.error(request, str(e))
                return redirect('cart')
            except Exception as e:
                messages.error(request, f"An unexpected error occurred during checkout: {str(e)}")
                return redirect('checkout')
    else:
        initial_data = {
            'full_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
            'email': request.user.email,
        }
        form = CheckoutForm(initial=initial_data)

    context = {
        'form': form,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping_fee': shipping_fee,
        'grand_total': grand_total,
        'is_buy_now': False,
    }
    return render(request, 'checkout.html', context)


@login_required
def order_confirmation(request, order_reference):
    """Displays order receipt and confirmation after successful checkout."""
    order = get_object_or_404(Order, order_reference=order_reference, user=request.user)
    context = {
        'order': order,
    }
    return render(request, 'order_confirmation.html', context)


@login_required
def my_orders(request):
    """Displays order history strictly for the authenticated user."""
    orders = Order.objects.filter(user=request.user).prefetch_related('items__product').order_by('-created_at')
    context = {
        'orders': orders,
    }
    return render(request, 'my_orders.html', context)


@login_required
def order_detail(request, order_reference):
    """Detailed view for a specific historical order belonging to user."""
    order = get_object_or_404(Order, order_reference=order_reference, user=request.user)
    context = {
        'order': order,
    }
    return render(request, 'order_detail.html', context)


# ==========================================
# User Authentication Views
# ==========================================

def register_view(request):
    """User registration with password hashing, input validation, duplicate checks, and cart migration."""
    if request.user.is_authenticated:
        return redirect('home')

    session_key_before_login = request.session.session_key

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)

        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')

        # Explicit pre-validation checks before saving
        if username and User.objects.filter(username__iexact=username).exists():
            form.add_error('username', "This username is already taken. Please choose another username.")

        if email and User.objects.filter(email__iexact=email).exists():
            form.add_error('email', "This email address is already registered. Please log in or use another email.")

        if password and password_confirm and password != password_confirm:
            form.add_error('password_confirm', "Passwords do not match.")

        if form.is_valid():
            try:
                with transaction.atomic():
                    # Double-check inside transaction before creating user
                    cleaned_username = form.cleaned_data['username']
                    cleaned_email = form.cleaned_data['email']

                    if User.objects.filter(username__iexact=cleaned_username).exists():
                        form.add_error('username', "This username is already taken. Please choose another username.")
                        return render(request, 'register.html', {'form': form})

                    if User.objects.filter(email__iexact=cleaned_email).exists():
                        form.add_error('email', "This email address is already registered. Please log in or use another email.")
                        return render(request, 'register.html', {'form': form})

                    user = form.save()
            except IntegrityError:
                form.add_error('username', "This username is already taken. Please choose another username.")
                return render(request, 'register.html', {'form': form})
            except Exception:
                form.add_error(None, "Registration failed due to an unexpected error. Please try again.")
                return render(request, 'register.html', {'form': form})

            # Authenticate and login the new user
            login(request, user)
            # Migrate any guest cart items to the new user account
            if session_key_before_login:
                merge_session_cart_to_user(session_key_before_login, user)

            messages.success(request, f"Welcome to ShopEase, {user.username}! Your account was created successfully.")
            next_url = request.GET.get('next') or 'home'
            return redirect(next_url)
    else:
        form = UserRegisterForm()

    return render(request, 'register.html', {'form': form})


def login_view(request):
    """User login with credential validation, message alerts, and cart migration."""
    if request.user.is_authenticated:
        return redirect('home')

    session_key_before_login = request.session.session_key

    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username_or_email = form.cleaned_data.get('username').strip()
            password = form.cleaned_data.get('password')

            # Check if user passed email instead of username
            user_obj = None
            if '@' in username_or_email:
                user_match = User.objects.filter(email__iexact=username_or_email).first()
                if user_match:
                    user_obj = authenticate(request, username=user_match.username, password=password)
            
            if not user_obj:
                user_obj = authenticate(request, username=username_or_email, password=password)

            if user_obj is not None:
                login(request, user_obj)
                # Migrate any guest cart items to the authenticated user account
                if session_key_before_login:
                    merge_session_cart_to_user(session_key_before_login, user_obj)

                messages.success(request, f"Welcome back, {user_obj.username}!")
                next_url = request.GET.get('next') or 'home'
                return redirect(next_url)
            else:
                messages.error(request, "Invalid username/email or password. Please try again.")
    else:
        form = UserLoginForm()

    return render(request, 'login.html', {'form': form})


def logout_view(request):
    """Logs out user and redirects to home page with confirmation."""
    logout(request)
    messages.info(request, "You have been logged out safely.")
    return redirect('home')
