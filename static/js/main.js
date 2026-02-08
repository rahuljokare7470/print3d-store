/**
 * PrintCraft 3D - Main JavaScript File
 * ======================================
 *
 * This file handles all the interactive functionality:
 * - Add to Cart (AJAX - no page reload)
 * - Cart quantity updates
 * - Product image gallery
 * - WhatsApp integration
 * - Toast notifications
 * - Search functionality
 *
 * HOW AJAX WORKS (Simple Explanation):
 * When you click "Add to Cart", instead of reloading the entire page,
 * JavaScript sends the data to the server in the background (using fetch)
 * and updates just the cart badge. This is faster and smoother!
 */

// Wait for the page to fully load before running scripts
document.addEventListener('DOMContentLoaded', function () {

    // ═══════════════════════════════════════════════════════════
    // ADD TO CART (AJAX)
    // ═══════════════════════════════════════════════════════════

    /**
     * Handle "Add to Cart" button clicks without reloading the page.
     *
     * How it works:
     * 1. User clicks the "Add to Cart" button
     * 2. JavaScript captures the click event
     * 3. Sends the product data to /cart/add via POST
     * 4. Server adds to session cart and returns JSON
     * 5. JavaScript updates the cart badge number
     * 6. Shows a toast notification
     */
    document.querySelectorAll('.add-to-cart-form').forEach(function (form) {
        form.addEventListener('submit', function (e) {
            e.preventDefault();  // Stop the form from submitting normally

            var btn = form.querySelector('.btn-add-cart');
            var originalText = btn.innerHTML;

            // Show loading state
            btn.classList.add('btn-loading');
            btn.innerHTML = 'Adding...';

            // Get form data
            var formData = new FormData(form);

            // Send data to server using Fetch API
            fetch('/cart/add', {
                method: 'POST',
                body: formData,
            })
            .then(function (response) { return response.json(); })
            .then(function (data) {
                if (data.success) {
                    // Update cart badge
                    updateCartBadge(data.cart_count);

                    // Show success notification
                    showToast(data.message, 'success');

                    // Reset button
                    btn.classList.remove('btn-loading');
                    btn.innerHTML = '<i class="fas fa-check"></i> Added!';

                    // Restore original text after 2 seconds
                    setTimeout(function () {
                        btn.innerHTML = originalText;
                    }, 2000);
                }
            })
            .catch(function (error) {
                console.error('Error adding to cart:', error);
                btn.classList.remove('btn-loading');
                btn.innerHTML = originalText;
                showToast('Failed to add to cart. Please try again.', 'danger');
            });
        });
    });


    // ═══════════════════════════════════════════════════════════
    // CART BADGE UPDATE
    // ═══════════════════════════════════════════════════════════

    /**
     * Update the cart icon badge number in the navbar.
     * Called after adding items to cart.
     */
    function updateCartBadge(count) {
        var badges = document.querySelectorAll('.cart-count-badge');
        badges.forEach(function (badge) {
            badge.textContent = count;
            if (count > 0) {
                badge.style.display = 'inline-block';
                // Add a little bounce animation
                badge.style.transform = 'scale(1.3)';
                setTimeout(function () {
                    badge.style.transform = 'scale(1)';
                }, 200);
            } else {
                badge.style.display = 'none';
            }
        });
    }


    // ═══════════════════════════════════════════════════════════
    // TOAST NOTIFICATIONS
    // ═══════════════════════════════════════════════════════════

    /**
     * Show a temporary notification message.
     *
     * @param {string} message - The text to display
     * @param {string} type    - 'success', 'danger', 'warning', 'info'
     */
    function showToast(message, type) {
        type = type || 'info';

        // Create toast container if it doesn't exist
        var container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
        }

        // Create the toast element
        var toast = document.createElement('div');
        toast.className = 'alert alert-' + type + ' alert-dismissible fade show shadow-sm';
        toast.style.cssText = 'min-width: 280px; animation: fadeInUp 0.3s ease;';
        toast.setAttribute('role', 'alert');

        // Icon based on type
        var icons = {
            success: 'fas fa-check-circle',
            danger: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };

        toast.innerHTML =
            '<i class="' + (icons[type] || icons.info) + ' me-2"></i>' +
            message +
            '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>';

        container.appendChild(toast);

        // Auto-remove after 4 seconds
        setTimeout(function () {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100px)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(function () {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, 4000);
    }


    // ═══════════════════════════════════════════════════════════
    // PRODUCT IMAGE GALLERY
    // ═══════════════════════════════════════════════════════════

    /**
     * Product detail page: Click thumbnails to change main image.
     */
    var mainImage = document.getElementById('main-product-image');
    var thumbnails = document.querySelectorAll('.product-thumbnails .thumb');

    thumbnails.forEach(function (thumb) {
        thumb.addEventListener('click', function () {
            // Get the full-size image URL from data attribute
            var newSrc = this.getAttribute('data-full');
            if (mainImage && newSrc) {
                mainImage.src = newSrc;

                // Update active state
                thumbnails.forEach(function (t) { t.classList.remove('active'); });
                this.classList.add('active');
            }
        });
    });


    // ═══════════════════════════════════════════════════════════
    // QUANTITY CONTROLS
    // ═══════════════════════════════════════════════════════════

    /**
     * Plus/minus buttons for quantity on product detail and cart pages.
     */
    document.querySelectorAll('.qty-btn-minus').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var input = this.parentElement.querySelector('.qty-input');
            var current = parseInt(input.value) || 1;
            if (current > 1) {
                input.value = current - 1;
            }
        });
    });

    document.querySelectorAll('.qty-btn-plus').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var input = this.parentElement.querySelector('.qty-input');
            var current = parseInt(input.value) || 1;
            var max = parseInt(input.getAttribute('max')) || 10;
            if (current < max) {
                input.value = current + 1;
            }
        });
    });


    // ═══════════════════════════════════════════════════════════
    // WHATSAPP INTEGRATION
    // ═══════════════════════════════════════════════════════════

    /**
     * Build WhatsApp cart message and open WhatsApp.
     * Used on the cart page "Order via WhatsApp" button.
     */
    var whatsappCartBtn = document.getElementById('whatsapp-cart-btn');
    if (whatsappCartBtn) {
        whatsappCartBtn.addEventListener('click', function (e) {
            e.preventDefault();

            var whatsappNumber = this.getAttribute('data-phone');
            var cartItems = document.querySelectorAll('.cart-item-row');
            var message = 'Hi! I would like to order the following items:\n\n';

            cartItems.forEach(function (row) {
                var name = row.getAttribute('data-name');
                var qty = row.getAttribute('data-qty');
                var price = row.getAttribute('data-price');
                message += '• ' + name + ' x' + qty + ' = Rs.' + price + '\n';
            });

            var totalEl = document.getElementById('cart-grand-total');
            if (totalEl) {
                message += '\nTotal: Rs.' + totalEl.textContent.trim() + '\n';
            }

            message += '\nPlease confirm availability and share payment details. Thank you!';

            var encodedMsg = encodeURIComponent(message);
            var url = 'https://wa.me/' + whatsappNumber + '?text=' + encodedMsg;
            window.open(url, '_blank');
        });
    }


    // ═══════════════════════════════════════════════════════════
    // PRODUCT FILTERS (Product Gallery Page)
    // ═══════════════════════════════════════════════════════════

    /**
     * Handle sort dropdown change on products page.
     */
    var sortSelect = document.getElementById('sort-select');
    if (sortSelect) {
        sortSelect.addEventListener('change', function () {
            var url = new URL(window.location.href);
            url.searchParams.set('sort', this.value);
            window.location.href = url.toString();
        });
    }

    /**
     * Price range filter form.
     */
    var priceFilterForm = document.getElementById('price-filter-form');
    if (priceFilterForm) {
        priceFilterForm.addEventListener('submit', function (e) {
            e.preventDefault();
            var url = new URL(window.location.href);
            var minPrice = document.getElementById('filter-min-price').value;
            var maxPrice = document.getElementById('filter-max-price').value;

            if (minPrice) url.searchParams.set('min_price', minPrice);
            else url.searchParams.delete('min_price');

            if (maxPrice) url.searchParams.set('max_price', maxPrice);
            else url.searchParams.delete('max_price');

            window.location.href = url.toString();
        });
    }


    // ═══════════════════════════════════════════════════════════
    // IMAGE UPLOAD PREVIEW (Admin)
    // ═══════════════════════════════════════════════════════════

    /**
     * Show a preview of uploaded images in the admin product form.
     */
    document.querySelectorAll('.image-upload-input').forEach(function (input) {
        input.addEventListener('change', function () {
            var previewId = this.getAttribute('data-preview');
            var preview = document.getElementById(previewId);

            if (preview && this.files && this.files[0]) {
                var reader = new FileReader();
                reader.onload = function (e) {
                    preview.src = e.target.result;
                    preview.style.display = 'block';
                };
                reader.readAsDataURL(this.files[0]);
            }
        });
    });


    // ═══════════════════════════════════════════════════════════
    // DELETE CONFIRMATIONS (Admin)
    // ═══════════════════════════════════════════════════════════

    /**
     * Confirm before deleting products, orders, etc.
     */
    document.querySelectorAll('.confirm-delete').forEach(function (form) {
        form.addEventListener('submit', function (e) {
            var itemName = this.getAttribute('data-name') || 'this item';
            if (!confirm('Are you sure you want to delete ' + itemName + '? This cannot be undone.')) {
                e.preventDefault();
            }
        });
    });


    // ═══════════════════════════════════════════════════════════
    // SCROLL ANIMATIONS
    // ═══════════════════════════════════════════════════════════

    /**
     * Fade in elements as they scroll into view.
     * Elements with class 'animate-on-scroll' will fade in.
     */
    var animateElements = document.querySelectorAll('.animate-on-scroll');
    if (animateElements.length > 0) {
        var observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });

        animateElements.forEach(function (el) { observer.observe(el); });
    }


    // ═══════════════════════════════════════════════════════════
    // NAVBAR SCROLL EFFECT
    // ═══════════════════════════════════════════════════════════

    /**
     * Add shadow to navbar when scrolled down.
     */
    var navbar = document.querySelector('.navbar');
    if (navbar) {
        window.addEventListener('scroll', function () {
            if (window.scrollY > 50) {
                navbar.style.boxShadow = '0 2px 20px rgba(0, 0, 0, 0.1)';
            } else {
                navbar.style.boxShadow = '0 2px 15px rgba(0, 0, 0, 0.05)';
            }
        });
    }


    // ═══════════════════════════════════════════════════════════
    // AUTO-DISMISS FLASH MESSAGES
    // ═══════════════════════════════════════════════════════════

    /**
     * Auto-dismiss Bootstrap alerts after 5 seconds.
     */
    document.querySelectorAll('.alert-auto-dismiss').forEach(function (alert) {
        setTimeout(function () {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });


    // ═══════════════════════════════════════════════════════════
    // BACK TO TOP BUTTON (Optional Enhancement)
    // ═══════════════════════════════════════════════════════════

    // Create "Back to Top" button dynamically
    var backToTop = document.createElement('button');
    backToTop.id = 'back-to-top';
    backToTop.innerHTML = '<i class="fas fa-chevron-up"></i>';
    backToTop.style.cssText =
        'position:fixed; bottom:95px; right:28px; width:44px; height:44px;' +
        'border-radius:50%; background:var(--primary); color:#fff; border:none;' +
        'cursor:pointer; display:none; z-index:999; font-size:0.9rem;' +
        'box-shadow:0 2px 10px rgba(0,0,0,0.2); transition:all 0.3s ease;';
    document.body.appendChild(backToTop);

    backToTop.addEventListener('click', function () {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    window.addEventListener('scroll', function () {
        if (window.scrollY > 500) {
            backToTop.style.display = 'flex';
            backToTop.style.alignItems = 'center';
            backToTop.style.justifyContent = 'center';
        } else {
            backToTop.style.display = 'none';
        }
    });

});
