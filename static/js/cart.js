/**
 * TIENDA ESCOLAR VIRTUAL - I.E.D. LOS LAURELES
 * Funciones JavaScript interactivas para el carrito de compras y catálogo.
 */

document.addEventListener('DOMContentLoaded', function () {
  // 1. Auto-cerrar alertas Flash después de 5 segundos
  const alerts = document.querySelectorAll('.alert-dismissible');
  alerts.forEach(function (alert) {
    setTimeout(function () {
      const bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    }, 5000);
  });

  // 2. Formatear valores de moneda en COP
  const currencyElements = document.querySelectorAll('.currency-format');
  currencyElements.forEach(function (el) {
    const val = parseFloat(el.textContent);
    if (!isNaN(val)) {
      el.textContent = new Intl.NumberFormat('es-CO', {
        style: 'currency',
        currency: 'COP',
        maximumFractionDigits: 0
      }).format(val);
    }
  });

  // 3. Validación interactiva de stock en modales de producto
  const qtyInputs = document.querySelectorAll('.cart-qty-input');
  qtyInputs.forEach(function (input) {
    input.addEventListener('change', function () {
      const max = parseInt(this.getAttribute('max'));
      const min = parseInt(this.getAttribute('min')) || 1;
      let val = parseInt(this.value);

      if (isNaN(val) || val < min) {
        this.value = min;
      } else if (max && val > max) {
        this.value = max;
        alert(`Stock máximo disponible: ${max} unidades.`);
      }
    });
  });
});
