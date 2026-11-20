# ShopEase - Modern Full-Stack E-Commerce Platform

A complete, fully functional, modern e-commerce web application built with **Python Django**, **SQLite**, **Vanilla HTML5/CSS3/JavaScript**, and **Django ORM**.

ShopEase features an eye-catching, responsive UI designed for Indian online shoppers with prices in Indian Rupees (**₹**), real-time stock management, atomic checkout transactions, and an administrative control panel.

---

## 🌟 Key Features

1. **Modern Responsive Storefront**
   - Sticky navigation with glassmorphism effects, live cart count badge, and category sub-navigation bar.
   - High-impact hero section with festival discount alerts and dynamic action buttons.
   - Dynamic product showcase with category pills, availability badges, and Indian Rupee (`₹`) pricing.
   - Comprehensive search and category/availability filtering.

2. **Interactive Product Catalog & Detail Pages**
   - Real-time catalog filtering by Category, Stock Availability, and Sorting (Price Low-High, Price High-Low, Newest, Name).
   - Detailed product view with zoomable image preview, in-stock counters, quantity selectors (`+` / `-`), and related items carousel.
   - Automatic fallback SVG graphics ensuring no broken image icons ever show up.

3. **Persistent Shopping Cart**
   - Supports both authenticated customer carts and guest session carts with automatic migration upon login/registration.
   - Dynamic item quantity adjustment (+ / -) directly inside the cart.
   - Real-time subtotal calculation and free delivery progress indicator (Free Delivery for orders above ₹999).
   - Strict inventory validation preventing customers from adding more units than available in stock.

4. **Secure User Authentication**
   - Full user registration and login workflows with secure password hashing via Django's PBKDF2 algorithm.
   - User profile indicator in the header and protected routes (`@login_required`) for checkout and order history.

5. **Atomic Checkout & Order Processing**
   - Two-column checkout with pre-filled customer details and live order summary.
   - Multiple payment methods: **Cash on Delivery (COD)** and **Simulated Online Payment / UPI / Card**.
   - **Database Transactions (`transaction.atomic()` & `select_for_update()`)**:
     - Strict server-side price recalculation (browser-submitted prices are never trusted).
     - Live stock re-verification before order placement.
     - Safe inventory deduction and cart clearance upon order completion.
     - Generation of distinctive order references (e.g., `SE-20261026-XXXXXX`).

6. **Order Confirmation & Order History**
   - Dedicated confirmation page with itemized breakdown, tax & delivery receipts, and reference tracking.
   - "My Orders" customer portal to track past orders with color-coded status badges (*Pending*, *Processing*, *Shipped*, *Delivered*, *Cancelled*).
   - Strict ownership isolation (users can only access their own orders).

7. **ShopEase Administration Panel**
   - Custom branded Django Admin (`ShopEase Administration`).
   - Manage categories, products, inventory counts, and upload images.
   - Visual stock warnings (Green for In-Stock, Amber for Low Stock, Red for Out-of-Stock).
   - Manage customer orders, inspect itemized order contents, and update order/payment statuses.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.12+, Django 6.1+
- **Database**: SQLite3 with Django ORM
- **Frontend**: Semantic HTML5, Vanilla CSS3 (Custom Design System, Google Fonts *Plus Jakarta Sans* & *Inter*), Modern JavaScript (ES6+)
- **Image Processing**: Pillow
- **Testing**: Django Test Suite & End-to-End Verification Harness

---

## 📁 Project Structure

```text
task 1/
│
├── manage.py                          # Django management CLI
├── requirements.txt                   # Project Python dependencies
├── README.md                          # Comprehensive project documentation
├── verify_e2e.py                      # Automated E2E verification test script
│
├── shopease/                          # Django Project Configuration
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py                    # Configured apps, media, static, and templates
│   ├── urls.py                        # Root URL router with admin customization
│   └── wsgi.py
│
├── store/                             # Main ShopEase Application
│   ├── __init__.py
│   ├── admin.py                       # Custom admin with badges & inlines
│   ├── apps.py
│   ├── context_processors.py          # Global cart count & category nav context
│   ├── forms.py                       # Registration, Login, and Checkout forms
│   ├── models.py                      # Category, Product, CartItem, Order, OrderItem
│   ├── tests.py                       # Unit & integration test cases
│   ├── urls.py                        # App route definitions
│   ├── views.py                       # Storefront, cart, checkout, and auth views
│   │
│   └── management/
│       └── commands/
│           ├── __init__.py
│           └── seed_products.py       # Seeds 16 products & default admin account
│
├── templates/                         # HTML5 Django Templates
│   ├── base.html                      # Master layout, navigation, alerts, & footer
│   ├── home.html                      # Homepage with hero, categories, & featured items
│   ├── product_list.html              # Search, filter, and sortable catalog
│   ├── product_detail.html            # Detail page with quantity selector
│   ├── cart.html                      # Shopping cart with subtotals & quantity editing
│   ├── checkout.html                  # Address form & payment options
│   ├── order_confirmation.html        # Order receipt & confirmation
│   ├── my_orders.html                 # Customer order history
│   ├── order_detail.html              # Detailed past order receipt
│   ├── login.html                     # Customer sign-in page
│   └── register.html                  # Customer registration page
│
├── static/                            # Static Assets
│   ├── css/
│   │   └── style.css                  # Modern design system & responsive styles
│   ├── js/
│   │   └── script.js                  # Quantity controls, alerts, and AJAX cart helpers
│   └── images/
│       ├── logo.svg                   # Brand vector logo
│       └── placeholder.svg            # Fallback product graphic
│
└── media/                             # Uploaded media directory
    └── products/                      # Product images
```

---

## 🚀 Quickstart & Installation (Windows)

Follow these steps in PowerShell or Command Prompt to set up and run ShopEase locally:

### 1. Create and Activate Virtual Environment
```powershell
python -m venv venv
venv\Scripts\activate
```

### 2. Install Project Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Generate and Apply Database Migrations
```powershell
python manage.py makemigrations
python manage.py migrate
```

### 4. Populate Database with Sample Products
Run the custom seeding command to populate categories, 16 sample products, and the initial administrator account:
```powershell
python manage.py seed_products
```

### 5. Create Superuser (Optional)
If you wish to create a custom administrator account:
```powershell
python manage.py createsuperuser
```
*(Note: `python manage.py seed_products` already creates a default admin: Username `admin`, Password `admin123`)*

### 6. Run the Test Suite
```powershell
python manage.py test store
python verify_e2e.py
```

### 7. Start the Development Server
```powershell
python manage.py runserver
```

---

## 🌐 URLs & Credentials

| Service | URL | Credentials |
| :--- | :--- | :--- |
| **ShopEase Storefront** | [http://127.0.0.1:8000/](http://127.0.0.1:8000/) | Public / Register your own account |
| **Admin Control Panel** | [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/) | **Username**: `admin`<br>**Password**: `admin123` |
| **All Products Catalog** | [http://127.0.0.1:8000/products/](http://127.0.0.1:8000/products/) | Public |
| **Shopping Cart** | [http://127.0.0.1:8000/cart/](http://127.0.0.1:8000/cart/) | Public / Session & DB backed |
| **My Orders** | [http://127.0.0.1:8000/orders/](http://127.0.0.1:8000/orders/) | Requires Customer Login |

---

## 🔒 Security Best Practices Implemented

- **Password Hashing**: Industry-standard PBKDF2 algorithm via Django's auth system.
- **CSRF Protection**: Tokens enforced on all `POST` forms.
- **Transactional Safety**: Atomic database transactions (`transaction.atomic()`) prevent inventory discrepancies or partial order creation.
- **Zero Client Trust**: All product prices, cart subtotals, and stock deductions are recomputed and enforced on the server.
- **Access Control**: Strict permission separation between regular customers and staff in the admin panel.
