/**
 * Global Dynamic Wishlist Functionality
 * Handles heart icon clicks across all pages with real-time synchronization
 */

// Global wishlist state
let wishlistState = new Set();
let isInitialized = false;

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing wishlist system...');
    // Initialize wishlist functionality
    initializeWishlistSystem();
});

// Also initialize if DOM is already loaded
if (document.readyState === 'loading') {
    // DOM is still loading
    document.addEventListener('DOMContentLoaded', function() {
        console.log('DOM loaded (fallback), initializing wishlist system...');
        initializeWishlistSystem();
    });
} else {
    // DOM is already loaded
    console.log('DOM already loaded, initializing wishlist system immediately...');
    initializeWishlistSystem();
}

/**
 * Initialize the complete wishlist system
 */
async function initializeWishlistSystem() {
    if (isInitialized) return;
    
    // Setup notification system
    setupNotificationSystem();
    
    // Load current wishlist state
    await loadWishlistState();
    
    // Setup wishlist handlers
    setupWishlistHandlers();
    
    // Update all wishlist icons based on current state
    updateAllWishlistIcons();
    
    isInitialized = true;
}

/**
 * Load current wishlist state from server
 */
async function loadWishlistState() {
    const token = getJwtToken();
    if (!token) {
        wishlistState.clear();
        return;
    }
    
    try {
        // Get all product IDs on the current page
        const productIds = Array.from(document.querySelectorAll('[data-product-id]'))
            .map(el => el.getAttribute('data-product-id'))
            .filter(id => id && id !== 'undefined' && id !== 'null');
        
        console.log('Loading wishlist state for products:', productIds);
        
        if (productIds.length === 0) {
            console.log('No products found on page');
            return;
        }
        
        const response = await fetch('/api/wishlist/status/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token,
                'X-CSRFToken': getCSRFToken(),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ product_ids: productIds })
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('Wishlist status response:', data);
            if (data.success) {
                // Update wishlist state
                wishlistState.clear();
                Object.entries(data.wishlist_status).forEach(([productId, isWishlisted]) => {
                    if (isWishlisted) {
                        wishlistState.add(productId);
                    }
                });
                console.log('Updated wishlist state:', Array.from(wishlistState));
            }
        } else {
            console.error('Failed to load wishlist status:', response.status, response.statusText);
        }
    } catch (error) {
        console.error('Error loading wishlist state:', error);
    }
}

/**
 * Setup wishlist click handlers for all heart icons
 */
function setupWishlistHandlers() {
    document.querySelectorAll('.wish-icon, .wishlist-btn, [data-wishlist-toggle]').forEach(function(icon) {
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
    const isWishlisted = wishlistState.has(productId);
    const addUrl = this.getAttribute('data-add-url');
    const removeUrl = this.getAttribute('data-remove-url');
    
    console.log('Wishlist click:', {
        productId,
        isWishlisted,
        addUrl,
        removeUrl,
        currentState: Array.from(wishlistState)
    });
    
    if (!productId) {
        console.error('Missing product ID:', this);
        showNotification('Error: Missing product ID', 'error');
        return;
    }
    
    if (!addUrl || !removeUrl) {
        console.error('Missing wishlist URLs:', {
            productId,
            addUrl,
            removeUrl,
            element: this
        });
        showNotification('Error: Missing wishlist URLs', 'error');
        return;
    }
    
    // Validate URLs
    if (!addUrl.includes('/wishlist/add/') || !removeUrl.includes('/wishlist/remove/')) {
        console.error('Invalid wishlist URLs:', {
            addUrl,
            removeUrl
        });
        showNotification('Error: Invalid wishlist URLs', 'error');
        return;
    }
    
    const url = isWishlisted ? removeUrl : addUrl;
    console.log('Using URL:', url);
    
    // Get JWT token
    const token = getJwtToken();
    if (!token) {
        console.log('No JWT token found, redirecting to login');
        // Redirect to login with current page as next
        const currentPath = window.location.pathname + window.location.search;
        window.location.href = '/login/?next=' + encodeURIComponent(currentPath);
        return;
    }
    
    // Disable the icon during request
    this.style.pointerEvents = 'none';
    this.style.opacity = '0.6';
    this.classList.add('updating');
    
    // Optimistically update UI
    updateWishlistIcon(this, !isWishlisted);
    
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
        console.log('Response status:', response.status);
        if (response.status === 401) {
            // Token expired, redirect to login
            const currentPath = window.location.pathname + window.location.search;
            window.location.href = '/login/?next=' + encodeURIComponent(currentPath);
            return null;
        }
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Wishlist response data:', data);
        if (!data) return;
        
        if (data.success) {
            // Update global state
            if (data.action === 'add') {
                wishlistState.add(productId);
                showNotification('Added to wishlist!', 'success');
            } else {
                wishlistState.delete(productId);
                showNotification('Removed from wishlist', 'info');
            }
            
            // Broadcast change to all instances of this product on the page
            broadcastWishlistChange(productId, data.action === 'add');
            
            // Update wishlist count in header if it exists
            updateWishlistCount();
        } else {
            console.error('Server returned error:', data);
            // Revert optimistic update on error
            updateWishlistIcon(this, isWishlisted);
            showNotification(data.message || 'Error updating wishlist', 'error');
        }
    })
    .catch(error => {
        console.error('Wishlist error:', error);
        console.error('Error details:', {
            message: error.message,
            stack: error.stack,
            url: url,
            productId: productId
        });
        
        // Revert optimistic update on error
        updateWishlistIcon(this, isWishlisted);
        
        // Show specific error message based on error type
        if (error.message.includes('Failed to fetch')) {
            showNotification('Network error: Please check your connection', 'error');
        } else if (error.message.includes('404')) {
            showNotification('Error: Wishlist endpoint not found', 'error');
        } else if (error.message.includes('500')) {
            showNotification('Server error: Please try again later', 'error');
        } else {
            showNotification(`Error updating wishlist: ${error.message}`, 'error');
        }
    })
    .finally(() => {
        // Re-enable the icon
        this.style.pointerEvents = '';
        this.style.opacity = '1';
        this.classList.remove('updating');
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
 * Update a single wishlist icon's appearance
 */
function updateWishlistIcon(iconElement, isWishlisted) {
    const heartIcon = iconElement.querySelector('i') || iconElement;
    
    if (isWishlisted) {
        heartIcon.className = 'fa-solid fa-heart';
        heartIcon.style.color = '#b91c1c';
        iconElement.setAttribute('aria-pressed', 'true');
        iconElement.setAttribute('title', 'Remove from Wishlist');
        iconElement.classList.add('wishlisted');
    } else {
        heartIcon.className = 'fa-regular fa-heart';
        heartIcon.style.color = '#b91c1c';
        iconElement.setAttribute('aria-pressed', 'false');
        iconElement.setAttribute('title', 'Add to Wishlist');
        iconElement.classList.remove('wishlisted');
    }
}

/**
 * Update all wishlist icons on the page based on current state
 */
function updateAllWishlistIcons() {
    document.querySelectorAll('[data-product-id]').forEach(element => {
        const productId = element.getAttribute('data-product-id');
        const isWishlisted = wishlistState.has(productId);
        updateWishlistIcon(element, isWishlisted);
    });
}

/**
 * Broadcast wishlist change to all instances of a product on the page
 */
function broadcastWishlistChange(productId, isWishlisted) {
    document.querySelectorAll(`[data-product-id="${productId}"]`).forEach(element => {
        updateWishlistIcon(element, isWishlisted);
        
        // Add a subtle animation to show the change
        element.classList.add('updating');
        element.style.transform = 'scale(1.1)';
        setTimeout(() => {
            element.style.transform = 'scale(1)';
            element.classList.remove('updating');
        }, 300);
    });
}

/**
 * Update wishlist count in header
 */
function updateWishlistCount() {
    // Update the count based on current state
    const wishlistIcon = document.querySelector('a[href*="wishlist"] i');
    const wishlistCountElement = document.querySelector('.wishlist-count, [data-wishlist-count]');
    
    if (wishlistCountElement) {
        wishlistCountElement.textContent = wishlistState.size;
    }
    
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
    updateAllWishlistIcons();
}

/**
 * Add product to wishlist state (for external use)
 */
function addToWishlistState(productId) {
    wishlistState.add(productId);
    broadcastWishlistChange(productId, true);
    updateWishlistCount();
}

/**
 * Remove product from wishlist state (for external use)
 */
function removeFromWishlistState(productId) {
    wishlistState.delete(productId);
    broadcastWishlistChange(productId, false);
    updateWishlistCount();
}

/**
 * Check if product is in wishlist
 */
function isInWishlist(productId) {
    return wishlistState.has(productId);
}

/**
 * Force refresh wishlist state from server
 */
async function refreshWishlistState() {
    await loadWishlistState();
    updateAllWishlistIcons();
    updateWishlistCount();
}

// Handle page navigation to maintain wishlist state
window.addEventListener('beforeunload', function() {
    // Save current wishlist state to sessionStorage for quick restoration
    try {
        sessionStorage.setItem('wishlist_state', JSON.stringify(Array.from(wishlistState)));
    } catch (e) {
        console.warn('Could not save wishlist state to sessionStorage');
    }
});

// Restore wishlist state on page load if available (but always refresh from server)
window.addEventListener('load', function() {
    try {
        const savedState = sessionStorage.getItem('wishlist_state');
        if (savedState) {
            const stateArray = JSON.parse(savedState);
            wishlistState = new Set(stateArray);
            console.log('Restored wishlist state from session:', stateArray);
            updateAllWishlistIcons();
        }
    } catch (e) {
        console.warn('Could not restore wishlist state from sessionStorage');
    }
});

/**
 * Debug function to check current state
 */
function debugWishlistState() {
    console.log('=== WISHLIST DEBUG INFO ===');
    console.log('Current wishlist state:', Array.from(wishlistState));
    console.log('JWT Token:', getJwtToken() ? 'Present' : 'Missing');
    console.log('Is initialized:', isInitialized);
    
    const productElements = document.querySelectorAll('[data-product-id]');
    console.log('Products on page:', productElements.length);
    
    productElements.forEach(el => {
        const productId = el.getAttribute('data-product-id');
        const addUrl = el.getAttribute('data-add-url');
        const removeUrl = el.getAttribute('data-remove-url');
        const ariaPressed = el.getAttribute('aria-pressed');
        const isInState = wishlistState.has(productId);
        
        console.log(`Product ${productId}:`, {
            element: el,
            addUrl,
            removeUrl,
            ariaPressed,
            isInWishlistState: isInState,
            iconClass: el.querySelector('i')?.className,
            urlsValid: addUrl && addUrl.includes('/wishlist/add/') && removeUrl && removeUrl.includes('/wishlist/remove/')
        });
    });
    
    // Test API endpoint
    console.log('Testing wishlist status API...');
    const productIds = Array.from(productElements).map(el => el.getAttribute('data-product-id')).filter(id => id);
    if (productIds.length > 0) {
        fetch('/api/wishlist/status/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + getJwtToken(),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ product_ids: productIds })
        }).then(r => r.json()).then(data => {
            console.log('API Response:', data);
        }).catch(err => {
            console.error('API Error:', err);
        });
    }
    
    console.log('=== END DEBUG INFO ===');
}

// Export functions for global use
window.wishlistUtils = {
    setupWishlistHandlers,
    showNotification,
    reinitializeWishlist,
    addToWishlistState,
    removeFromWishlistState,
    isInWishlist,
    refreshWishlistState,
    initializeWishlistSystem,
    getWishlistState: () => Array.from(wishlistState),
    debug: debugWishlistState
};
