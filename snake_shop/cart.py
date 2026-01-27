# snake_shop/cart.py
from decimal import Decimal
from django.conf import settings
from .models import Producto

class Cart:
    def __init__(self, request):

        # Inicializa el carrito.
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            # guarda un carrito vacío en la sesión
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, producto, cantidad=1, override_cantidad=False):

        # Agrega un producto al carrito o actualiza su cantidad.
        producto_id = str(producto.id)
        
        if producto_id not in self.cart:
            self.cart[producto_id] = {
                'cantidad': 0,
                # Convertimos el Decimal a string aquí
                'precio': str(producto.precio)
            }
        
        # Obtenemos la cantidad actual, asegurando que sea un número (o 0 si es None)
        current_cantidad = self.cart[producto_id].get('cantidad')
        if current_cantidad is None:
            current_cantidad = 0

        if override_cantidad:
            self.cart[producto_id]['cantidad'] = cantidad
        else:
            self.cart[producto_id]['cantidad'] = current_cantidad + cantidad

        self.save()

    def save(self):
        # marca la sesión como "modificada" para asegurar que se guarde
        self.session.modified = True

    def remove(self, producto):

        # Elimina un producto del carrito.
        producto_id = str(producto.id)
        if producto_id in self.cart:
            del self.cart[producto_id]
            self.save()

    def __iter__(self):

        # Itera sobre los items del carrito y obtiene los productos de la base de datos.
        producto_ids = self.cart.keys()
        productos = Producto.objects.filter(id__in=producto_ids)
        cart = self.cart.copy()
        for producto in productos:
            cart[str(producto.id)]['producto'] = producto

        for item in cart.values():
            # Convertimos el string de vuelta a Decimal para los cálculos
            precio = (
                producto.precio_promocion
                if producto.en_promocion and producto.precio_promocion
                else producto.precio
            )
            item['precio'] = precio
            item['total_precio'] = precio * item['cantidad']

            yield item
            
            # Precio promocional si aplica
            precio = producto.precio_promocion if producto.en_promocion and producto.precio_promocion else producto.precio
            item['precio'] = precio
            item['total_precio'] = precio * item['cantidad']
            # yield item

    def __len__(self):

        # Cuenta todos los items en el carrito.
        return sum(item['cantidad'] for item in self.cart.values())

    def get_total_precio(self):
        total = Decimal('0')
        for item in self:
            # Usa precio_promocion si está en promoción
            precio = (
                item['producto'].precio_promocion
                if item['producto'].en_promocion and item['producto'].precio_promocion
                else item['producto'].precio
            )
            total += precio * item['cantidad']
        return total

    
    def get_costo_envio(request):
        return 3990 if request.session.get("tipo_envio") == "despacho" else 0

    def clear(self):
        # elimina el carrito de la sesión
        del self.session[settings.CART_SESSION_ID]
        self.save()
