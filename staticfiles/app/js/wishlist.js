/**
 * Global Wishlist Functionality
 * Handles heart icon clicks across all pages
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize wishlist functionality
    setupWishlistHandlers();
    
    // Setup notification system
    setupNotificationSystem();
});

/**
 * Setup wishlist click handlers for all heart icons
 */
function setupWishlistHandlers() {
    document.querySelectorAll('.wish-icon').forEach(function(icon) {
        // Remove any existing event listeners to prevent duplicates
        icon.removeEventListener('click', handleWishlistClick);
        icon.addEventListener('click', handleWishlistClick);
    });
}

/**
 * Handle wishlist icon click
 */
function handleWishlistClick(e) {
    e.preventDefault();
    e.stopPropagation();
    
    const productId = this.getAttribute('data-product-id');
    const isWishlisted = this.getAttribute('aria-pressed') === 'true';
    const addUrl = this.getAttribute('data-add-url');
    const removeUrl = this.getAttribute('data-remove-url');
    
    if (!productId || !addUrl || !removeUrl) {
        console.error('Missing wishlist data attributes');
        return;
    }
    
    const url = isWishlisted ? removeUrl : addUrl;
    
    // Get JWT token
    const token = getJwtToken();
    if (!token) {
        // Redirect to login with current page as next
        const currentPath = window.location.pathname + window.location.search;
        window.location.href = '/login/?next=' + encodeURIComponent(currentPath);
        return;
    }
    
    // Disable the icon during request
    this.style.pointerEvents = 'none';
    this.style.opacity = '0.6';
    
    // Make the request
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + token,
            'X-CSRFToken': getCSRFToken(),
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (response.status === 401) {
            // Token expired, redirect to login
            const currentPath = window.location.pathname + window.location.search;
            window.location.href = '/login/?next=' + encodeURIComponent(currentPath);
            return null;
        }
        return response.json();
    })
    .then(data => {
        if (!data) return;
        
        if (data.success) {
            const heartIcon = this.querySelector('i');
            if (isWishlisted) {
                // Remove from wishlist
                heartIcon.className = 'fa-regular fa-heart';
                this.setAttribute('aria-pressed', 'false');
                this.setAttribute('title', 'Add to Wishlist');
                showNotification('Removed from wishlist', 'info');
            } else {
                // Add to wishlist
                heartIcon.className = 'fa-solid fa-heart';
                this.setAttribute('aria-pressed', 'true');
                this.setAttribute('title', 'Remove from Wishlist');
                showNotification('Added to wishlist!', 'success');
            }
            
            // Update wishlist count in header if it exists
            updateWishlistCount();
        } else {
            showNotification(data.message || 'Error updating wishlist', 'error');
        }
    })
    .catch(error => {
        console.error('Wishlist error:', error);
        showNotification('Error updating wishlist', 'error');
    })
    .finally(() => {
        // Re-enable the icon
        this.style.pointerEvents = '';
        this.style.opacity = '1';
    });
}

/**
 * Get JWT token from localStorage or cookies
 */
function getJwtToken() {
    try {
        // Try localStorage first
        const token = localStorage.getItem('jwt_token');
        if (token) return token;
        
        // Fallback to cookies
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'jwt_token') {
                return value;
            }
        }
        return null;
    } catch (e) {
        return null;
    }
}

/**
 * Get CSRF token from form or meta tag
 */
function getCSRFToken() {
    // Try to get from form input
    const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfInput) return csrfInput.value;
    
    // Try to get from meta tag
    const csrfMeta = document.querySelector('meta[name=csrf-token]');
    if (csrfMeta) return csrfMeta.getAttribute('content');
    
    return '';
}

/**
 * Setup notification system
 */
function setupNotificationSystem() {
    // Create notification container if it doesn't exist
    if (!document.getElementById('notification-container')) {
        const container = document.createElement('div');
        container.id = 'notification-container';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            pointer-events: none;
        `;
        document.body.appendChild(container);
    }
}

/**
 * Show notification message
 */
function showNotification(message, type = 'info') {
    const container = document.getElementById('notification-container');
    if (!container) return;
    
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Style the notification
    const colors = {
        success: '#10b981',
        error: '#ef4444',
        info: '#3b82f6',
        warning: '#f59e0b'
    };
    
    notification.style.cssText = `
        background: ${colors[type] || colors.info};
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        margin-bottom: 10px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        transform: translateX(100%);
        transition: transform 0.3s ease;
        pointer-events: auto;
        font-weight: 500;
        font-size: 14px;
        max-width: 300px;
        word-wrap: break-word;
    `;
    
    container.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 10);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

/**
 * Update wishlist count in header
 */
function updateWishlistCount() {
    // This would typically make an API call to get the current wishlist count
    // For now, we'll just show a visual feedback
    const wishlistIcon = document.querySelector('a[href*="wishlist"] i');
    if (wishlistIcon) {
        // Add a small animation to indicate update
        wishlistIcon.style.transform = 'scale(1.2)';
        setTimeout(() => {
            wishlistIcon.style.transform = 'scale(1)';
        }, 200);
    }
}

/**
 * Re-initialize wishlist handlers (useful for dynamic content)
 */
function reinitializeWishlist() {
    setupWishlistHandlers();
}

// Export functions for global use
window.wishlistUtils = {
    setupWishlistHandlers,
    showNotification,
    reinitializeWishlist
};
