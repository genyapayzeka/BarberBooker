/**
 * Admin Dashboard JavaScript
 * This file contains JavaScript functionality for the admin dashboard.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    
    // Add active class to current nav item
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href && currentPath.startsWith(href) && href !== '/admin/') {
            link.classList.add('active');
        } else if (currentPath === '/admin/' && href === '/admin/') {
            link.classList.add('active');
        }
    });
    
    // Setup confirmation dialog for deleting items
    const confirmationForms = document.querySelectorAll('.delete-confirmation-form');
    confirmationForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });
    
    // Setup datepicker if available
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(input => {
        input.min = new Date().toISOString().split('T')[0]; // Set min date to today
    });
    
    // Handle password confirmation validation
    const newPasswordInput = document.getElementById('new_password');
    const confirmPasswordInput = document.getElementById('confirm_password');
    
    if (newPasswordInput && confirmPasswordInput) {
        function validatePasswordMatch() {
            if (confirmPasswordInput.value !== newPasswordInput.value) {
                confirmPasswordInput.setCustomValidity("Passwords don't match");
            } else {
                confirmPasswordInput.setCustomValidity('');
            }
        }
        
        newPasswordInput.addEventListener('change', validatePasswordMatch);
        confirmPasswordInput.addEventListener('keyup', validatePasswordMatch);
    }
    
    // Setup availability checking for appointment scheduling
    const dateSelect = document.getElementById('date');
    const timeSelect = document.getElementById('time');
    const barberSelect = document.getElementById('barber_id');
    const availabilityIndicator = document.getElementById('availability-indicator');
    
    if (dateSelect && timeSelect && barberSelect && availabilityIndicator) {
        function checkAvailability() {
            const date = dateSelect.value;
            const time = timeSelect.value;
            const barberId = barberSelect.value;
            
            if (!date || !time || !barberId) return;
            
            availabilityIndicator.innerHTML = '<div class="spinner-border spinner-border-sm" role="status"><span class="visually-hidden">Loading...</span></div> Checking availability...';
            
            fetch(`/admin/check-availability?date=${date}&time=${time}&barber_id=${barberId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        if (data.data.available) {
                            availabilityIndicator.innerHTML = '<span class="text-success"><i class="bi bi-check-circle-fill"></i> This time slot is available</span>';
                        } else {
                            availabilityIndicator.innerHTML = '<span class="text-danger"><i class="bi bi-exclamation-circle-fill"></i> This time slot is already booked</span>';
                        }
                    } else {
                        availabilityIndicator.innerHTML = '<span class="text-danger">Error checking availability</span>';
                    }
                })
                .catch(error => {
                    availabilityIndicator.innerHTML = '<span class="text-danger">Error checking availability</span>';
                    console.error('Error:', error);
                });
        }
        
        dateSelect.addEventListener('change', checkAvailability);
        timeSelect.addEventListener('change', checkAvailability);
        barberSelect.addEventListener('change', checkAvailability);
        
        // Check initially if all values are set
        if (dateSelect.value && timeSelect.value && barberSelect.value) {
            checkAvailability();
        }
    }
    
    // Setup phone number formatting
    const phoneInputs = document.querySelectorAll('input[type="tel"]');
    
    phoneInputs.forEach(input => {
        input.addEventListener('blur', function() {
            let value = this.value.replace(/\D/g, '');
            
            if (value.length === 10) {
                // Format as (XXX) XXX-XXXX for US numbers
                this.value = `(${value.substring(0, 3)}) ${value.substring(3, 6)}-${value.substring(6, 10)}`;
            } else if (value.length === 11 && value.startsWith('1')) {
                // Format as +1 (XXX) XXX-XXXX for US numbers with country code
                this.value = `+1 (${value.substring(1, 4)}) ${value.substring(4, 7)}-${value.substring(7, 11)}`;
            }
        });
    });
    
    // Setup service duration/price calculation
    const serviceSelect = document.getElementById('service_id');
    const durationDisplay = document.getElementById('duration-display');
    const priceDisplay = document.getElementById('price-display');
    
    if (serviceSelect && (durationDisplay || priceDisplay)) {
        serviceSelect.addEventListener('change', function() {
            const selectedOption = this.options[this.selectedIndex];
            const serviceInfo = selectedOption.text;
            
            // Extract duration and price from the option text
            // Assuming format like "Service Name - $25.00 (30 min)"
            const durationMatch = serviceInfo.match(/\((\d+) min\)/);
            const priceMatch = serviceInfo.match(/\$(\d+(\.\d+)?)/);
            
            if (durationDisplay && durationMatch) {
                durationDisplay.textContent = `${durationMatch[1]} minutes`;
            }
            
            if (priceDisplay && priceMatch) {
                priceDisplay.textContent = `$${priceMatch[1]}`;
            }
        });
        
        // Trigger change event if a service is already selected
        if (serviceSelect.value) {
            serviceSelect.dispatchEvent(new Event('change'));
        }
    }
});
