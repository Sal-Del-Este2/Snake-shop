// snake_shop/static/js/payment_formatting.js

document.addEventListener('DOMContentLoaded', function() {
    const cardNumberInput = document.getElementById('id_card_number');
    const expiryDateInput = document.getElementById('id_expiry_date');
    const cvvInput = document.getElementById('id_cvv');

    // 1. FORMATO PARA NÚMERO DE TARJETA (XXXX XXXX XXXX XXXX)
    if (cardNumberInput) {
        cardNumberInput.addEventListener('input', function(e) {
            const { target } = e;
            // Elimina todos los caracteres no numéricos
            let value = target.value.replace(/\D/g, '');
            
            // Agrega espacios cada 4 dígitos
            value = value.replace(/(\d{4}(?!\s))/g, '$1 ').trim();
            
            // Limita la longitud máxima a 19 (16 dígitos + 3 espacios)
            target.value = value.substring(0, 19);
        });
    }

    // 2. FORMATO PARA FECHA DE VENCIMIENTO (MM/AA)
    if (expiryDateInput) {
        expiryDateInput.addEventListener('input', function(e) {
            const { target } = e;
            // Elimina todos los caracteres no numéricos
            let value = target.value.replace(/\D/g, '');

            // Añade la barra después de los primeros dos dígitos
            if (value.length > 2) {
                value = value.substring(0, 2) + '/' + value.substring(2, 4);
            }
            
            // Limita a 5 caracteres (MM/AA)
            target.value = value.substring(0, 5);
        });
    }
    
    // 3. Limitar CVV a 3 o 4 dígitos y solo números
    if (cvvInput) {
        cvvInput.addEventListener('input', function(e) {
            e.target.value = e.target.value.replace(/\D/g, '').substring(0, 4);
        });
    }
    
});