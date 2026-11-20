from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, CartItem, Order, OrderItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'product_count', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = "Products"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'category',
        'price_display',
        'stock_display',
        'is_available',
        'is_featured',
        'image_preview',
        'updated_at'
    )
    list_filter = ('category', 'is_available', 'is_featured', 'created_at')
    search_fields = ('name', 'description', 'category__name')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_available', 'is_featured')
    readonly_fields = ('created_at', 'updated_at', 'image_preview_large')
    fieldsets = (
        ('Basic Information', {
            'fields': ('category', 'name', 'slug', 'description')
        }),
        ('Pricing & Inventory', {
            'fields': ('price', 'stock', 'is_available', 'is_featured')
        }),
        ('Media', {
            'fields': ('image', 'image_url', 'image_preview_large')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def price_display(self, obj):
        return f"₹{obj.price:,.2f}"
    price_display.short_description = "Price"

    def stock_display(self, obj):
        if obj.stock == 0:
            return format_html('<span style="color: #ef4444; font-weight: bold;">Out of Stock (0)</span>')
        elif obj.stock < 5:
            return format_html('<span style="color: #f59e0b; font-weight: bold;">Low Stock ({})</span>', obj.stock)
        return format_html('<span style="color: #10b981; font-weight: bold;">{} in stock</span>', obj.stock)
    stock_display.short_description = "Stock"

    def image_preview(self, obj):
        img_url = obj.get_display_image()
        return format_html('<img src="{}" style="width: 45px; height: 45px; object-fit: cover; border-radius: 6px;" />', img_url)
    image_preview.short_description = "Preview"

    def image_preview_large(self, obj):
        img_url = obj.get_display_image()
        return format_html('<img src="{}" style="max-width: 250px; max-height: 250px; border-radius: 8px;" />', img_url)
    image_preview_large.short_description = "Image Preview"


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_name', 'price', 'quantity', 'subtotal_display')
    can_delete = False

    def subtotal_display(self, obj):
        return f"₹{obj.subtotal:,.2f}"
    subtotal_display.short_description = "Subtotal"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_reference',
        'user',
        'full_name',
        'total_display',
        'payment_method_badge',
        'payment_status_badge',
        'order_status_badge',
        'created_at'
    )
    list_filter = ('order_status', 'payment_status', 'payment_method', 'created_at')
    search_fields = ('order_reference', 'user__username', 'full_name', 'email', 'phone')
    readonly_fields = ('order_reference', 'user', 'total_amount', 'created_at', 'updated_at')
    inlines = [OrderItemInline]
    fieldsets = (
        ('Order Identification', {
            'fields': ('order_reference', 'user', 'created_at', 'updated_at')
        }),
        ('Customer & Delivery Details', {
            'fields': ('full_name', 'email', 'phone', 'address', 'city', 'state', 'postal_code', 'notes')
        }),
        ('Financial & Payment', {
            'fields': ('total_amount', 'payment_method', 'payment_status')
        }),
        ('Fulfillment', {
            'fields': ('order_status', 'tracking_number')
        }),
    )

    def total_display(self, obj):
        return format_html('<strong>₹{}</strong>', f"{obj.total_amount:,.2f}")
    total_display.short_description = "Total"

    def payment_method_badge(self, obj):
        method = dict(Order.PAYMENT_CHOICES).get(obj.payment_method, obj.payment_method)
        return format_html('<span style="background: #e0e7ff; color: #3730a3; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">{}</span>', method)
    payment_method_badge.short_description = "Payment Method"

    def payment_status_badge(self, obj):
        colors = {
            'Completed': ('#dcfce7', '#166534'),
            'Pending': ('#fef9c3', '#854d0e'),
            'Failed': ('#fee2e2', '#991b1b'),
        }
        bg, fg = colors.get(obj.payment_status, ('#f3f4f6', '#374151'))
        return format_html('<span style="background: {}; color: {}; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">{}</span>', bg, fg, obj.payment_status)
    payment_status_badge.short_description = "Payment Status"

    def order_status_badge(self, obj):
        colors = {
            'Pending': ('#fef9c3', '#854d0e'),
            'Processing': ('#e0f2fe', '#0369a1'),
            'Shipped': ('#ede9fe', '#5b21b6'),
            'Delivered': ('#dcfce7', '#166534'),
            'Cancelled': ('#fee2e2', '#991b1b'),
        }
        bg, fg = colors.get(obj.order_status, ('#f3f4f6', '#374151'))
        return format_html('<span style="background: {}; color: {}; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">{}</span>', bg, fg, obj.order_status)
    order_status_badge.short_description = "Order Status"


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_or_session', 'product', 'quantity', 'subtotal_display', 'updated_at')
    list_filter = ('updated_at',)
    search_fields = ('user__username', 'product__name', 'session_key')

    def user_or_session(self, obj):
        return obj.user.username if obj.user else f"Guest ({obj.session_key[:8]}...)"
    user_or_session.short_description = "Cart Owner"

    def subtotal_display(self, obj):
        return f"₹{obj.subtotal:,.2f}"
    subtotal_display.short_description = "Subtotal"
