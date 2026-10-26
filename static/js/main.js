// Norelia - Korean Cosmetics Shop - JavaScript

document.addEventListener('DOMContentLoaded', function() {
    
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
    
    // Quantity input validation
    const quantityInputs = document.querySelectorAll('input[type="number"]');
    quantityInputs.forEach(input => {
        input.addEventListener('change', function() {
            const min = parseInt(this.min) || 1;
            const max = parseInt(this.max) || 999;
            let value = parseInt(this.value);
            
            if (value < min) {
                this.value = min;
            } else if (value > max) {
                this.value = max;
                alert(`Максималното количество е ${max}`);
            }
        });
    });
    
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Image zoom on hover (product detail page)
    const mainImage = document.getElementById('mainImage');
    if (mainImage) {
        mainImage.addEventListener('mouseover', function() {
            this.style.transform = 'scale(1.1)';
            this.style.transition = 'transform 0.3s';
        });
        
        mainImage.addEventListener('mouseout', function() {
            this.style.transform = 'scale(1)';
        });
    }
    
    // Confirm before clearing cart
    const clearCartBtn = document.querySelector('form[action*="clear_cart"] button');
    if (clearCartBtn) {
        clearCartBtn.addEventListener('click', function(e) {
            if (!confirm('Сигурни ли сте, че искате да изчистите количката?')) {
                e.preventDefault();
            }
        });
    }
    
    console.log('Norelia Shop - Ready! 🌸');
});
