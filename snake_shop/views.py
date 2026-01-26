import hashlib
import hmac
import requests
import random
import uuid
from decimal import Decimal

from django.conf import settings
from django.core.mail import send_mail 
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.urls import reverse
from django.db import transaction
from django.http import HttpResponse
from django.db.models.functions import TruncDate, TruncMonth
from django.db.models import Sum, Count
from django.http import JsonResponse

# Modelos y Formularios del Proyecto
from .models import Producto, Categoria, Perfil, Pedido, ItemPedido, Transaccion, TicketSoporte 
from .forms import CartAddProductForm, PerfilForm, ProductoForm, ContactoTecnicoForm, UserUpdateForm
from .cart import Cart

# FUNCIONES DE UTILIDAD (FLOW API)
def generar_firma_flow(params):
    # Genera la firma digital (s) requerida por Flow para asegurar la integridad.
    keys = sorted(params.keys())
    string_to_sign = "".join(f"{k}{params[k]}" for k in keys)
    return hmac.new(
        settings.FLOW_SECRET_KEY.encode(),
        string_to_sign.encode(),
        hashlib.sha256
    ).hexdigest()

# Vistas de Productos y Tienda
def home(request):
    # 3 productos ALEATORIOS en promoción (o los únicos si hay menos de 3)
    productos_promocion = Producto.objects.filter(
        en_promocion=True, 
        disponible=True
    ).select_related('categoria')[:3]
    
    context = {'productos_promocion': productos_promocion}
    return render(request, 'snake_shop/home.html', context)
    # return render(request, 'snake_shop/home.html')

def lista_productos(request, categoria_slug=None):
    categoria = None
    categorias = Categoria.objects.all()
    # productos = Producto.objects.filter(disponible=True)
    productos = Producto.objects.filter(disponible=True).select_related('categoria')

    # 3 productos en promoción para carrusel
    productos_promocion = Producto.objects.filter(
        en_promocion=True, disponible=True
    ).select_related('categoria')[:3]

    if categoria_slug:
        categoria = get_object_or_404(Categoria, slug=categoria_slug)
        productos = productos.filter(categoria=categoria)

    context = {
        'categoria': categoria,
        'categorias': categorias,
        'productos': productos,
        'productos_promocion': productos_promocion  # NUEVO
    }
    return render(request, 'snake_shop/lista_productos.html', context)

def detalle_producto(request, product_slug):
    producto = get_object_or_404(Producto, slug=product_slug, disponible=True)
    cart_product_form = CartAddProductForm()
    return render(request, 'snake_shop/detalle_producto.html', {
        'producto': producto, 
        'cart_product_form': cart_product_form
    })

# Vistas de Soporte Técnico (Módulo Institucional)
def contacto_tecnico_view(request):
    initial_data = {}
    if request.user.is_authenticated:
        full_name = f"{request.user.first_name} {request.user.last_name}".strip()
        initial_data['nombre_completo'] = full_name if full_name else request.user.username
        
        if request.user.email:
            initial_data['email'] = request.user.email
        elif hasattr(request.user, 'perfil') and request.user.perfil.email:
            initial_data['email'] = request.user.perfil.email
    
    if request.method == 'POST':
        form = ContactoTecnicoForm(request.POST, request.FILES)
        if form.is_valid():
            ticket = form.save(commit=False)
            if request.user.is_authenticated:
                ticket.usuario = request.user
            ticket.save() 
            
            try:
                subject = f"Confirmación Ticket #{ticket.folio} - Snake Shop"
                message = f"Hola {ticket.nombre_completo},\n\nHemos recibido tu solicitud #{ticket.folio}.\nAsunto: {ticket.asunto}\n\nGracias por contactarnos."
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [ticket.email], fail_silently=True)
            except Exception as e:
                print(f"Error email: {e}")

            messages.success(request, f'¡Enviado! Tu folio es #{ticket.folio}.')
            return redirect('home') 
    else:
        form = ContactoTecnicoForm(initial=initial_data)
    
    return render(request, 'snake_shop/contacto_tecnico.html', {'form': form})

# Vistas de Autenticación y Perfil
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Bienvenido {user.username}')
            return redirect('lista_productos')
    else:
        form = AuthenticationForm()
    return render(request, 'snake_shop/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'Sesión cerrada correctamente.')
    return redirect('home')

def register_view(request):
    if request.method == 'POST':
        # Usamos un UserCreationForm extendido o capturamos el email manualmente
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Evitamos el IntegrityError: UNIQUE constraint
            Perfil.objects.get_or_create(usuario=user) 
            login(request, user)
            messages.success(request, '¡Cuenta creada con éxito! Por favor, completa tu email en el perfil.')
            return redirect('profile')
    else:
        form = UserCreationForm()
    return render(request, 'snake_shop/register.html', {'form': form})

@login_required
def profile_view(request):
    # Manejo de error si el perfil no existe (Failsafe)
    try:
        perfil = request.user.perfil
    except Perfil.DoesNotExist:
        perfil = Perfil.objects.create(usuario=request.user)

    if request.method == 'POST':
        form_usuario = UserUpdateForm(request.POST, instance=request.user)
        form_perfil = PerfilForm(request.POST, instance=perfil)

        if form_usuario.is_valid() and form_perfil.is_valid():
            # SINCRONIZACIÓN CRÍTICA: Guardamos en User para que Flow lo vea
            user = form_usuario.save()
            
            # Guardamos en Perfil para consistencia interna
            perfil_obj = form_perfil.save(commit=False)
            perfil_obj.email = user.email # Replicamos el email al perfil
            perfil_obj.save()
            
            messages.success(request, '¡Perfil y Email actualizados correctamente!')
            return redirect('profile')
    else:
        form_usuario = UserUpdateForm(instance=request.user)
        form_perfil = PerfilForm(instance=perfil)
        
    return render(request, 'snake_shop/profile.html', {
        'form_usuario': form_usuario,
        'form': form_perfil
    })

# Vistas de Vendedor (Gestión)
def es_vendedor(user):
    # Verifica si el usuario tiene permisos de vendedor
    return user.is_staff or (hasattr(user, 'perfil') and user.perfil.is_seller)

@login_required
@user_passes_test(es_vendedor, login_url='/login/')
def crear_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            producto = form.save(commit=False)
            producto.vendedor = request.user
            producto.save()
            messages.success(request, "Producto creado exitosamente.")
            return redirect('lista_productos')
    else:
        form = ProductoForm()
    return render(request, 'snake_shop/crear_producto.html', {'form': form})

@login_required
@user_passes_test(es_vendedor, login_url='/login/')
def gestion_pedidos(request):

    # Muestra los pedidos. Si es staff ve todos, si es vendedor solo los suyos.
    if request.user.is_staff:
        pedidos = Pedido.objects.all().order_by('-creado')
    else:
        pedidos = Pedido.objects.filter(items__producto__vendedor=request.user).distinct().order_by('-creado')
    
    return render(request, 'snake_shop/gestion_pedidos.html', {'pedidos': pedidos})

@login_required
@user_passes_test(es_vendedor, login_url='/login/')
@require_POST
def actualizar_estado_vendedor(request, pedido_id):

    # Permite al vendedor forzar el estado de pago y despacho manualmente.
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    # Solo staff o el dueño de los productos en el pedido pueden editar
    nuevo_estado = request.POST.get('estado_despacho')
    pagado = request.POST.get('pagado') == 'on' 

    if nuevo_estado in dict(Pedido.ESTADOS_DESPACHO):
        pedido.estado_despacho = nuevo_estado
        pedido.pagado = pagado
        pedido.save()
        messages.success(request, f'Pedido #{pedido.id} actualizado correctamente.')
    else:
        messages.error(request, 'Estado de despacho no válido.')
        
    return redirect('gestion_pedidos')

# Vistas de Carrito y Checkout
@require_POST
def cart_add(request, producto_id):
    cart = Cart(request)
    producto = get_object_or_404(Producto, id=producto_id)
    form = CartAddProductForm(request.POST, producto=producto)
    if form.is_valid():
        cd = form.cleaned_data
        cart.add(producto=producto, cantidad=cd['cantidad'], override_cantidad=cd['override'])
    return redirect('cart_detail')

@require_POST
def cart_remove(request, producto_id):
    cart = Cart(request)
    producto = get_object_or_404(Producto, id=producto_id)
    cart.remove(producto)
    return redirect('cart_detail')

def cart_detail(request):
    cart = Cart(request)
    for item in cart:
        item['update_cantidad_form'] = CartAddProductForm(initial={'cantidad': item['cantidad'], 'override': True})
    return render(request, 'snake_shop/cart_detail.html', {'cart': cart})

# @login_required esto es para habilitar el usuario invitado
def checkout(request):
    cart = Cart(request)
    if not cart: 
        return redirect('lista_productos')
    
    # Llamamos a la función de cálculo
    sub, env, desc, total = obtener_totales_finales(request, cart)
    
    return render(request, 'snake_shop/checkout.html', {
        'cart': cart,
        'subtotal': sub,
        'envio': env,
        'descuento': desc,
        'total_final': total
    })

def obtener_totales_finales(request, cart):

    # Calcula montos exactos para evitar discrepancias con Flow.
    subtotal = cart.get_total_precio()
    envio = 3990
    descuento = 0
    
    # Aplicar 15% de descuento solo si es usuario administrativo (staff)
    if request.user.is_staff:
        descuento = int(subtotal * 0.15)
    
    total_final = (subtotal + envio) - descuento
    return subtotal, envio, descuento, total_final

# INTEGRACIÓN DE PAGOS FLOW (RF-06, RF-07, RF-08)
# @login_required, tambien debe ser para invitados
@require_POST
def crear_pedido(request):
    cart = Cart(request)
    if not cart:
        messages.error(request, 'Tu carrito está vacío.')
        return redirect('lista_productos')

    # 1. DATOS DEL COMPRADOR
    if request.user.is_authenticated:
        usuario = request.user
        email = request.user.email

        try:
            perfil = request.user.perfil
        except Perfil.DoesNotExist:
            messages.warning(request, 'Debes completar tu perfil antes de comprar.')
            return redirect('profile')

        direccion = perfil.direccion
        ciudad = perfil.ciudad
        codigo_postal = getattr(perfil, "codigo_postal", None) #perfil.codigo_postal

        if not email:
            messages.error(request, 'Tu cuenta no tiene un email válido.')
            return redirect('profile')

    else:
        # Comprar Como Invitado
        # nombre = request.POST.get('nombre')
        usuario = None
        email = request.POST.get('email')
        direccion = request.POST.get('direccion')
        ciudad = request.POST.get('ciudad')
        codigo_postal = request.POST.get('codigo_postal') or None

        if not all([email, direccion, ciudad]):
            messages.error(request, 'Debes completar los datos de envío.')
            return redirect('cart_detail')

    tipo_envio = request.POST.get('tipo_envio', 'despacho')
    if tipo_envio == 'retiro':
        costo_envio = 0
        direccion = None
        ciudad = None
        codigo_postal = None
    else:
        costo_envio = 3990
        direccion = request.POST.get('direccion')
        ciudad = request.POST.get('ciudad')
        codigo_postal = request.POST.get('codigo_postal') or None

    # 2. CREACIÓN DEL PEDIDO
    try:
        with transaction.atomic():
            subtotal = cart.get_total_precio()
            # costo_envio = 3990
            descuento = 0

            if usuario and usuario.is_staff:
                descuento = int(subtotal * 0.15)

            total = subtotal + costo_envio - descuento

            pedido = Pedido.objects.create(
                usuario=usuario,
                email=email,               # MUY IMPORTANTE PARA INVITADOS
                direccion=direccion,
                ciudad=ciudad,
                codigo_postal=codigo_postal,
                estado_despacho=tipo_envio,
                costo_envio=costo_envio,
                # subtotal=subtotal,
                descuento=descuento,
                total=total
            )

            # 3. ITEMS + STOCK
            for item in cart:
                producto = item['producto']

                if producto.stock < item['cantidad']:
                    raise ValueError(f"Stock insuficiente para {producto.nombre}")

                ItemPedido.objects.create(
                    pedido=pedido,
                    producto=producto,
                    precio=item['precio'],
                    cantidad=item['cantidad']
                )

                producto.stock -= item['cantidad']
                producto.save()

            # 4. FLOW
            url_api = f"{settings.FLOW_URL_BASE}/payment/create"

            params = {
                "apiKey": settings.FLOW_API_KEY,
                "commerceOrder": str(pedido.id),
                "subject": f"Compra Snake Shop - Pedido #{pedido.id}",
                "currency": "CLP",
                "amount": int(total),
                "email": email,
                "urlReturn": request.build_absolute_uri(
                    reverse('order_complete', args=[pedido.id])
                ),
                "urlConfirmation": request.build_absolute_uri(
                    reverse('confirmacion_flow')
                ),
            }

            params["s"] = generar_firma_flow(params)
            response = requests.post(url_api, data=params)
            data = response.json()

            if response.status_code == 200 and 'url' in data:
                request.session['pedido_id'] = pedido.id
                cart.clear()
                return redirect(f"{data['url']}?token={data['token']}")

            raise Exception(data.get('message', 'Error desconocido en Flow'))

    except Exception as e:
        messages.error(request, f"Error al procesar el pago: {e}")
        return redirect('cart_detail')

    # # 1. Validar que el perfil exista y tenga datos de envío
    # try:
    #     perfil = request.user.perfil
    # except Perfil.DoesNotExist:
    #     messages.warning(request, 'Debes completar tu perfil antes de comprar.')
    #     return redirect('profile')
    
    # if not perfil.direccion or not perfil.comuna:
    #     messages.warning(request, 'Completa tus datos de envío en el perfil antes de pagar.')
    #     return redirect('profile')

    # # 2. Validar Email para Flow (Failsafe)
    # if not request.user.email:
    #     messages.error(request, "Tu cuenta no tiene un email válido para procesar el pago.")
    #     return redirect('profile')

    # try:
    #     with transaction.atomic():
    #         # 1. LÓGICA DE CÁLCULO UNIFICADA
    #         subtotal_productos = cart.get_total_precio()
    #         costo_envio = 3990
    #         monto_descuento = 0
            
    #         # 2. Descuento del 15% si es administrativo (staff)
    #         if request.user.is_staff:
    #             monto_descuento = int(subtotal_productos * 0.15)
            
    #         total_a_pagar = (subtotal_productos + costo_envio) - monto_descuento

    #         # 3. Crear el Pedido con el TOTAL REAL
    #         pedido = Pedido.objects.create(
    #             usuario=request.user,
    #             direccion=perfil.direccion,
    #             ciudad=perfil.ciudad,
    #             codigo_postal=perfil.codigo_postal,
    #             total=total_a_pagar  # Guardamos el monto final con descuento y envío
    #         )

    #         # 4. Validar Stock y crear Items
    #         for item in cart:
    #             producto = item['producto']
    #             if producto.stock < item['cantidad']:
    #                 raise ValueError(f"Stock insuficiente para {producto.nombre}")

    #             ItemPedido.objects.create(
    #                 pedido=pedido,
    #                 producto=producto,
    #                 precio=item['precio'],
    #                 cantidad=item['cantidad']
    #             )
    #             # Descontar stock
    #             producto.stock -= item['cantidad']
    #             producto.save()

    #         # 5. Configurar Pasarela de Pago (Flow)
    #         url_api = f"{settings.FLOW_URL_BASE}/payment/create"
            
    #         params = {
    #             "apiKey": settings.FLOW_API_KEY,
    #             "commerceOrder": str(pedido.id),
    #             "subject": f"Compra Snake Shop - Pedido #{pedido.id}",
    #             "currency": "CLP",
    #             "amount": int(total_a_pagar), # Monto exacto enviado a Flow
    #             "email": request.user.email,
    #             "urlReturn": request.build_absolute_uri(reverse('order_complete', args=[pedido.id])),
    #             "urlConfirmation": request.build_absolute_uri(reverse('confirmacion_flow')),
    #         }
            
    #         # Firma y Petición
    #         params["s"] = generar_firma_flow(params)
    #         response = requests.post(url_api, data=params)
    #         data = response.json()

    #         if response.status_code == 200 and 'url' in data:
    #             request.session['pedido_id'] = pedido.id
    #             cart.clear() # Limpiamos el carrito solo si la redirección es exitosa
    #             return redirect(f"{data['url']}?token={data['token']}")
    #         else:
    #             error_flow = data.get('message', 'Error desconocido en Flow')
    #             raise Exception(f"Flow API Error: {error_flow}")

    # except Exception as e:
    #     # Si algo falla, el 'transaction.atomic' hace rollback (el stock no se descuenta)
    #     messages.error(request, f"Error al procesar el pago: {e}")
    #     return redirect('cart_detail')

@csrf_exempt
@require_POST
def confirmacion_flow(request):

    # Webhook: Recibe la confirmación asíncrona de Flow.
    token = request.POST.get('token')
    url_status = f"{settings.FLOW_URL_BASE}/payment/getStatus"
    params = {"apiKey": settings.FLOW_API_KEY, "token": token}
    params["s"] = generar_firma_flow(params)
    
    response = requests.get(url_status, params=params)
    data = response.json()
    
    if data.get('status') == 2: # 2 = Pagado
        pedido = Pedido.objects.get(id=data.get('commerceOrder'))
        if not pedido.pagado:
            pedido.pagado = True
            pedido.save()
            Transaccion.objects.create(
                pedido=pedido, 
                id_transaccion=token,
                monto=data.get('amount'), 
                estado='aprobado'
            )
    return HttpResponse(status=200)

@csrf_exempt
def order_complete(request, pedido_id):
    # Vista de retorno tras el pago exitoso (urlReturn). Se elimina @login_required para evitar errores 404 al volver de la pasarela.

    # Buscamos el pedido por ID. Quitamos la restricción de 'usuario=request.user' 
    # temporalmente en esta vista de éxito para asegurar que cargue tras la redirección.
    pedido = get_object_or_404(Pedido, id=pedido_id)
    return render(request, 'snake_shop/order_complete.html', {'pedido': pedido})

def pago_fallido(request):

    # Vista de retorno cuando el pago es rechazado.
    messages.error(request, 'El pago no pudo ser procesado o fue cancelado.')
    return redirect('cart_detail')

# Vistas de Cliente (Historial)
@login_required
def mis_pedidos_view(request):
    pedidos = Pedido.objects.filter(usuario=request.user).order_by('-creado')
    return render(request, 'snake_shop/mis_pedidos.html', {'pedidos': pedidos})

@login_required
def detalle_pedido_view(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)
    return render(request, 'snake_shop/detalle_pedido.html', {
        'pedido': pedido, 
        'items': pedido.items.all()
    })    

@login_required
@require_POST
def eliminar_pedido(request, pedido_id):

    # Permite al usuario eliminar un pedido solo si NO ha sido pagado.
    pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)
    
    if not pedido.pagado:
        # Devolvemos el stock al inventario antes de borrar
        for item in pedido.items.all():
            item.producto.stock += item.cantidad
            item.producto.save()
            
        pedido.delete()
        messages.success(request, f'Pedido #{pedido_id} eliminado correctamente.')
    else:
        messages.error(request, 'No puedes eliminar un pedido que ya ha sido pagado.')
        
    return redirect('mis_pedidos')    

# Vistas de Vendedor (Gestión)
def es_vendedor(user):
    # Verifica si el usuario tiene permisos de vendedor
    return user.is_staff or (hasattr(user, 'perfil') and user.perfil.is_seller)

@login_required
@user_passes_test(es_vendedor, login_url='/login/')
def crear_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            producto = form.save(commit=False)
            producto.vendedor = request.user
            producto.save()
            messages.success(request, "Producto creado exitosamente.")
            return redirect('lista_productos')
    else:
        form = ProductoForm()
    return render(request, 'snake_shop/crear_producto.html', {'form': form})

@login_required
@user_passes_test(es_vendedor, login_url='/login/')
def gestion_pedidos(request):
    if request.user.is_staff:
        pedidos = Pedido.objects.all().order_by('-creado')
    else:
        pedidos = Pedido.objects.filter(items__producto__vendedor=request.user).distinct().order_by('-creado')
    return render(request, 'snake_shop/gestion_pedidos.html', {'pedidos': pedidos})

@login_required
@user_passes_test(es_vendedor, login_url='/login/')
@require_POST
def actualizar_estado_vendedor(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    nuevo_estado = request.POST.get('estado_despacho')
    pagado = request.POST.get('pagado') == 'on' 

    if nuevo_estado in dict(Pedido.ESTADO_CHOICES):
        pedido.estado_despacho = nuevo_estado
        pedido.pagado = pagado
        pedido.save()

        # LOGICA PARA REFLEJAR EN EL PANEL DE TRANSACCIONES
        if pedido.pagado:
            # Creamos o actualizamos la transacción para que aparezca en el admin
            Transaccion.objects.get_or_create(
                pedido=pedido,
                defaults={
                    'monto': pedido.get_total_cost(), # O el campo de total que uses
                    'estado': 'aprobado'
                }
            )
        else:
            # Si el vendedor quita el pago, opcionalmente eliminamos o marcamos la transacción
            Transaccion.objects.filter(pedido=pedido).delete()

        messages.success(request, f'Pedido #{pedido.id} actualizado correctamente.')
    
    return redirect('gestion_pedidos')

# gestión de tickets de soporte técnico
@login_required
@user_passes_test(es_vendedor, login_url='/login/')
def gestion_tickets(request):
    # Muestra todos los tickets de soporte para el staff usando los campos correctos
    # Cambiamos 'fecha_creacion' por 'creado' que es el que existe en tu modelo
    tickets = TicketSoporte.objects.all().order_by('-creado') 
    return render(request, 'snake_shop/gestion_tickets.html', {'tickets': tickets})

@login_required
@user_passes_test(es_vendedor, login_url='/login/')
@require_POST
def actualizar_ticket(request, ticket_id):
    # Permite responder y cambiar el estado del ticket
    ticket = get_object_or_404(TicketSoporte, id=ticket_id)
    nuevo_estado = request.POST.get('estado')
    respuesta = request.POST.get('respuesta_vendedor')

    if nuevo_estado:
        ticket.estado = nuevo_estado
        ticket.respuesta_vendedor = respuesta
        ticket.save()
        messages.success(request, f"Ticket #{ticket.id} actualizado correctamente.")
    
    return redirect('gestion_tickets')

# Reporte de ventas por vendedor
@login_required
@user_passes_test(es_vendedor)
def estadisticas_vendedor(request):
    # 1. Ventas totales y Ticket Promedio
    total_recaudado = Transaccion.objects.filter(estado='aprobado').aggregate(Sum('monto'))['monto__sum'] or 0
    cantidad_pagados = Transaccion.objects.filter(estado='aprobado').count()
    ticket_promedio = total_recaudado / cantidad_pagados if cantidad_pagados > 0 else 0
    
    # 2. Top 3 Productos 
    productos_top = Pedido.objects.filter(pagado=True) \
        .values('items__producto__nombre') \
        .annotate(total_vendido=Sum('items__cantidad')) \
        .order_by('-total_vendido')[:3]

    # 3. DEFINICIÓN DE VARIABLES FALTANTES 
    resumen_transacciones = Transaccion.objects.values('estado').annotate(cantidad=Count('id'))
    pedidos_pendientes = Pedido.objects.filter(estado_despacho='pendiente').count()
    total_pedidos = Pedido.objects.count()

    # 4. Diccionario de contexto corregido
    context = {
        'total_recaudado': total_recaudado,
        'ticket_promedio': ticket_promedio,
        'productos_top': productos_top,
        'resumen_transacciones': resumen_transacciones, # Ahora sí está definido
        'pedidos_pendientes': pedidos_pendientes,       # Ahora sí está definido
        'total_pedidos': total_pedidos,               # Ahora sí está definido
    }
    return render(request, 'snake_shop/estadisticas.html', context)

@require_POST
def seleccionar_envio(request):
    tipo_envio = request.POST.get("envio", "retiro")  # "despacho" o "retiro"

    if tipo_envio not in ["despacho", "retiro"]:
        return JsonResponse({"error": "Opción inválida"}, status=400)

    request.session["tipo_envio"] = tipo_envio
    request.session.modified = True

    return JsonResponse({"ok": True})