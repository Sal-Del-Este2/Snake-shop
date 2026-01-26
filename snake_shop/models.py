from django.db import models, transaction
from django.contrib.auth.models import User
from django.urls import reverse
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Max

# Utilidades / Helpers
class FolioSequence(models.Model):
    # Lleva el correlativo de folios por tipo (pedido, ticket, etc.) Formato final: SS-YYYY-00001
    TIPO_CHOICES = [
        ('pedido', 'Pedido'),
        ('ticket', 'Ticket de Soporte'),
    ]
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, unique=True)
    anio = models.PositiveIntegerField()
    correlativo = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.tipo} - {self.anio} - {self.correlativo}"

def generar_folio(tipo: str) -> str:
    # Genera un folio correlativo único y atómico del tipo: SS-YYYY-00001
    year = timezone.now().year
    with transaction.atomic():
        seq, created = FolioSequence.objects.select_for_update().get_or_create(
            tipo=tipo,
            defaults={'anio': year, 'correlativo': 0},
        )
        # Si cambió el año, reiniciar correlativo
        if seq.anio != year:
            seq.anio = year
            seq.correlativo = 0
        seq.correlativo += 1
        seq.save()
        return f"SS-{seq.anio}-{seq.correlativo:05d}"

def validar_archivo_soporte(file):
    # Valida tamaño y tipo MIME de archivos de soporte. Requerimiento US-18: máx 50MB, formatos: jpg, png, mp4, mov.
    max_size = 50 * 1024 * 1024  # 50MB
    if file.size > max_size:
        raise ValidationError("El archivo no puede superar los 50MB.")

    allowed = [
        'image/jpeg',
        'image/png',
        'video/mp4',
        'video/quicktime',  # mov
    ]

    content_type = getattr(file, 'content_type', None)
    if content_type and content_type not in allowed:
        raise ValidationError("Formato de archivo no permitido (solo jpg, png, mp4, mov).")

# Modelos para Productos y Categorías
class Categoria(models.Model):
    # Define las categorías a las que pertenecen los productos.
    nombre = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        verbose_name_plural = 'Categorias'

    def __str__(self):
        return self.nombre

    def get_absolute_url(self):
        return reverse('lista_productos_por_categoria', args=[self.slug])

class Producto(models.Model):
    # Define los productos que se venderán en la tienda.
    categoria = models.ForeignKey(Categoria, related_name='productos', on_delete=models.CASCADE)
    nombre = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=200, db_index=True)
    imagen = models.ImageField(upload_to='productos/%Y/%m/%d/', blank=True)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    disponible = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    # Vendedor enlazado al User (Perfil define rol)
    vendedor = models.ForeignKey(User, related_name='productos', on_delete=models.CASCADE)
    # para promociones
    precio_promocion = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=None)
    en_promocion = models.BooleanField(default=False)

    class Meta:
        ordering = ('nombre',)
        indexes = [
            models.Index(fields=['id', 'slug']),
        ]

    def __str__(self):
        return self.nombre

    def get_absolute_url(self):
        return reverse('detalle_producto', args=[self.slug])

# Modelos para Usuarios y Perfiles
class Perfil(models.Model):
    # Modelo de usuario para agregar roles y detalles de envío.
    ROLES = (
        ('cliente', 'Cliente'),
        ('vendedor', 'Vendedor'),
    )
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    rol = models.CharField(max_length=10, choices=ROLES, default='cliente')
    direccion = models.CharField(max_length=150, blank=True)
    comuna = models.CharField(max_length=100, blank=True)
    ciudad = models.CharField(max_length=100, blank=True)
    codigo_postal = models.CharField(max_length=20, blank=True)
    pais = models.CharField(max_length=100, blank=True)
    telefono = models.CharField(max_length=15, blank=True)
    email = models.EmailField(max_length=254, blank=True)

    @property
    def is_seller(self):
        return self.rol == 'vendedor'

    def __str__(self):
        return self.usuario.username

@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.get_or_create(usuario=instance)

# Modelos para Pedidos y Carrito
class Pedido(models.Model):

    ESTADO_CHOICES = (
        ('pendiente', 'Pendiente'),
        ('en_despacho', 'En Despacho'),
        ('completado', 'Completado'),
        ('retiro', 'Retiro en tienda'),
    )

    usuario = models.ForeignKey(User, related_name='pedidos', on_delete=models.SET_NULL, null=True, blank=True) # User, related_name='pedidos', on_delete=models.CASCADE,
    direccion = models.CharField(max_length=250, null=True, blank=True)
    email = models.EmailField(max_length=254, blank=True)
    ciudad = models.CharField(max_length=100, null=True, blank=True)
    codigo_postal = models.CharField(max_length=20, null=True, blank=True)
    envio = models.IntegerField(default=0)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    pagado = models.BooleanField(default=False)
    estado_despacho = models.CharField(max_length=20, choices=(
            ('en_despacho', 'Despacho a domicilio'),
            ('retiro', 'Retiro en tienda'),
        ), default='en_despacho')

    # Campos profesionales de totales
    costo_envio = models.IntegerField(default=0)
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    # envio = models.DecimalField(max_digits=10, decimal_places=2, default=3990.00)
    
    # Folio único para trazabilidad (US-16)
    folio = models.CharField(max_length=50, unique=True, editable=False)
    class Meta:
        ordering = ('-creado',)

    def __str__(self):
        return f'Pedido {self.folio or self.id}'

    def save(self, *args, **kwargs):
        if not self.folio:
            self.folio = generar_folio('pedido')
        super().save(*args, **kwargs)

    def get_total_cost(self):
        # Si el total está persistido, se usa ese valor. # Si no, se calcula a partir de los ítems.
        if self.total and self.total > 0:
            return self.total
        return sum(item.get_cost() for item in self.items.all())

class ItemPedido(models.Model):
    # Detalla los productos que forman parte de un pedido.
    pedido = models.ForeignKey(Pedido, related_name='items', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, related_name='items_pedido', on_delete=models.CASCADE)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    cantidad = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f'Item {self.id} - Pedido {self.pedido.folio}'

    def get_cost(self):
        return self.precio * self.cantidad

# Modelo para Transacciones de Pago
class Transaccion(models.Model):
    # Registra los detalles de las transacciones de pago. Pensado para integración con Flow y auditoría.
    ESTADO_PAGO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('rechazado', 'Rechazado'),
        ('error', 'Error'),
    ]

    pedido = models.ForeignKey(Pedido, related_name='transacciones', on_delete=models.CASCADE)
    id_transaccion = models.CharField(max_length=200)  # ID interno de la app
    flow_order = models.CharField(max_length=200, blank=True, null=True)
    flow_token = models.CharField(max_length=200, blank=True, null=True)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=50, choices=ESTADO_PAGO_CHOICES, default='pendiente')
    raw_webhook = models.JSONField(blank=True, null=True)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Transaccion {self.id_transaccion} - Pedido {self.pedido.folio}'

# Modelos para Servicio Técnico y Soporte
class TicketSoporte(models.Model):
    ESTADO_CHOICES = [
        ('abierto', 'Abierto'),
        ('en_proceso', 'En Proceso'),
        ('resuelto', 'Resuelto'),
        ('cerrado', 'Cerrado'),
    ]

    TIPO_CHOICES = [
        ('falla', 'Falla/Reparación'),
        ('garantia', 'Uso de Garantía'),
        ('consulta', 'Consulta Técnica'),
        ('devolucion', 'Solicitud de Devolución'),
    ]

    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets'
    )
    nombre_completo = models.CharField(max_length=100)
    email = models.EmailField()

    tipo_solicitud = models.CharField(max_length=20, choices=TIPO_CHOICES)
    numero_pedido = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Obligatorio para temas de garantía o devoluciones."
    )
    asunto = models.CharField(max_length=200)
    descripcion = models.TextField()

    # Mantener por compatibilidad (un archivo simple opcional)
    archivo = models.FileField(
        upload_to='soporte/archivos/%Y/%m/%d/',
        blank=True,
        null=True,
        validators=[validar_archivo_soporte]
    )

    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='abierto')
    folio = models.CharField(max_length=50, unique=True, editable=False)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creado']
        verbose_name = 'Ticket de Soporte'
        verbose_name_plural = 'Tickets de Soporte'

    def save(self, *args, **kwargs):
        # Folio único usando el generador central (US-16)
        if not self.folio:
            self.folio = generar_folio('ticket')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.folio

class TicketAttachment(models.Model):
    # Evidencias multimedia asociadas a un ticket de soporte. Evidencia Multimedia (múltiples adjuntos por ticket).
    ticket = models.ForeignKey(
        TicketSoporte,
        on_delete=models.CASCADE,
        related_name='adjuntos'
    )
    archivo = models.FileField(
        upload_to='soporte/archivos/%Y/%m/%d/',
        validators=[validar_archivo_soporte]
    )
    tipo_mime = models.CharField(max_length=100, blank=True)
    fecha_carga = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Adjunto {self.id} - {self.ticket.folio}"