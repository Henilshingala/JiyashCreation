// Color picker functionality for Django admin
document.addEventListener('DOMContentLoaded', function() {
    // Wait a bit for Django admin to fully load
    setTimeout(function() {
        // Find all color input fields
        const colorFields = document.querySelectorAll('input[name$="_color"]');
        
        colorFields.forEach(function(field) {
            // Create wrapper div
            const wrapper = document.createElement('div');
            wrapper.className = 'color-field-wrapper';
            
            // Insert wrapper before the field
            field.parentNode.insertBefore(wrapper, field);
            
            // Move field into wrapper
            wrapper.appendChild(field);
            
            // Change input type to color
            field.type = 'color';
            field.className = 'color-picker-input';
            
            // Create value display
            const valueDisplay = document.createElement('span');
            valueDisplay.className = 'color-value-display';
            valueDisplay.textContent = field.value || '#000000';
            wrapper.appendChild(valueDisplay);
            
            // Update display when color changes
            field.addEventListener('input', function() {
                valueDisplay.textContent = field.value;
            });
            
            // Also update on change event
            field.addEventListener('change', function() {
                valueDisplay.textContent = field.value;
            });
        });
    }, 500);
});
