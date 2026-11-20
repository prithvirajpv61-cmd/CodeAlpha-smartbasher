from .models import Category, CartItem


def cart_and_categories_processor(request):
    """
    Context processor that supplies global navigation data:
    - cart_count: Total item count in cart
    - categories_nav: List of all product categories
    - site_currency: '₹'
    """
    cart_count = 0

    try:
        if request.user.is_authenticated:
            items = CartItem.objects.filter(user=request.user)
            cart_count = sum(item.quantity for item in items)
        else:
            session_key = request.session.session_key
            if session_key:
                items = CartItem.objects.filter(session_key=session_key)
                cart_count = sum(item.quantity for item in items)
    except Exception:
        cart_count = 0

    try:
        categories_nav = Category.objects.all()
    except Exception:
        categories_nav = []

    return {
        'cart_count': cart_count,
        'categories_nav': categories_nav,
        'currency_symbol': '₹',
        'site_name': 'ShopEase',
    }
