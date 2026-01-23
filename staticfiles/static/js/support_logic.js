// snake_shop/static/js/support_logic.js

document.addEventListener('DOMContentLoaded', function() {
    const tipoSolicitud = document.getElementById('id_tipo_solicitud');
    const orderIdField = document.querySelector('.order-id-field');
    const orderIdInput = document.querySelector('.order-check-input');
    
    // Si no existen los elementos, salimos
    if (!tipoSolicitud || !orderIdField || !orderIdInput) return;

    const GARANTIA_VALUE = 'garantia'; 
    const DEVOLUCION_VALUE = 'devolucion'; 

    /**
     * Alterna la visibilidad y el estado 'required' del campo de número de pedido
     * basándose en la solicitud seleccionada.
     */
    function toggleOrderRequirement() {
        const selectedValue = tipoSolicitud.value;
        
        // Identificar si la opción seleccionada requiere número de pedido
        const isRequired = selectedValue === GARANTIA_VALUE || selectedValue === DEVOLUCION_VALUE;

        // 1. Alternar estado 'required'
        orderIdInput.required = isRequired;
        orderIdInput.placeholder = isRequired ? "OBLIGATORIO: Ingrese N° de Pedido" : "Opcional";

        // 2. Alternar estilo de resalte (para CSS)
        orderIdField.classList.toggle('is-required', isRequired);
    }

    // Ejecutar al cargar la página para establecer el estado inicial
    toggleOrderRequirement(); 

    // Escuchar cambios en el selector
    tipoSolicitud.addEventListener('change', toggleOrderRequirement);
});