# snake_shop/admin.py
from django.contrib import admin
from django.db.models import Sum
from django.db.models.functions import TruncDate, TruncMonth
from .models import (Categoria, Producto, Perfil, Pedido, ItemPedido, Transaccion, TicketSoporte, TicketAttachment, FolioSequence, )

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'slug']
    prepopulated_fields = {'slug': ('nombre',)}

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'slug', 'precio', 'precio_promocion', 'stock', 'disponible', 'en_promocion', 'creado', 'actualizado']
    list_filter = ['disponible', 'en_promocion', 'creado', 'actualizado']
    list_editable = ['precio', 'precio_promocion', 'en_promocion', 'stock', 'disponible']
    prepopulated_fields = {'slug': ('nombre',)}
    
    fieldsets = (
        (None, {'fields': ('nombre', 'slug', 'categoria', 'vendedor')}),
        ('Precio y Promoción', {'fields': ('precio', 'precio_promocion', 'en_promocion'),'description': 'Si "En Promoción" está activo, se mostrará precio_promocion en lugar del precio normal.'}),
        ('Stock e Inventario', {'fields': ('stock', 'disponible', 'imagen')}),
        ('Descripción', {'fields': ('descripcion',), 'classes': ('collapse',)}),
    )

@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'rol', 'ciudad']
    list_filter = ['rol']

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ['id', 'folio', 'usuario', 'total', 'pagado', 'estado_despacho', 'creado']
    list_filter = ['pagado', 'estado_despacho', 'creado']
    search_fields = ['folio', 'usuario__username', 'usuario__email']
    date_hierarchy = 'creado'
    readonly_fields = ['folio', 'creado', 'actualizado']

@admin.register(ItemPedido)
class ItemPedidoAdmin(admin.ModelAdmin):
    list_display = ['id', 'pedido', 'producto', 'precio', 'cantidad']

@admin.register(Transaccion)
class TransaccionAdmin(admin.ModelAdmin):
    list_display = ('id', 'pedido', 'flow_order', 'monto', 'estado', 'creado')
    list_filter = ('estado', ('creado', admin.DateFieldListFilter))
    search_fields = ('pedido__folio', 'pedido__id', 'flow_order', 'flow_token')

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)

        try:
            qs = response.context_data['cl'].queryset
        except (AttributeError, KeyError):
            return response

        # Ajusta el estado usado para sumar según tu lógica (ej: 'pagado')
        total = qs.filter(estado='pagado').aggregate(Sum('monto'))['monto__sum'] or 0

        extra_context = extra_context or {}
        extra_context['total_ventas'] = f"{total:,.0f}".replace(",", ".")
        return super().changelist_view(request, extra_context=extra_context)

@admin.register(TicketSoporte)
class TicketSoporteAdmin(admin.ModelAdmin):
    list_display = ['folio', 'usuario', 'tipo_solicitud', 'estado', 'numero_pedido', 'creado']
    list_filter = ['tipo_solicitud', 'estado', 'creado']
    search_fields = ['folio', 'numero_pedido', 'email', 'nombre_completo']
    date_hierarchy = 'creado'
    readonly_fields = ['folio', 'creado']

@admin.register(TicketAttachment)
class TicketAttachmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'ticket', 'tipo_mime', 'fecha_carga']
    list_filter = ['tipo_mime', 'fecha_carga']
    search_fields = ['ticket__folio']

@admin.register(FolioSequence)
class FolioSequenceAdmin(admin.ModelAdmin):
    list_display = ['tipo', 'anio', 'correlativo']
    list_filter = ['tipo', 'anio']
