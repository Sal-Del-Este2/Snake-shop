def cart_counter(request):
    cart = request.session.get('cart', {})
    total_items = sum(item['cantidad'] for item in cart.values())
    return {
        'cart_count': total_items
    }