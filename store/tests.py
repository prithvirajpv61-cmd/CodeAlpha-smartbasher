from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from store.models import Category, Product, CartItem, Order, OrderItem


class ShopEaseTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # Create Category
        self.category = Category.objects.create(name='Electronics', description='Tech gear')
        
        # Create Product
        self.product = Product.objects.create(
            category=self.category,
            name='Test Wireless Earbuds',
            description='Premium earbuds with active noise cancellation.',
            price=Decimal('1999.00'),
            stock=10,
            is_available=True
        )

        # Create Test User
        self.user_password = 'TestPassword123'
        self.user = User.objects.create_user(
            username='testshopper',
            email='shopper@example.com',
            password=self.user_password,
            first_name='John',
            last_name='Doe'
        )

    def test_homepage_loads(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ShopEase')
        self.assertContains(response, 'Test Wireless Earbuds')

    def test_product_catalog_and_filter(self):
        # Product list view
        response = self.client.get(reverse('product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Wireless Earbuds')

        # Filter by category
        response_cat = self.client.get(reverse('product_list') + f'?category={self.category.slug}')
        self.assertEqual(response_cat.status_code, 200)
        self.assertContains(response_cat, 'Test Wireless Earbuds')

        # Search query
        response_search = self.client.get(reverse('product_list') + '?q=Earbuds')
        self.assertEqual(response_search.status_code, 200)
        self.assertContains(response_search, 'Test Wireless Earbuds')

    def test_product_detail(self):
        response = self.client.get(reverse('product_detail', kwargs={'slug': self.product.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Wireless Earbuds')
        self.assertContains(response, '₹1,999.00')

    def test_cart_operations(self):
        # Add to cart
        response = self.client.post(reverse('add_to_cart', args=[self.product.id]), {'quantity': 2}, follow=True)
        self.assertEqual(response.status_code, 200)

        # Check cart item exists in session/cart
        cart_items = CartItem.objects.all()
        self.assertEqual(cart_items.count(), 1)
        item = cart_items.first()
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.subtotal, Decimal('3998.00'))

        # Update cart quantity (increase)
        response_inc = self.client.post(reverse('update_cart', args=[item.id]), {'action': 'increase'}, follow=True)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 3)

        # Update cart quantity (decrease)
        response_dec = self.client.post(reverse('update_cart', args=[item.id]), {'action': 'decrease'}, follow=True)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 2)

        # Remove from cart
        response_rem = self.client.post(reverse('remove_from_cart', args=[item.id]), follow=True)
        self.assertEqual(CartItem.objects.count(), 0)

    def test_user_registration_and_login(self):
        # Case A: Register with a new username and valid details
        reg_data = {
            'username': 'newuser123',
            'first_name': 'Alice',
            'last_name': 'Smith',
            'email': 'alice@example.com',
            'password': 'SecurePassword123',
            'password_confirm': 'SecurePassword123'
        }
        response = self.client.post(reverse('register'), reg_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username='newuser123').exists())

        # Case G: Log in with newly registered account
        self.client.logout()
        login_response = self.client.post(reverse('login'), {
            'username': 'newuser123',
            'password': 'SecurePassword123'
        }, follow=True)
        self.assertEqual(login_response.status_code, 200)
        self.assertTrue(login_response.context['user'].is_authenticated)

    def test_registration_duplicate_username(self):
        # Case B: Register with an existing username -> friendly validation error
        reg_data = {
            'username': 'testshopper',  # Already created in setUp
            'email': 'different_email@example.com',
            'password': 'SecurePassword123',
            'password_confirm': 'SecurePassword123'
        }
        response = self.client.post(reverse('register'), reg_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This username is already taken. Please choose another username.")

    def test_registration_duplicate_email(self):
        # Case C: Register with an existing email -> friendly validation error
        reg_data = {
            'username': 'uniquename999',
            'email': 'shopper@example.com',  # Already created in setUp
            'password': 'SecurePassword123',
            'password_confirm': 'SecurePassword123'
        }
        response = self.client.post(reverse('register'), reg_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This email address is already registered. Please log in or use another email.")

    def test_registration_mismatched_passwords(self):
        # Case D: Mismatched passwords
        reg_data = {
            'username': 'mismatch_user',
            'email': 'mismatch@example.com',
            'password': 'PasswordOne123',
            'password_confirm': 'PasswordTwo123'
        }
        response = self.client.post(reverse('register'), reg_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Passwords do not match.")

    def test_registration_empty_required_fields(self):
        # Case E: Empty required fields
        response = self.client.post(reverse('register'), {
            'username': '',
            'email': '',
            'password': '',
            'password_confirm': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())

    def test_registration_repeated_existing_username(self):
        # Case F: Register with existing username repeatedly - must never crash
        reg_data = {
            'username': 'testshopper',
            'email': 'retry@example.com',
            'password': 'Password123',
            'password_confirm': 'Password123'
        }
        for _ in range(3):
            response = self.client.post(reverse('register'), reg_data)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "This username is already taken. Please choose another username.")

    def test_checkout_and_order_processing(self):
        # Login user
        self.client.login(username='testshopper', password=self.user_password)

        # Add product to cart
        self.client.post(reverse('add_to_cart', args=[self.product.id]), {'quantity': 2})
        self.assertEqual(CartItem.objects.filter(user=self.user).count(), 1)

        initial_stock = self.product.stock

        # Submit checkout
        checkout_data = {
            'full_name': 'John Doe',
            'email': 'shopper@example.com',
            'phone': '9876543210',
            'address': 'Flat 402, Lotus Residency, MG Road',
            'city': 'Bengaluru',
            'state': 'Karnataka',
            'postal_code': '560001',
            'payment_method': 'cod',
            'notes': 'Please call before arrival'
        }
        response = self.client.post(reverse('checkout'), checkout_data, follow=True)
        self.assertEqual(response.status_code, 200)

        # Verify Order was created
        order = Order.objects.filter(user=self.user).first()
        self.assertIsNotNone(order)
        self.assertTrue(order.order_reference.startswith('SE-'))
        self.assertEqual(order.payment_method, 'cod')
        
        # Verify OrderItem preserves price
        order_item = order.items.first()
        self.assertEqual(order_item.product_name, 'Test Wireless Earbuds')
        self.assertEqual(order_item.price, Decimal('1999.00'))
        self.assertEqual(order_item.quantity, 2)
        self.assertEqual(order_item.subtotal, Decimal('3998.00'))

        # Verify stock was safely decremented
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, initial_stock - 2)

        # Verify user's cart is empty
        self.assertEqual(CartItem.objects.filter(user=self.user).count(), 0)

        # Verify order history access
        orders_response = self.client.get(reverse('my_orders'))
        self.assertEqual(orders_response.status_code, 200)
        self.assertContains(orders_response, order.order_reference)

    def test_stock_protection(self):
        # Try to buy more than available stock
        self.client.login(username='testshopper', password=self.user_password)
        CartItem.objects.create(user=self.user, product=self.product, quantity=999)

        checkout_data = {
            'full_name': 'John Doe',
            'email': 'shopper@example.com',
            'phone': '9876543210',
            'address': 'MG Road',
            'city': 'Bengaluru',
            'state': 'Karnataka',
            'postal_code': '560001',
            'payment_method': 'cod'
        }
        response = self.client.post(reverse('checkout'), checkout_data, follow=True)
        # Should fail with error message and NOT create order
        self.assertEqual(Order.objects.count(), 0)
        self.assertContains(response, 'Insufficient stock')

    def test_buy_now_authenticated_flow_and_cart_preservation(self):
        # 1. User puts an unrelated product into the cart first
        unrelated_product = Product.objects.create(
            category=self.category,
            name='Unrelated Cart Product',
            description='Should remain in cart.',
            price=Decimal('500.00'),
            stock=20,
            is_available=True
        )
        self.client.login(username='testshopper', password=self.user_password)
        self.client.post(reverse('add_to_cart', args=[unrelated_product.id]), {'quantity': 1})
        self.assertEqual(CartItem.objects.filter(user=self.user).count(), 1)

        # 2. User clicks "Buy Now" on self.product with quantity 2
        initial_stock = self.product.stock
        buy_now_resp = self.client.post(reverse('buy_now', args=[self.product.id]), {'quantity': 2})
        # Should redirect to checkout with buy_now parameters
        self.assertEqual(buy_now_resp.status_code, 302)
        self.assertIn('buy_now=1', buy_now_resp.url)
        self.assertIn(f'product_id={self.product.id}', buy_now_resp.url)

        # 3. Follow redirect to checkout page
        checkout_page_resp = self.client.get(buy_now_resp.url)
        self.assertEqual(checkout_page_resp.status_code, 200)
        self.assertContains(checkout_page_resp, self.product.name)
        self.assertTrue(checkout_page_resp.context['is_buy_now'])

        # 4. Place Buy Now Order
        checkout_payload = {
            'buy_now': '1',
            'product_id': self.product.id,
            'quantity': '2',
            'full_name': 'John Doe',
            'email': 'shopper@example.com',
            'phone': '9876543210',
            'address': 'Direct Buy Road',
            'city': 'Bengaluru',
            'state': 'Karnataka',
            'postal_code': '560001',
            'payment_method': 'cod',
            'notes': 'Instant delivery'
        }
        order_resp = self.client.post(reverse('checkout'), checkout_payload, follow=True)
        self.assertEqual(order_resp.status_code, 200)

        # 5. Verify Order & Stock
        order = Order.objects.filter(user=self.user).order_by('-created_at').first()
        self.assertIsNotNone(order)
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.first().product, self.product)
        self.assertEqual(order.items.first().quantity, 2)

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, initial_stock - 2)

        # 6. CRITICAL VERIFICATION: Unrelated cart item is STILL in the cart!
        cart_items = CartItem.objects.filter(user=self.user)
        self.assertEqual(cart_items.count(), 1)
        self.assertEqual(cart_items.first().product, unrelated_product)
        self.assertEqual(cart_items.first().quantity, 1)

    def test_buy_now_unauthenticated_flow_preserves_selection(self):
        # Anonymous user clicks Buy Now
        buy_now_resp = self.client.post(reverse('buy_now', args=[self.product.id]), {'quantity': 3})
        self.assertEqual(buy_now_resp.status_code, 302)
        # Should redirect to login with next url pointing to checkout
        self.assertIn(reverse('login'), buy_now_resp.url)
        self.assertIn('next=', buy_now_resp.url)

        # User logs in
        login_resp = self.client.post(reverse('login'), {
            'username': 'testshopper',
            'password': self.user_password
        }, follow=True)
        self.assertEqual(login_resp.status_code, 200)

        # Check session or direct checkout URL has buy_now_item preserved
        checkout_resp = self.client.get(reverse('checkout') + f"?buy_now=1&product_id={self.product.id}&quantity=3")
        self.assertEqual(checkout_resp.status_code, 200)
        self.assertContains(checkout_resp, self.product.name)

    def test_buy_now_out_of_stock_rejected(self):
        self.product.stock = 0
        self.product.save()

        response = self.client.post(reverse('buy_now', args=[self.product.id]), {'quantity': 1}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'out of stock')

