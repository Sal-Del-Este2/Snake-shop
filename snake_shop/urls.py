# snake_shop/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # URLs de la Tienda
    path('tienda/', views.lista_productos, name='lista_productos'),
    path('tienda/categorias/<slug:categoria_slug>/', views.lista_productos, name='lista_productos_por_categoria'),
    path('tienda/productos/<slug:product_slug>/', views.detalle_producto, name='detalle_producto'),

    # URLs de Autenticación y Perfil
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('mis-pedidos/', views.mis_pedidos_view, name='mis_pedidos'),
    path('mis-pedidos/<int:pedido_id>/', views.detalle_pedido_view, name='detalle_pedido'), 
    path('mis-pedidos/<int:pedido_id>/eliminar/', views.eliminar_pedido, name='eliminar_pedido'),
    
    # URL DE SERVICIO TÉCNICO (Módulo Institucional)
    path('soporte-tecnico/', views.contacto_tecnico_view, name='contacto_tecnico'),

    # URLs del Vendedor (Gestión Administrativa)
    path('crear-producto/', views.crear_producto, name='crear_producto'), # Asegúrate que esta línea exista
    path('gestion-pedidos/', views.gestion_pedidos, name='gestion_pedidos'),
    path('gestion-pedidos/<int:pedido_id>/actualizar/', views.actualizar_estado_vendedor, name='actualizar_estado_vendedor'),
    path('gestion-tickets/', views.gestion_tickets, name='gestion_tickets'),
    path('gestion-tickets/<int:ticket_id>/actualizar/', views.actualizar_ticket, name='actualizar_ticket'),
    path('estadisticas/', views.estadisticas_vendedor, name='estadisticas_vendedor'),
        
    # URLs de Carrito y Checkout
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:producto_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:producto_id>/', views.cart_remove, name='cart_remove'),
    path('checkout/', views.checkout, name='checkout'),
    path('crear_pedido/', views.crear_pedido, name='crear_pedido'),

    # --- FLUJO DE PAGO FLOW (Sincronizado con views.py) ---
    # Esta es la URL de retorno para el cliente (RF-09)
    path('order-complete/<int:pedido_id>/', views.order_complete, name='order_complete'),
    path('pago/fallido/', views.pago_fallido, name='pago_fallido'),
    # URL crítica para el Webhook de confirmación automática (RF-07)
    path('pago/confirmacion/', views.confirmacion_flow, name='confirmacion_flow'),

    # URL de la página de inicio
    path('', views.home, name='home'),
    path("seleccionar-envio/", views.seleccionar_envio, name="seleccionar_envio"),
]
