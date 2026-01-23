# snake_shop/forms.py
from django import forms
from .models import Perfil, User
from django.core.exceptions import ValidationError
from .models import Perfil, Producto

class CartAddProductForm(forms.Form):
    cantidad = forms.IntegerField(label='Cantidad', min_value=1, initial=1)
    override = forms.BooleanField(required=False, initial=False, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        self.producto = kwargs.pop('producto', None)
        super().__init__(*args, **kwargs)

    def clean_cantidad(self):
        cantidad = self.cleaned_data.get('cantidad')
        if self.producto and cantidad > self.producto.stock:
            raise ValidationError(
                f'Solo quedan {self.producto.stock} unidades de este producto en stock.'
            )
        return cantidad # <<-- ¡Esta es la línea que faltaba!

class PerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ('direccion', 'comuna','ciudad', 'codigo_postal', 'pais', 'telefono')
        
class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=True) # El email es obligatorio para Flow

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']        

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ('nombre', 'slug', 'descripcion', 'precio', 'precio_promocion', 'en_promocion', 'stock', 'categoria', 'imagen')        
        
# ticket soporte técnico
from .models import TicketSoporte 

# ...
class ContactoTecnicoForm(forms.ModelForm):
    # Campos adicionales que pueden no estar en el modelo base pero son útiles para el formulario
    
    class Meta:
        model = TicketSoporte
        fields = ('nombre_completo', 'email', 'tipo_solicitud', 'numero_pedido', 
                  'asunto', 'descripcion', 'archivo')
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describa el problema, cuándo ocurrió y qué pasos tomó para intentar solucionarlo.'}),
            'numero_pedido': forms.TextInput(attrs={'placeholder': 'Opcional, pero necesario para garantías.'}),
        }
        