from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from store.models import Category, Product


class Command(BaseCommand):
    help = "Populate the database with sample categories, products, and a default admin user."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding ShopEase database with sample data..."))

        # 1. Create or get Default Superuser
        admin_user, created_admin = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@shopease.local',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created_admin:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created superuser 'admin' with password 'admin123'"))
        else:
            self.stdout.write(self.style.WARNING("Superuser 'admin' already exists."))

        # 2. Categories
        categories_data = [
            {
                'name': 'Electronics',
                'description': 'Latest gadgets, audio gear, smart wearables, and computer peripherals.',
                'icon': 'cpu'
            },
            {
                'name': 'Clothing',
                'description': 'Contemporary fashion, casual wear, jackets, and wardrobe essentials.',
                'icon': 'shirt'
            },
            {
                'name': 'Accessories',
                'description': 'Premium watches, sunglasses, leather wallets, and travel gear.',
                'icon': 'watch'
            },
            {
                'name': 'Home Appliances',
                'description': 'Modern kitchen tech, air purifiers, espresso makers, and home essentials.',
                'icon': 'home'
            },
        ]

        categories_map = {}
        for cat_info in categories_data:
            cat, created = Category.objects.get_or_create(
                name=cat_info['name'],
                defaults={
                    'description': cat_info['description'],
                    'icon': cat_info['icon']
                }
            )
            categories_map[cat.name] = cat
            status = "Created" if created else "Found"
            self.stdout.write(f"  [{status}] Category: {cat.name}")

        # 3. Sample Products (at least 4 in each of 4 categories = 16 products)
        products_data = [
            # Electronics
            {
                'category': 'Electronics',
                'name': 'AeroSound Pro Wireless ANC Headphones',
                'description': 'Experience studio-grade acoustics with advanced Active Noise Cancellation, 40-hour continuous playback battery, ultra-plush memory foam earcups, and dual beamforming crystal microphones for flawless calls.',
                'price': Decimal('4999.00'),
                'stock': 25,
                'is_featured': True,
                'image_url': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&auto=format&fit=crop&q=80',
            },
            {
                'category': 'Electronics',
                'name': 'PulseFit Ultra Smart Watch',
                'description': '1.8-inch Vivid AMOLED Display with always-on technology. Features 24/7 heart-rate monitor, SpO2 blood oxygen sensor, GPS route tracking, sleep staging, and 5 ATM water resistance for swimming.',
                'price': Decimal('3299.00'),
                'stock': 18,
                'is_featured': True,
                'image_url': 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800&auto=format&fit=crop&q=80',
            },
            {
                'category': 'Electronics',
                'name': 'NovaStrike RGB Mechanical Keyboard',
                'description': 'Custom hot-swappable tactile switches with aircraft-grade aluminum top plate. Includes dynamic per-key RGB backlighting, detachable braided Type-C cable, and sound-dampening acoustic silicone padding.',
                'price': Decimal('2799.00'),
                'stock': 12,
                'is_featured': False,
                'image_url': 'https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=800&auto=format&fit=crop&q=80',
            },
            {
                'category': 'Electronics',
                'name': 'HyperView 4K Action Camera',
                'description': 'Ultra HD 4K at 60FPS recording with 6-axis gyro image stabilization. Includes 30m waterproof casing, dual color touchscreens, voice control, and ultra-wide 170-degree distortion-corrected lens.',
                'price': Decimal('6499.00'),
                'stock': 8,
                'is_featured': True,
                'image_url': 'https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=800&auto=format&fit=crop&q=80',
            },

            # Clothing
            {
                'category': 'Clothing',
                'name': 'Artisan Washed Vintage Denim Jacket',
                'description': 'Crafted from 100% heavy-weight sustainable denim with antique brass buttons, comfortable relaxed fit, dual chest flap pockets, and deep interior phone stash compartments.',
                'price': Decimal('2499.00'),
                'stock': 30,
                'is_featured': True,
                'image_url': 'https://images.unsplash.com/photo-1576995853123-5a10305d93c0?w=800&auto=format&fit=crop&q=80',
            },
            {
                'category': 'Clothing',
                'name': 'BreezeKnit Premium Linen Casual Shirt',
                'description': 'Breathable pure organic linen woven with ultra-fine cotton fibers for all-day lightness. Features a tailored modern cut, mandarin collar, and mother-of-pearl buttons.',
                'price': Decimal('1499.00'),
                'stock': 40,
                'is_featured': True,
                'image_url': 'https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=800&auto=format&fit=crop&q=80',
            },
            {
                'category': 'Clothing',
                'name': 'UrbanTech Heavyweight Fleece Hoodie',
                'description': '450 GSM ultra-soft brushed fleece with double-lined kangaroo pocket, reinforced ribbed cuffs, drop-shoulder contemporary silhouette, and anti-shrink fabric treatment.',
                'price': Decimal('1899.00'),
                'stock': 22,
                'is_featured': False,
                'image_url': 'https://images.unsplash.com/photo-1556905055-8f358a7a47b2?w=800&auto=format&fit=crop&q=80',
            },
            {
                'category': 'Clothing',
                'name': 'Stretch Flex Everyday Chino Trousers',
                'description': '98% Cotton with 2% elastane for unrestricted mobility. Tailored slim-straight fit, wrinkle-resistant finish, reinforced waistband, and secure zippered coin pocket.',
                'price': Decimal('1699.00'),
                'stock': 15,
                'is_featured': False,
                'image_url': 'https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=800&auto=format&fit=crop&q=80',
            },

            # Accessories
            {
                'category': 'Accessories',
                'name': 'Heritage Full-Grain Leather Bi-Fold Wallet',
                'description': 'Handcrafted from authentic vegetable-tanned Italian leather that patinas beautifully over time. Built-in RFID shielding protects contactless cards from unauthorized scans.',
                'price': Decimal('999.00'),
                'stock': 35,
                'is_featured': True,
                'image_url': 'https://images.unsplash.com/photo-1627123424574-724758594e93?w=800&auto=format&fit=crop&q=80',
            },
            {
                'category': 'Accessories',
                'name': 'Solaris Aviator Polarized Sunglasses',
                'description': 'Ultra-lightweight aerospace titanium alloy frames with UV400 polarized scratch-resistant gradient lenses. Delivers maximum glare reduction and 100% UVA/UVB protection.',
                'price': Decimal('1799.00'),
                'stock': 14,
                'is_featured': False,
                'image_url': 'https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=800&auto=format&fit=crop&q=80',
            },
            {
                'category': 'Accessories',
                'name': 'Voyager All-Weather Commuter Backpack 28L',
                'description': 'Waterproof ballistic nylon shell, dedicated padded 16-inch laptop chamber with air-mesh ventilation back panel, luggage pass-through strap, and hidden anti-theft pocket.',
                'price': Decimal('2999.00'),
                'stock': 20,
                'is_featured': True,
                'image_url': 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=800&auto=format&fit=crop&q=80',
            },
            {
                'category': 'Accessories',
                'name': 'Chronos Sapphire Stainless Steel Watch',
                'description': 'Precision Japanese Quartz chronograph movement housed in 316L surgical-grade stainless steel with scratch-proof sapphire crystal glass and luminous dial hands.',
                'price': Decimal('4499.00'),
                'stock': 9,
                'is_featured': True,
                'image_url': 'https://images.unsplash.com/photo-1524592094714-0f0654e20314?w=800&auto=format&fit=crop&q=80',
            },

            # Home Appliances
            {
                'category': 'Home Appliances',
                'name': 'AeroChef Digital Air Fryer 5.5L',
                'description': '360-degree rapid vortex heat circulation fries food with up to 85% less oil. Includes 8 intelligent one-touch presets, non-stick dishwasher-safe ceramic basket, and auto shut-off safety.',
                'price': Decimal('3899.00'),
                'stock': 16,
                'is_featured': True,
                'image_url': 'https://images.unsplash.com/photo-1585659722983-3a675dabf23d?w=800&auto=format&fit=crop&q=80',
            },
            {
                'category': 'Home Appliances',
                'name': 'BaristaCraft 20-Bar Espresso Machine',
                'description': 'Professional 20-bar Italian high-pressure pump system extracts rich crema every single time. Equipped with commercial stainless steel steam wand for velvety microfoam lattes and cappuccinos.',
                'price': Decimal('8999.00'),
                'stock': 6,
                'is_featured': True,
                'image_url': 'https://images.unsplash.com/photo-1517668808822-9ebb02ae2a0e?w=800&auto=format&fit=crop&q=80',
            },
            {
                'category': 'Home Appliances',
                'name': 'RoboClean Smart Robot Vacuum & Mop',
                'description': 'LiDAR laser navigation precisely maps multiple floors in real time. 4000Pa extreme suction power with automated water pump mopping, cliff sensors, and voice assistant integration.',
                'price': Decimal('14999.00'),
                'stock': 4,
                'is_featured': False,
                'image_url': 'https://images.unsplash.com/photo-1563178406-4cdc2923acbc?w=800&auto=format&fit=crop&q=80',
            },
            {
                'category': 'Home Appliances',
                'name': 'NutriPulse 1200W High-Speed Nutrient Blender',
                'description': 'Heavy-duty 1200W motor with hardened stainless steel 6-point extraction blades that pulverize frozen fruits, greens, and nuts in seconds. Includes 2 BPA-free travel cups with flip-top lids.',
                'price': Decimal('2599.00'),
                'stock': 19,
                'is_featured': False,
                'image_url': 'https://images.unsplash.com/photo-1570222094114-d054a817e56b?w=800&auto=format&fit=crop&q=80',
            },
        ]

        created_count = 0
        updated_count = 0

        for item in products_data:
            cat = categories_map[item['category']]
            prod, created = Product.objects.update_or_create(
                name=item['name'],
                defaults={
                    'category': cat,
                    'description': item['description'],
                    'price': item['price'],
                    'stock': item['stock'],
                    'is_featured': item['is_featured'],
                    'is_available': True,
                    'image_url': item['image_url'],
                }
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully seeded database: {created_count} products created, {updated_count} updated across 4 categories."
            )
        )
