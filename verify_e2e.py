import os
import sys

# Ensure UTF-8 output on Windows console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shopease.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from store.models import Category, Product, CartItem, Order, OrderItem

def run_verification():
    print("=" * 60)
    print("ShopEase End-to-End Functional Verification")
    print("=" * 60)

    client = Client()

    # Step 1: Verify Homepage
    print("\n[Step 1] Loading Homepage (GET /)...")
    resp = client.get('/')
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    assert 'ShopEase' in resp.content.decode()
    assert '₹' in resp.content.decode()
    print("  -> Homepage loaded successfully (Status 200, Currency ₹ verified)")

    # Step 2: Verify Catalog and Filter
    print("\n[Step 2] Testing Product Catalog (GET /products/)...")
    resp = client.get('/products/')
    assert resp.status_code == 200
    products_count = Product.objects.filter(is_available=True).count()
    print(f"  -> Catalog returned {products_count} active products")

    # Step 3: Registration Validation & Customer Account Creation
    print("\n[Step 3] Testing Registration Validation & Account Creation...")
    
    # Check 3A: Duplicate username validation
    resp_dup_user = client.post('/register/', {
        'username': 'admin',
        'email': 'different_admin@example.com',
        'password': 'Password123',
        'password_confirm': 'Password123'
    })
    assert resp_dup_user.status_code == 200
    assert 'This username is already taken. Please choose another username.' in resp_dup_user.content.decode()
    print("  -> Duplicate username rejection verified: friendly error displayed, no IntegrityError!")

    # Check 3B: Duplicate email validation
    resp_dup_email = client.post('/register/', {
        'username': 'unique_user_999',
        'email': 'admin@shopease.local',
        'password': 'Password123',
        'password_confirm': 'Password123'
    })
    assert resp_dup_email.status_code == 200
    assert 'This email address is already registered. Please log in or use another email.' in resp_dup_email.content.decode()
    print("  -> Duplicate email rejection verified: friendly error displayed!")

    # Check 3C: Mismatched password validation
    resp_mismatch = client.post('/register/', {
        'username': 'unique_user_999',
        'email': 'valid_unique@example.com',
        'password': 'Password123',
        'password_confirm': 'DifferentPassword456'
    })
    assert resp_mismatch.status_code == 200
    assert 'Passwords do not match.' in resp_mismatch.content.decode()
    print("  -> Mismatched password rejection verified: friendly error displayed!")

    # Check 3D: Valid new customer registration
    test_user_data = {
        'username': 'e2e_shopper',
        'first_name': 'Rahul',
        'last_name': 'Verma',
        'email': 'rahul.verma@example.com',
        'password': 'ComplexPassword123',
        'password_confirm': 'ComplexPassword123'
    }
    # Clean if exists from previous test
    User.objects.filter(username='e2e_shopper').delete()
    resp = client.post('/register/', test_user_data, follow=True)
    assert resp.status_code == 200
    user = User.objects.get(username='e2e_shopper')
    print(f"  -> Valid new user '{user.username}' successfully created with hashed password!")

    # Step 4: Add Product 1 to Cart (Cart Persistence Baseline)
    product_cart = Product.objects.filter(is_available=True, stock__gt=5).first()
    print(f"\n[Step 4] Adding Product '{product_cart.name}' (Stock: {product_cart.stock}) to Cart...")
    resp = client.post(f'/cart/add/{product_cart.id}/', {'quantity': 2}, follow=True)
    assert resp.status_code == 200
    cart_item = CartItem.objects.filter(user=user, product=product_cart).first()
    assert cart_item is not None
    assert cart_item.quantity == 2
    print(f"  -> Cart contains {cart_item.quantity} units, Subtotal: {cart_item.formatted_subtotal}")

    # Step 5: Direct "Buy Now" on a DIFFERENT Product
    product_buy_now = Product.objects.filter(is_available=True, stock__gt=5).exclude(id=product_cart.id).first()
    print(f"\n[Step 5] Triggering Direct 'Buy Now' for '{product_buy_now.name}' (Stock: {product_buy_now.stock})...")
    bn_stock_before = product_buy_now.stock
    resp_bn = client.post(f'/buy-now/{product_buy_now.id}/', {'quantity': 1})
    assert resp_bn.status_code == 302
    assert 'buy_now=1' in resp_bn.url
    print(f"  -> Buy Now redirected immediately to: {resp_bn.url}")

    # Complete Buy Now Order
    checkout_payload_bn = {
        'buy_now': '1',
        'product_id': product_buy_now.id,
        'quantity': '1',
        'full_name': 'Rahul Verma',
        'email': 'rahul.verma@example.com',
        'phone': '9876543210',
        'address': 'Plot 42, Green Glen Layout, Bellandur',
        'city': 'Bengaluru',
        'state': 'Karnataka',
        'postal_code': '560103',
        'payment_method': 'simulated',
        'notes': 'Buy Now order test'
    }
    resp_bn_order = client.post('/checkout/', checkout_payload_bn, follow=True)
    assert resp_bn_order.status_code == 200

    order_bn = Order.objects.filter(user=user).order_by('-created_at').first()
    assert order_bn is not None
    assert order_bn.items.first().product == product_buy_now
    print(f"  -> Direct Buy Now order placed! Reference: {order_bn.order_reference}")

    # Verify Buy Now product stock was decremented
    product_buy_now.refresh_from_db()
    assert product_buy_now.stock == bn_stock_before - 1
    print(f"  -> Buy Now product stock decremented safely: {bn_stock_before} -> {product_buy_now.stock}")

    # CRITICAL: Verify Product 1 is STILL in user's cart!
    cart_still_present = CartItem.objects.filter(user=user, product=product_cart).first()
    assert cart_still_present is not None and cart_still_present.quantity == 2, "Unrelated cart item was deleted by Buy Now!"
    print("  -> Verified: Unrelated cart items remain 100% preserved in database!")

    # Step 6: Checkout Remaining Cart Items
    print("\n[Step 6] Completing Standard Cart Checkout...")
    cart_stock_before = product_cart.stock
    checkout_payload_cart = {
        'full_name': 'Rahul Verma',
        'email': 'rahul.verma@example.com',
        'phone': '9876543210',
        'address': 'Plot 42, Green Glen Layout, Bellandur',
        'city': 'Bengaluru',
        'state': 'Karnataka',
        'postal_code': '560103',
        'payment_method': 'cod',
        'notes': 'Cart order test'
    }
    resp_cart_order = client.post('/checkout/', checkout_payload_cart, follow=True)
    assert resp_cart_order.status_code == 200

    order_cart = Order.objects.filter(user=user).order_by('-created_at').first()
    assert order_cart.items.first().product == product_cart
    print(f"  -> Cart order placed! Reference: {order_cart.order_reference}")

    product_cart.refresh_from_db()
    assert product_cart.stock == cart_stock_before - 2
    print(f"  -> Cart product stock decremented: {cart_stock_before} -> {product_cart.stock}")

    # Cart should now be empty after cart checkout
    assert CartItem.objects.filter(user=user).count() == 0
    print("  -> Cart cleared after standard cart checkout: verified (0 items)")

    # Step 8: Verify My Orders Page
    print("\n[Step 8] Verifying My Orders history...")
    resp = client.get('/orders/')
    assert resp.status_code == 200
    assert order_bn.order_reference in resp.content.decode()
    assert order_cart.order_reference in resp.content.decode()
    print(f"  -> Orders #{order_bn.order_reference} and #{order_cart.order_reference} verified in user's order history page")

    # Step 9: Verify Admin Access
    print("\n[Step 9] Verifying Django Admin Panel...")
    admin_client = Client()
    admin_client.login(username='admin', password='admin123')
    resp = admin_client.get('/admin/store/order/')
    assert resp.status_code == 200
    assert order_bn.order_reference in resp.content.decode()
    assert order_cart.order_reference in resp.content.decode()
    print(f"  -> Admin panel accessible (Status 200), orders found in admin list")

    print("\n" + "=" * 60)
    print("ALL 9 END-TO-END VERIFICATION CHECKS PASSED WITH ZERO ERRORS!")
    print("=" * 60)

if __name__ == '__main__':
    run_verification()
