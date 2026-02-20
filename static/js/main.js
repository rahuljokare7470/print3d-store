/**
 * PrintCraft 3D E-Commerce Store
 * Main JavaScript Application File
 *
 * Production-Ready Vanilla JavaScript
 * Bootstrap 5.3.2 Compatible
 * No external dependencies (vanilla JS only)
 */

document.addEventListener('DOMContentLoaded', function() {
    'use strict';

    // ========================================
    // CONFIGURATION & CONSTANTS
    // ========================================

    const CONFIG = {
        SEARCH_DEBOUNCE_MS: 300,
        SEARCH_MIN_CHARS: 2,
        RECENTLY_VIEWED_LIMIT: 8,
        TOAST_DURATION_MS: 3000,
        LAZY_IMG_CLASS: 'lazy-img',
        SCROLL_THRESHOLD_PX: 50,
        BACK_TO_TOP_THRESHOLD_PX: 300,
        QTY_MIN: 1,
        QTY_MAX: 99,
        WISHLIST_STORAGE_KEY: 'printcraft_wishlist',
        RECENTLY_VIEWED_STORAGE_KEY: 'printcraft_recently_viewed'
    };

    // ========================================
    // UTILITY FUNCTIONS
    // ========================================

    /**
     * Debounce function for search input
     * @param {Function} func - Function to debounce
     * @param {number} delay - Delay in milliseconds
     * @returns {Function} Debounced function
     */
    function debounce(func, delay) {
        let timeoutId;
        return function(...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => func.apply(this, args), delay);
        };
    }

    /**
     * Safely parse JSON with error handling
     * @param {string} jsonString - JSON string to parse
     * @param {*} fallback - Fallback value if parsing fails
     * @returns {*} Parsed JSON or fallback
     */
    function safeJsonParse(jsonString, fallback = null) {
        try {
            return JSON.parse(jsonString);
        } catch (error) {
            console.error('JSON Parse Error:', error);
            return fallback;
        }
    }

    /**
     * Show error notification
     * @param {string} message - Error message
     */
    function logError(message) {
        console.error('[PrintCraft 3D]', message);
    }

    /**
     * Generate unique toast ID
     * @returns {string} Unique ID
     */
    function generateToastId() {
        return 'toast_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    // ========================================
    // TOAST NOTIFICATION SYSTEM
    // ========================================

    /**
     * Show toast notification
     * @param {string} message - Toast message
     * @param {string} type - Toast type: success, error, warning, info
     */
    function showToast(message, type = 'success') {
        // Validate type
        const validTypes = ['success', 'error', 'warning', 'info'];
        if (!validTypes.includes(type)) {
            type = 'success';
        }

        // Create toast container if not exists
        let toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toastContainer';
            toastContainer.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999;';
            document.body.appendChild(toastContainer);
        }

        // Create toast element
        const toastId = generateToastId();
        const toastEl = document.createElement('div');
        toastEl.id = toastId;
        toastEl.className = `toast align-items-center text-white border-0 mb-3`;

        // Set background color based on type
        const bgColorMap = {
            'success': 'bg-success',
            'error': 'bg-danger',
            'warning': 'bg-warning text-dark',
            'info': 'bg-info'
        };
        toastEl.classList.add(bgColorMap[type]);

        // Create toast content
        toastEl.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${escapeHtml(message)}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;

        // Add to container
        toastContainer.appendChild(toastEl);

        // Initialize Bootstrap toast
        const bsToast = new bootstrap.Toast(toastEl);
        bsToast.show();

        // Remove from DOM after hide
        toastEl.addEventListener('hidden.bs.toast', function() {
            toastEl.remove();
        });

        // Auto-hide after duration
        setTimeout(() => {
            if (toastEl.parentNode) {
                bsToast.hide();
            }
        }, CONFIG.TOAST_DURATION_MS);
    }

    /**
     * Escape HTML special characters
     * @param {string} text - Text to escape
     * @returns {string} Escaped text
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // ========================================
    // AJAX CART SYSTEM
    // ========================================

    /**
     * Add item to cart via AJAX
     * @param {number|string} productId - Product ID
     * @param {number} quantity - Quantity to add (default: 1)
     */
    function addToCart(productId, quantity = 1) {
        if (!productId) {
            showToast('Invalid product', 'error');
            return;
        }

        // Validate quantity
        quantity = Math.max(CONFIG.QTY_MIN, Math.min(CONFIG.QTY_MAX, parseInt(quantity) || 1));

        fetch('/cart/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                product_id: productId,
                quantity: quantity
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast(`Added to cart (${quantity}x)`, 'success');
                updateCartBadge();
            } else {
                showToast(data.message || 'Failed to add to cart', 'error');
            }
        })
        .catch(error => {
            logError('Add to cart error: ' + error);
            showToast('Error adding to cart', 'error');
        });
    }

    /**
     * Update item quantity in cart
     * @param {number|string} productId - Product ID
     * @param {number} quantity - New quantity
     */
    function updateCartQuantity(productId, quantity) {
        if (!productId) return;

        quantity = Math.max(CONFIG.QTY_MIN, Math.min(CONFIG.QTY_MAX, parseInt(quantity) || 1));

        fetch('/cart/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                product_id: productId,
                quantity: quantity
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Reload cart page or update item total
                const itemElement = document.querySelector(`[data-product-id="${productId}"]`);
                if (itemElement) {
                    const priceEl = itemElement.querySelector('.item-price');
                    const unitPrice = parseFloat(priceEl?.dataset.unitPrice || 0);
                    const totalEl = itemElement.querySelector('.item-total');
                    if (totalEl && unitPrice) {
                        totalEl.textContent = (unitPrice * quantity).toFixed(2);
                    }
                }
                updateCartBadge();
            } else {
                showToast(data.message || 'Failed to update cart', 'error');
            }
        })
        .catch(error => {
            logError('Update cart error: ' + error);
            showToast('Error updating cart', 'error');
        });
    }

    /**
     * Remove item from cart
     * @param {number|string} productId - Product ID
     */
    function removeFromCart(productId) {
        if (!productId) return;

        fetch(`/cart/remove/${productId}`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('Removed from cart', 'success');

                // Remove cart item element from DOM
                const itemElement = document.querySelector(`[data-product-id="${productId}"]`);
                if (itemElement) {
                    itemElement.style.opacity = '0';
                    setTimeout(() => itemElement.remove(), 300);
                }

                updateCartBadge();
            } else {
                showToast(data.message || 'Failed to remove item', 'error');
            }
        })
        .catch(error => {
            logError('Remove from cart error: ' + error);
            showToast('Error removing item', 'error');
        });
    }

    /**
     * Update cart badge count
     */
    function updateCartBadge() {
        fetch('/cart/count')
            .then(response => response.json())
            .then(data => {
                const badges = document.querySelectorAll('.cart-badge');
                badges.forEach(badge => {
                    badge.textContent = data.count || 0;
                    badge.style.display = data.count > 0 ? 'inline-block' : 'none';
                });
            })
            .catch(error => logError('Update badge error: ' + error));
    }

    /**
     * Get CSRF token from meta tag
     * @returns {string} CSRF token
     */
    function getCsrfToken() {
        return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    }

    // ========================================
    // LIVE SEARCH SYSTEM
    // ========================================

    const searchInput = document.getElementById('searchInput');
    const searchResults = document.getElementById('searchResults');

    if (searchInput && searchResults) {
        // Debounced search handler
        const performSearch = debounce(function(query) {
            if (query.length < CONFIG.SEARCH_MIN_CHARS) {
                searchResults.style.display = 'none';
                return;
            }

            fetch(`/api/search?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    searchResults.innerHTML = '';

                    if (!data.results || data.results.length === 0) {
                        searchResults.innerHTML = `
                            <div class="dropdown-item text-muted">
                                No results found
                            </div>
                        `;
                    } else {
                        data.results.forEach(product => {
                            const resultEl = document.createElement('a');
                            resultEl.href = product.url || '#';
                            resultEl.className = 'dropdown-item d-flex align-items-center';
                            resultEl.innerHTML = `
                                <img src="${escapeHtml(product.image)}" alt="${escapeHtml(product.name)}" style="width: 40px; height: 40px; object-fit: cover; margin-right: 10px; border-radius: 4px;">
                                <div style="flex: 1; min-width: 0;">
                                    <div class="text-truncate">${escapeHtml(product.name)}</div>
                                    <small class="text-muted">Rs. ${parseFloat(product.price).toFixed(2)}</small>
                                </div>
                            `;
                            searchResults.appendChild(resultEl);
                        });
                    }

                    searchResults.style.display = 'block';
                })
                .catch(error => {
                    logError('Search error: ' + error);
                    searchResults.innerHTML = '<div class="dropdown-item text-danger">Error loading results</div>';
                    searchResults.style.display = 'block';
                });
        }, CONFIG.SEARCH_DEBOUNCE_MS);

        // Input event listener
        searchInput.addEventListener('input', function() {
            performSearch(this.value.trim());
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!e.target.closest('#searchInput') && !e.target.closest('#searchResults')) {
                searchResults.style.display = 'none';
            }
        });

        // Keep dropdown open when clicking inside
        searchResults.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    }

    // ========================================
    // WISHLIST SYSTEM (localStorage)
    // ========================================

    /**
     * Get wishlist from localStorage
     * @returns {array} Array of product IDs
     */
    function getWishlist() {
        const wishlist = localStorage.getItem(CONFIG.WISHLIST_STORAGE_KEY);
        return safeJsonParse(wishlist, []);
    }

    /**
     * Save wishlist to localStorage
     * @param {array} wishlist - Wishlist array
     */
    function saveWishlist(wishlist) {
        localStorage.setItem(CONFIG.WISHLIST_STORAGE_KEY, JSON.stringify(wishlist));
    }

    /**
     * Check if product is in wishlist
     * @param {number|string} productId - Product ID
     * @returns {boolean} True if in wishlist
     */
    function isInWishlist(productId) {
        return getWishlist().includes(productId.toString());
    }

    /**
     * Toggle product in wishlist
     * @param {number|string} productId - Product ID
     * @returns {boolean} True if added, false if removed
     */
    function toggleWishlist(productId) {
        productId = productId.toString();
        const wishlist = getWishlist();
        const index = wishlist.indexOf(productId);

        if (index > -1) {
            wishlist.splice(index, 1);
            showToast('Removed from wishlist', 'success');
            return false;
        } else {
            wishlist.push(productId);
            showToast('Added to wishlist', 'success');
            return true;
        }

        saveWishlist(wishlist);
    }

    /**
     * Update wishlist icons across page
     */
    function updateWishlistIcons() {
        document.querySelectorAll('.wishlist-btn').forEach(btn => {
            const productId = btn.dataset.productId;
            if (isInWishlist(productId)) {
                btn.classList.add('active');
                btn.setAttribute('aria-pressed', 'true');
            } else {
                btn.classList.remove('active');
                btn.setAttribute('aria-pressed', 'false');
            }
        });
    }

    /**
     * Update wishlist count badge
     */
    function updateWishlistCount() {
        const badges = document.querySelectorAll('.wishlist-badge');
        const count = getWishlist().length;
        badges.forEach(badge => {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'inline-block' : 'none';
        });
    }

    // Initialize wishlist on page load
    updateWishlistIcons();
    updateWishlistCount();

    // Wishlist button click handler
    document.addEventListener('click', function(e) {
        if (e.target.closest('.wishlist-btn')) {
            const btn = e.target.closest('.wishlist-btn');
            const productId = btn.dataset.productId;
            if (productId) {
                toggleWishlist(productId);
                updateWishlistIcons();
                updateWishlistCount();
            }
        }
    });

    // ========================================
    // RECENTLY VIEWED SYSTEM (localStorage)
    // ========================================

    /**
     * Get recently viewed products
     * @returns {array} Array of recently viewed products
     */
    function getRecentlyViewed() {
        const items = localStorage.getItem(CONFIG.RECENTLY_VIEWED_STORAGE_KEY);
        return safeJsonParse(items, []);
    }

    /**
     * Add product to recently viewed
     * @param {number|string} productId - Product ID
     * @param {string} name - Product name
     * @param {string} image - Product image URL
     * @param {number} price - Product price
     * @param {string} url - Product URL
     */
    function addToRecentlyViewed(productId, name, image, price, url) {
        productId = productId.toString();
        let items = getRecentlyViewed();

        // Remove duplicate if exists
        items = items.filter(item => item.id !== productId);

        // Add to beginning
        items.unshift({
            id: productId,
            name: name,
            image: image,
            price: price,
            url: url,
            timestamp: Date.now()
        });

        // Keep only last N items
        items = items.slice(0, CONFIG.RECENTLY_VIEWED_LIMIT);

        localStorage.setItem(CONFIG.RECENTLY_VIEWED_STORAGE_KEY, JSON.stringify(items));
    }

    /**
     * Render recently viewed products
     */
    function renderRecentlyViewed() {
        const container = document.getElementById('recentlyViewed');
        if (!container) return;

        const items = getRecentlyViewed();
        if (items.length === 0) {
            container.innerHTML = '<p class="text-muted">No recently viewed products</p>';
            return;
        }

        let html = '';
        items.forEach(item => {
            html += `
                <div class="col-md-4 col-lg-3 mb-3">
                    <div class="card h-100">
                        <img src="${escapeHtml(item.image)}" class="card-img-top" alt="${escapeHtml(item.name)}" style="height: 200px; object-fit: cover;">
                        <div class="card-body">
                            <h6 class="card-title text-truncate">
                                <a href="${escapeHtml(item.url)}" class="text-decoration-none">${escapeHtml(item.name)}</a>
                            </h6>
                            <p class="card-text text-primary fw-bold">Rs. ${parseFloat(item.price).toFixed(2)}</p>
                            <a href="${escapeHtml(item.url)}" class="btn btn-sm btn-outline-primary w-100">View Product</a>
                        </div>
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;
    }

    // Render recently viewed on page load
    renderRecentlyViewed();

    // ========================================
    // LAZY LOADING IMAGES
    // ========================================

    /**
     * Initialize lazy loading images
     */
    function initLazyLoading() {
        // Check if IntersectionObserver is supported
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver(function(entries, observer) {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        const src = img.dataset.src;

                        if (src) {
                            img.src = src;
                            img.classList.add('loaded');
                            observer.unobserve(img);
                        }
                    }
                });
            }, {
                rootMargin: '50px'
            });

            document.querySelectorAll(`.${CONFIG.LAZY_IMG_CLASS}`).forEach(img => {
                imageObserver.observe(img);
            });
        } else {
            // Fallback for browsers without IntersectionObserver
            document.querySelectorAll(`.${CONFIG.LAZY_IMG_CLASS}`).forEach(img => {
                if (img.dataset.src) {
                    img.src = img.dataset.src;
                    img.classList.add('loaded');
                }
            });
        }
    }

    // Initialize lazy loading
    initLazyLoading();

    // ========================================
    // BACK TO TOP BUTTON
    // ========================================

    const backToTopBtn = document.getElementById('backToTop');
    if (backToTopBtn) {
        window.addEventListener('scroll', function() {
            if (window.pageYOffset > CONFIG.BACK_TO_TOP_THRESHOLD_PX) {
                backToTopBtn.style.display = 'block';
            } else {
                backToTopBtn.style.display = 'none';
            }
        });

        backToTopBtn.addEventListener('click', function() {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }

    // ========================================
    // NAVBAR SCROLL EFFECT
    // ========================================

    const navbar = document.querySelector('nav.navbar');
    if (navbar) {
        window.addEventListener('scroll', function() {
            if (window.pageYOffset > CONFIG.SCROLL_THRESHOLD_PX) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        });
    }

    // ========================================
    // QUANTITY SELECTOR
    // ========================================

    /**
     * Initialize quantity selectors
     */
    function initQuantitySelectors() {
        document.addEventListener('click', function(e) {
            // Handle plus button
            if (e.target.closest('.qty-plus')) {
                const input = e.target.closest('.qty-selector')?.querySelector('.qty-input');
                if (input) {
                    let value = parseInt(input.value) || CONFIG.QTY_MIN;
                    value = Math.min(value + 1, CONFIG.QTY_MAX);
                    input.value = value;
                    triggerQuantityChange(input);
                }
            }

            // Handle minus button
            if (e.target.closest('.qty-minus')) {
                const input = e.target.closest('.qty-selector')?.querySelector('.qty-input');
                if (input) {
                    let value = parseInt(input.value) || CONFIG.QTY_MIN;
                    value = Math.max(value - 1, CONFIG.QTY_MIN);
                    input.value = value;
                    triggerQuantityChange(input);
                }
            }
        });

        // Direct input validation
        document.querySelectorAll('.qty-input').forEach(input => {
            input.addEventListener('change', function() {
                let value = parseInt(this.value) || CONFIG.QTY_MIN;
                value = Math.max(CONFIG.QTY_MIN, Math.min(value, CONFIG.QTY_MAX));
                this.value = value;
                triggerQuantityChange(this);
            });

            // Prevent non-numeric input
            input.addEventListener('input', function() {
                this.value = this.value.replace(/[^\d]/g, '');
            });
        });
    }

    /**
     * Trigger quantity change event
     * @param {HTMLElement} input - Quantity input element
     */
    function triggerQuantityChange(input) {
        const event = new CustomEvent('quantityChanged', {
            detail: { quantity: parseInt(input.value) }
        });
        input.dispatchEvent(event);

        // If in cart, update the cart
        const cartItem = input.closest('[data-product-id]');
        if (cartItem) {
            const productId = cartItem.dataset.productId;
            const quantity = parseInt(input.value);
            updateCartQuantity(productId, quantity);
        }
    }

    initQuantitySelectors();

    // ========================================
    // PRODUCT IMAGE GALLERY
    // ========================================

    /**
     * Initialize product image gallery
     */
    function initImageGallery() {
        const mainImage = document.querySelector('.product-main-image');
        const thumbnails = document.querySelectorAll('.product-thumbnail');

        if (mainImage && thumbnails.length > 0) {
            thumbnails.forEach(thumbnail => {
                thumbnail.addEventListener('click', function() {
                    // Remove active class from all thumbnails
                    thumbnails.forEach(t => t.classList.remove('active'));

                    // Add active class to clicked thumbnail
                    this.classList.add('active');

                    // Change main image
                    const src = this.dataset.src || this.src;
                    mainImage.style.opacity = '0.5';
                    mainImage.src = src;
                    mainImage.onload = function() {
                        this.style.opacity = '1';
                    };
                });
            });

            // Set first thumbnail as active
            if (thumbnails.length > 0) {
                thumbnails[0].classList.add('active');
            }
        }
    }

    initImageGallery();

    // ========================================
    // STAR RATING INPUT
    // ========================================

    /**
     * Initialize star rating input
     */
    function initStarRating() {
        document.addEventListener('click', function(e) {
            const star = e.target.closest('.star-rating-input .star');
            if (star) {
                const container = star.closest('.star-rating-input');
                const stars = container?.querySelectorAll('.star');
                const index = Array.from(stars).indexOf(star);
                const ratingValue = index + 1;

                // Update hidden input
                const hiddenInput = container?.querySelector('input[type="hidden"]');
                if (hiddenInput) {
                    hiddenInput.value = ratingValue;
                }

                // Update star display
                stars.forEach((s, i) => {
                    if (i < ratingValue) {
                        s.classList.add('active');
                    } else {
                        s.classList.remove('active');
                    }
                });
            }
        });

        // Hover preview effect
        document.addEventListener('mouseover', function(e) {
            const star = e.target.closest('.star-rating-input .star');
            if (star) {
                const container = star.closest('.star-rating-input');
                const stars = container?.querySelectorAll('.star');
                const index = Array.from(stars).indexOf(star);

                stars.forEach((s, i) => {
                    if (i <= index) {
                        s.classList.add('hover');
                    } else {
                        s.classList.remove('hover');
                    }
                });
            }
        });

        document.addEventListener('mouseout', function(e) {
            const container = e.target.closest('.star-rating-input');
            if (container) {
                const stars = container.querySelectorAll('.star');
                stars.forEach(s => s.classList.remove('hover'));
            }
        });
    }

    initStarRating();

    // ========================================
    // PRODUCT FILTERS
    // ========================================

    /**
     * Filter products by category
     * @param {string} category - Category slug
     */
    function filterProducts(category) {
        if (!category) return;

        const params = new URLSearchParams(window.location.search);
        params.set('category', category);
        window.location.href = window.location.pathname + '?' + params.toString();
    }

    // Category filter links
    document.querySelectorAll('.category-filter').forEach(link => {
        link.addEventListener('click', function(e) {
            const category = this.dataset.category;
            if (category) {
                e.preventDefault();
                filterProducts(category);
            }
        });
    });

    // Sort dropdown
    const sortDropdown = document.querySelector('[name="sort"]');
    if (sortDropdown) {
        sortDropdown.addEventListener('change', function() {
            const params = new URLSearchParams(window.location.search);
            params.set('sort', this.value);
            window.location.href = window.location.pathname + '?' + params.toString();
        });
    }

    // Price range filter
    const priceRangeInputs = document.querySelectorAll('input[name="price_min"], input[name="price_max"]');
    if (priceRangeInputs.length > 0) {
        const filterBtn = document.querySelector('[data-action="apply-filters"]');
        if (filterBtn) {
            filterBtn.addEventListener('click', function() {
                const priceMin = document.querySelector('input[name="price_min"]')?.value || '';
                const priceMax = document.querySelector('input[name="price_max"]')?.value || '';

                const params = new URLSearchParams(window.location.search);
                if (priceMin) params.set('price_min', priceMin);
                if (priceMax) params.set('price_max', priceMax);

                window.location.href = window.location.pathname + '?' + params.toString();
            });
        }
    }

    // ========================================
    // FORM VALIDATION ENHANCEMENT
    // ========================================

    /**
     * Initialize Bootstrap 5 form validation
     */
    function initFormValidation() {
        const forms = document.querySelectorAll('.needs-validation');

        forms.forEach(form => {
            form.addEventListener('submit', function(e) {
                if (!form.checkValidity() === false) {
                    e.preventDefault();
                    e.stopPropagation();
                }
                form.classList.add('was-validated');
            });
        });
    }

    /**
     * Validate Indian phone number format
     * @param {string} phone - Phone number
     * @returns {boolean} True if valid
     */
    function validateIndianPhone(phone) {
        const regex = /^[6-9]\d{9}$/;
        return regex.test(phone.replace(/\D/g, ''));
    }

    /**
     * Validate email format
     * @param {string} email - Email address
     * @returns {boolean} True if valid
     */
    function validateEmail(email) {
        const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return regex.test(email);
    }

    // Custom phone validation
    document.querySelectorAll('input[type="tel"]').forEach(input => {
        input.addEventListener('blur', function() {
            if (this.value && !validateIndianPhone(this.value)) {
                this.classList.add('is-invalid');
                this.classList.remove('is-valid');
            } else if (this.value) {
                this.classList.add('is-valid');
                this.classList.remove('is-invalid');
            }
        });
    });

    // Custom email validation
    document.querySelectorAll('input[type="email"]').forEach(input => {
        input.addEventListener('blur', function() {
            if (this.value && !validateEmail(this.value)) {
                this.classList.add('is-invalid');
                this.classList.remove('is-valid');
            } else if (this.value) {
                this.classList.add('is-valid');
                this.classList.remove('is-invalid');
            }
        });
    });

    initFormValidation();

    // ========================================
    // SLUG AUTO-GENERATION
    // ========================================

    /**
     * Generate slug from text
     * @param {string} text - Text to slugify
     * @returns {string} Slugified text
     */
    function generateSlug(text) {
        return text
            .toLowerCase()
            .trim()
            .replace(/[^\w\s-]/g, '')
            .replace(/[\s_-]+/g, '-')
            .replace(/^-+|-+$/g, '');
    }

    const productNameInput = document.getElementById('productName');
    const productSlugInput = document.getElementById('productSlug');

    if (productNameInput && productSlugInput) {
        productNameInput.addEventListener('input', function() {
            productSlugInput.value = generateSlug(this.value);
        });
    }

    // ========================================
    // IMAGE PREVIEW
    // ========================================

    /**
     * Initialize image previews
     */
    function initImagePreview() {
        document.addEventListener('change', function(e) {
            if (e.target.matches('input[type="file"]')) {
                const input = e.target;
                const preview = input.closest('form')?.querySelector('.image-preview');

                if (!preview || !input.files[0]) return;

                const reader = new FileReader();
                reader.onload = function(event) {
                    preview.src = event.target.result;
                    preview.style.display = 'block';
                    preview.style.maxWidth = '200px';
                    preview.style.marginTop = '10px';
                    preview.style.borderRadius = '4px';
                };

                reader.readAsDataURL(input.files[0]);
            }
        });
    }

    initImagePreview();

    // ========================================
    // CONFIRM DELETE
    // ========================================

    /**
     * Initialize delete confirmation
     */
    function initConfirmDelete() {
        document.addEventListener('click', function(e) {
            if (e.target.closest('.btn-delete')) {
                e.preventDefault();
                const btn = e.target.closest('.btn-delete');
                const itemName = btn.dataset.itemName || 'this item';

                if (confirm(`Are you sure you want to delete ${itemName}? This action cannot be undone.`)) {
                    // If it's a form submit
                    if (btn.type === 'submit') {
                        btn.closest('form').submit();
                    } else if (btn.href) {
                        // If it's a link
                        window.location.href = btn.href;
                    }
                }
            }
        });
    }

    initConfirmDelete();

    // ========================================
    // STATS COUNTER ANIMATION
    // ========================================

    /**
     * Initialize stats counter animation
     */
    function initStatsCounter() {
        const counters = document.querySelectorAll('.stat-counter');
        if (counters.length === 0) return;

        const counterObserver = new IntersectionObserver(function(entries, observer) {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const counter = entry.target;
                    const finalValue = parseInt(counter.dataset.value) || 0;
                    const duration = 1500; // 1.5 seconds
                    const increment = finalValue / (duration / 50);

                    let currentValue = 0;
                    const timer = setInterval(() => {
                        currentValue += increment;
                        if (currentValue >= finalValue) {
                            currentValue = finalValue;
                            clearInterval(timer);
                        }
                        counter.textContent = Math.floor(currentValue).toLocaleString();
                    }, 50);

                    observer.unobserve(counter);
                }
            });
        }, {
            threshold: 0.5
        });

        counters.forEach(counter => counterObserver.observe(counter));
    }

    initStatsCounter();

    // ========================================
    // INITIALIZATION COMPLETE
    // ========================================

    // Initialize cart badge on load
    updateCartBadge();

    // Expose functions to global scope for HTML inline calls
    window.printcraft = {
        addToCart,
        updateCartQuantity,
        removeFromCart,
        updateCartBadge,
        toggleWishlist,
        isInWishlist,
        getWishlist,
        updateWishlistIcons,
        updateWishlistCount,
        addToRecentlyViewed,
        getRecentlyViewed,
        renderRecentlyViewed,
        showToast,
        filterProducts,
        generateSlug,
        validateIndianPhone,
        validateEmail
    };

    // Log ready state
    console.log('[PrintCraft 3D] Application initialized successfully');

}); // End DOMContentLoaded
