"""
PrintCraft 3D - E-Commerce Web Application (v2.0)
==================================================

This is the upgraded main application file with:
- All existing routes preserved (home, products, cart, checkout, admin, etc.)
- New payment integration (Razorpay)
- Product reviews system
- Search API for AJAX
- Wishlist functionality
- Improved image compression
- GZip compression middleware
- Security headers (CSP, X-Frame-Options, etc.)
- Rate limiting on contact and login forms
- Customer recommendations

HOW FLASK WORKS (Simple Explanation):
1. A user visits a URL (e.g., /products)
2. Flask finds the matching "route" (function decorated with @app.route)
3. The function processes the request and returns HTML
4. The HTML is generated from a "template" (Jinja2 HTML file)

TO RUN THIS APPLICATION:
    python app.py
    Then open http://localhost:5000 in your browser

Author: Rj (Built with guidance)
"""

import os
import re
import uuid
import json
import logging
from datetime import datetime, timedelta
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, jsonify, abort, send_from_directory, make_response
)
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, current_user
)
from flask_mail import Mail, Message
from flask_compress import Compress
from werkzeug.utils import secure_filename

# Import our database models and config
from models import (
    db, AdminUser, Category, Product, Order, OrderItem,
    Inquiry, SiteSetting, Review, WishlistItem
)
from config import Config

# Try to import Razorpay for payment integration
try:
    import razorpay
    RAZORPAY_AVAILABLE = True
except ImportError:
    RAZORPAY_AVAILABLE = False
    print("⚠️  Razorpay not installed. Payment integration disabled.")
    print("   Install with: pip install razorpay")

# Try to import Pillow for image optimization
try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    print("⚠️  Pillow not installed. Image optimization disabled.")
    print("   Install with: pip install Pillow")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# RATE LIMITING (Simple in-memory rate limiter)
# ═══════════════════════════════════════════════════════════════

class SimpleRateLimiter:
    """Simple in-memory rate limiter using timestamps."""
    def __init__(self):
        self.attempts = {}

    def is_allowed(self, key, max_attempts=5, window_seconds=300):
        """Check if an action is allowed under rate limits."""
        now = datetime.utcnow()
        if key not in self.attempts:
            self.attempts[key] = []

        # Remove old attempts outside the time window
        self.attempts[key] = [
            timestamp for timestamp in self.attempts[key]
            if (now - timestamp).total_seconds() < window_seconds
        ]

        # Check if under limit
        if len(self.attempts[key]) < max_attempts:
            self.attempts[key].append(now)
            return True
        return False

rate_limiter = SimpleRateLimiter()


# ═══════════════════════════════════════════════════════════════
# APP CREATION & SETUP
# ═══════════════════════════════════════════════════════════════

def create_app():
    """
    Factory function to create and configure the Flask application.
    Using a factory pattern makes testing and deployment easier.
    """
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    mail = Mail(app)

    # Initialize GZip compression
    compress = Compress()
    compress.init_app(app)

    # Set up login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'admin_login'
    login_manager.login_message = 'Please log in to access the admin panel.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        """Flask-Login uses this to reload the user from the session."""
        return AdminUser.query.get(int(user_id))

    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # ─── Security Headers (CSP, X-Frame-Options, etc.) ──────────────────
    @app.after_request
    def set_security_headers(response):
        """Add security headers to all responses."""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' fonts.googleapis.com cdnjs.cloudflare.com; "
            "font-src 'self' fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self'; "
            "frame-ancestors 'self';"
        )
        return response

    # ─── Template Context Processor ─────────────────────────────
    @app.context_processor
    def inject_globals():
        """
        Make these variables available in ALL templates automatically.
        No need to pass them in every render_template() call.
        """
        categories = Category.query.filter_by(is_active=True)\
            .order_by(Category.display_order).all()
        cart = session.get('cart', {})
        cart_count = sum(item.get('quantity', 0) for item in cart.values())
        cart_total = sum(
            item.get('price', 0) * item.get('quantity', 0)
            for item in cart.values()
        )
        unread_inquiries = Inquiry.query.filter_by(is_read=False).count()
        pending_orders = Order.query.filter(
            Order.order_status.in_(['pending', 'confirmed'])
        ).count()

        return dict(
            categories=categories,
            cart=cart,
            cart_count=cart_count,
            cart_total=cart_total,
            config=app.config,
            unread_inquiries=unread_inquiries,
            pending_orders=pending_orders,
            now=datetime.utcnow(),
        )

    # ═══════════════════════════════════════════════════════════
    # HELPER FUNCTIONS
    # ═══════════════════════════════════════════════════════════

    def slugify(text):
        """
        Convert text to URL-friendly slug.
        Example: "Desk Organiser Pro" → "desk-organiser-pro"
        """
        text = text.lower().strip()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[\s_]+', '-', text)
        text = re.sub(r'-+', '-', text)
        return text.strip('-')

    def allowed_file(filename):
        """Check if the uploaded file has an allowed extension."""
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

    def save_image(file):
        """
        Save and optimize an uploaded image.
        Returns the filename (not the full path).

        Steps:
        1. Generate a unique filename to avoid conflicts
        2. Save the file
        3. Optimize it (resize if too large, compress)
        4. Progressive quality reduction to hit size target
        """
        if not file or file.filename == '':
            return ''

        if not allowed_file(file.filename):
            flash('Invalid file type. Please upload PNG, JPG, or WebP.', 'danger')
            return ''

        # Generate unique filename: uuid_originalname.ext
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex[:8]}_{secure_filename(file.filename)}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Save the file
        file.save(filepath)

        # Optimize the image if Pillow is available
        if PILLOW_AVAILABLE:
            try:
                img = Image.open(filepath)

                # Convert RGBA to RGB (JPEG doesn't support transparency)
                if img.mode == 'RGBA':
                    bg = Image.new('RGB', img.size, (255, 255, 255))
                    bg.paste(img, mask=img.split()[3])
                    img = bg

                # Resize if larger than max width
                max_w = app.config.get('MAX_IMAGE_WIDTH', 1200)
                if img.width > max_w:
                    ratio = max_w / img.width
                    new_h = int(img.height * ratio)
                    img = img.resize((max_w, new_h), Image.LANCZOS)

                # Progressive quality reduction to hit target size
                max_kb = app.config.get('MAX_IMAGE_SIZE_KB', 150)
                quality = 90
                while quality > 30:
                    img.save(filepath, 'JPEG', quality=quality, optimize=True)
                    file_size_kb = os.path.getsize(filepath) / 1024
                    if file_size_kb <= max_kb:
                        break
                    quality -= 10

            except Exception as e:
                logger.warning(f"Image optimization failed: {e}")

        return filename

    def send_order_email(order):
        """Send order confirmation emails to the business and customer."""
        if not app.config.get('MAIL_USERNAME'):
            logger.info("Email not configured. Skipping email notification.")
            return

        try:
            # Build the items list for the email
            items_text = ""
            for item in order.items:
                items_text += f"  • {item.product_name} x{item.quantity} = ₹{item.line_total}\n"

            # Email to business owner
            owner_msg = Message(
                subject=f"New Order #{order.order_number}",
                recipients=[app.config['BUSINESS_EMAIL']],
                body=f"""New order received!

Order Number: {order.order_number}
Customer: {order.customer_name}
Phone: {order.customer_phone}
Email: {order.customer_email}
Address: {order.delivery_address}, {order.delivery_city} - {order.delivery_pincode}

Items:
{items_text}
Subtotal: ₹{order.subtotal}
Delivery: ₹{order.delivery_charge}
Total: ₹{order.total_amount}

Payment: {order.payment_method.upper()}
Notes: {order.special_instructions or 'None'}

Manage this order: {url_for('admin_order_detail', order_id=order.id, _external=True)}
"""
            )
            mail.send(owner_msg)

            # Email to customer
            if order.customer_email:
                customer_msg = Message(
                    subject=f"Order Confirmed - {order.order_number}",
                    recipients=[order.customer_email],
                    body=f"""Hi {order.customer_name}!

Thank you for your order with {app.config['BUSINESS_NAME']}!

Order Number: {order.order_number}

Items:
{items_text}
Subtotal: ₹{order.subtotal}
Delivery: ₹{order.delivery_charge}
Total: ₹{order.total_amount}

Payment Method: {order.payment_method.upper()}

We'll start working on your order soon. For any questions, contact us:
Email: {app.config['BUSINESS_EMAIL']}

Thank you for choosing {app.config['BUSINESS_NAME']}!
"""
                )
                mail.send(customer_msg)

        except Exception as e:
            logger.error(f"Email sending failed: {e}")

    # ═══════════════════════════════════════════════════════════
    # PUBLIC ROUTES (What customers see)
    # ═══════════════════════════════════════════════════════════

    @app.route('/')
    def home():
        """
        Homepage - Shows hero section and featured products.
        This is the first page visitors see.
        """
        featured_products = Product.query.filter_by(
            is_featured=True, is_active=True
        ).limit(8).all()

        latest_products = Product.query.filter_by(is_active=True)\
            .order_by(Product.created_at.desc()).limit(4).all()

        # Get all products for the homepage
        all_products = Product.query.filter_by(is_active=True)\
            .order_by(Product.created_at.desc()).all()

        return render_template('index.html',
                               featured_products=featured_products,
                               latest_products=latest_products,
                               all_products=all_products)

    @app.route('/products')
    def products():
        """
        Product gallery page with filtering and sorting.

        URL Parameters (from the browser URL):
            category - Filter by category slug (e.g., ?category=desk-accessories)
            sort     - Sort order (e.g., ?sort=price_low)
            min_price- Minimum price filter
            max_price- Maximum price filter
            search   - Search term
        """
        # Get filter parameters from the URL
        category_slug = request.args.get('category', '')
        sort_by = request.args.get('sort', 'newest')
        min_price = request.args.get('min_price', type=int)
        max_price = request.args.get('max_price', type=int)
        search = request.args.get('search', '').strip()

        # Start building the query
        query = Product.query.filter_by(is_active=True)

        # Apply category filter
        if category_slug:
            cat = Category.query.filter_by(slug=category_slug).first()
            if cat:
                query = query.filter_by(category_id=cat.id)

        # Apply price range filter
        if min_price is not None:
            query = query.filter(Product.price >= min_price)
        if max_price is not None:
            query = query.filter(Product.price <= max_price)

        # Apply search filter
        if search:
            query = query.filter(
                db.or_(
                    Product.name.ilike(f'%{search}%'),
                    Product.description.ilike(f'%{search}%'),
                )
            )

        # Apply sorting
        if sort_by == 'price_low':
            query = query.order_by(Product.price.asc())
        elif sort_by == 'price_high':
            query = query.order_by(Product.price.desc())
        elif sort_by == 'popular':
            # You would need to track views or sales for this
            query = query.order_by(Product.created_at.desc())
        elif sort_by == 'name':
            query = query.order_by(Product.name.asc())
        else:  # newest
            query = query.order_by(Product.created_at.desc())

        products_list = query.all()

        return render_template('products.html',
                               products=products_list,
                               current_category=category_slug,
                               current_sort=sort_by,
                               search_query=search,
                               min_price=min_price,
                               max_price=max_price)

    @app.route('/product/<slug>')
    def product_detail(slug):
        """
        Individual product page with full details and image gallery.

        The 'slug' parameter comes from the URL:
        e.g., /product/multipurpose-desk-organiser
        """
        product = Product.query.filter_by(slug=slug, is_active=True).first_or_404()

        # Get related products (same category, excluding current)
        related = Product.query.filter(
            Product.category_id == product.category_id,
            Product.id != product.id,
            Product.is_active == True
        ).limit(4).all()

        # Get products frequently ordered together (Customers also viewed)
        # Simple implementation: products from same category that were in same orders
        recommended = []
        if product.order_items:
            order_ids = [oi.order_id for oi in product.order_items]
            recommended = db.session.query(Product).join(OrderItem).filter(
                OrderItem.order_id.in_(order_ids),
                Product.id != product.id,
                Product.is_active == True
            ).distinct().limit(4).all()

        # Fallback to same category if no order history
        if not recommended:
            recommended = related

        # Get approved reviews for this product
        reviews = Review.query.filter_by(
            product_id=product.id, is_approved=True
        ).order_by(Review.created_at.desc()).all()

        # Check if product is in user's wishlist
        session_id = session.get('session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            session['session_id'] = session_id

        in_wishlist = WishlistItem.query.filter_by(
            session_id=session_id, product_id=product.id
        ).first() is not None

        return render_template('product_detail.html',
                               product=product,
                               related_products=related,
                               recommended_products=recommended,
                               reviews=reviews,
                               in_wishlist=in_wishlist)

    @app.route('/about')
    def about():
        """About Us page with business story and Google Maps."""
        return render_template('about.html')

    @app.route('/contact', methods=['GET', 'POST'])
    def contact():
        """
        Contact page with inquiry form.
        GET  = Show the form
        POST = Process the submitted form

        Rate limiting: Maximum 5 inquiries per 15 minutes per IP
        """
        if request.method == 'POST':
            # Rate limiting check
            client_ip = request.remote_addr
            if not rate_limiter.is_allowed(f"contact_{client_ip}", max_attempts=5, window_seconds=900):
                flash('Too many inquiries. Please wait 15 minutes before submitting again.', 'danger')
                return redirect(url_for('contact'))

            inquiry = Inquiry(
                name=request.form.get('name', '').strip(),
                email=request.form.get('email', '').strip(),
                phone=request.form.get('phone', '').strip(),
                subject=request.form.get('subject', 'General Inquiry').strip(),
                message=request.form.get('message', '').strip(),
            )

            if not inquiry.name or not inquiry.email or not inquiry.message:
                flash('Please fill in all required fields.', 'danger')
                return redirect(url_for('contact'))

            db.session.add(inquiry)
            db.session.commit()

            # Try to send email notification
            try:
                if app.config.get('MAIL_USERNAME'):
                    msg = Message(
                        subject=f"New Inquiry: {inquiry.subject}",
                        recipients=[app.config['BUSINESS_EMAIL']],
                        body=f"New inquiry from {inquiry.name} ({inquiry.email}):\n\n"
                             f"Phone: {inquiry.phone}\n"
                             f"Subject: {inquiry.subject}\n\n"
                             f"Message:\n{inquiry.message}"
                    )
                    mail.send(msg)
            except Exception as e:
                logger.error(f"Failed to send inquiry email: {e}")

            flash('Thank you for your message! We\'ll get back to you soon.', 'success')
            return redirect(url_for('contact'))

        return render_template('contact.html')

    # ═══════════════════════════════════════════════════════════
    # CART ROUTES (Shopping cart - uses browser session)
    # ═══════════════════════════════════════════════════════════

    @app.route('/cart')
    def cart():
        """Display the shopping cart page."""
        cart_data = session.get('cart', {})
        cart_items = []
        subtotal = 0

        for product_id, item in cart_data.items():
            product = Product.query.get(int(product_id))
            if product and product.is_active:
                item_total = product.price * item['quantity']
                subtotal += item_total
                cart_items.append({
                    'product': product,
                    'quantity': item['quantity'],
                    'color': item.get('color', ''),
                    'total': item_total,
                })

        delivery = 0 if subtotal >= app.config['FREE_DELIVERY_ABOVE'] else app.config['DELIVERY_CHARGE']
        grand_total = subtotal + delivery

        return render_template('cart.html',
                               cart_items=cart_items,
                               subtotal=subtotal,
                               delivery=delivery,
                               grand_total=grand_total)

    @app.route('/cart/add', methods=['POST'])
    def cart_add():
        """
        Add a product to the cart (called via AJAX from JavaScript).
        Returns JSON response for the frontend to update the cart icon.
        """
        product_id = request.form.get('product_id', type=int)
        quantity = request.form.get('quantity', 1, type=int)
        color = request.form.get('color', '')

        product = Product.query.get_or_404(product_id)

        cart = session.get('cart', {})
        pid = str(product_id)

        if pid in cart:
            cart[pid]['quantity'] += quantity
        else:
            cart[pid] = {
                'name': product.name,
                'price': product.price,
                'quantity': quantity,
                'color': color,
                'image': product.image_url,
            }

        session['cart'] = cart
        session.modified = True

        cart_count = sum(item['quantity'] for item in cart.values())
        return jsonify({
            'success': True,
            'message': f'{product.name} added to cart!',
            'cart_count': cart_count,
        })

    @app.route('/cart/update', methods=['POST'])
    def cart_update():
        """Update quantity of an item in the cart."""
        product_id = str(request.form.get('product_id', ''))
        quantity = request.form.get('quantity', 1, type=int)

        cart = session.get('cart', {})
        if product_id in cart:
            if quantity <= 0:
                del cart[product_id]
            else:
                cart[product_id]['quantity'] = quantity

        session['cart'] = cart
        session.modified = True
        return redirect(url_for('cart'))

    @app.route('/cart/remove/<product_id>')
    def cart_remove(product_id):
        """Remove an item from the cart."""
        cart = session.get('cart', {})
        if product_id in cart:
            del cart[product_id]
        session['cart'] = cart
        session.modified = True
        flash('Item removed from cart.', 'info')
        return redirect(url_for('cart'))

    @app.route('/cart/clear')
    def cart_clear():
        """Empty the entire cart."""
        session['cart'] = {}
        session.modified = True
        flash('Cart cleared.', 'info')
        return redirect(url_for('cart'))

    # ═══════════════════════════════════════════════════════════
    # CHECKOUT & ORDER ROUTES
    # ═══════════════════════════════════════════════════════════

    @app.route('/checkout', methods=['GET', 'POST'])
    def checkout():
        """
        Checkout page where customers enter delivery details.
        GET  = Show the checkout form
        POST = Process the order
        """
        cart_data = session.get('cart', {})
        if not cart_data:
            flash('Your cart is empty!', 'warning')
            return redirect(url_for('products'))

        if request.method == 'POST':
            # Calculate totals
            subtotal = 0
            order_items = []
            for pid, item in cart_data.items():
                product = Product.query.get(int(pid))
                if product:
                    item_total = product.price * item['quantity']
                    subtotal += item_total
                    order_items.append(OrderItem(
                        product_id=product.id,
                        product_name=product.name,
                        quantity=item['quantity'],
                        unit_price=product.price,
                    ))

            delivery = 0 if subtotal >= app.config['FREE_DELIVERY_ABOVE'] else app.config['DELIVERY_CHARGE']
            payment_method = request.form.get('payment_method', 'cod')

            # Create the order
            order = Order(
                order_number=Order.generate_order_number(),
                customer_name=request.form.get('name', '').strip(),
                customer_email=request.form.get('email', '').strip(),
                customer_phone=request.form.get('phone', '').strip(),
                delivery_address=request.form.get('address', '').strip(),
                delivery_city=request.form.get('city', 'Pune').strip(),
                delivery_pincode=request.form.get('pincode', '').strip(),
                subtotal=subtotal,
                delivery_charge=delivery,
                total_amount=subtotal + delivery,
                payment_method=payment_method,
                special_instructions=request.form.get('notes', '').strip(),
            )
            order.items = order_items

            # If Razorpay payment, store the order IDs
            if payment_method == 'razorpay':
                order.razorpay_order_id = request.form.get('razorpay_order_id', '')
                order.razorpay_payment_id = request.form.get('razorpay_payment_id', '')
                if order.razorpay_payment_id:
                    order.payment_status = 'paid'
                    order.order_status = 'confirmed'

            db.session.add(order)
            db.session.commit()

            # Send email notifications
            send_order_email(order)

            # Clear the cart
            session['cart'] = {}
            session.modified = True

            flash(f'Order placed successfully! Your order number is {order.order_number}', 'success')
            return redirect(url_for('order_confirmation', order_number=order.order_number))

        # GET: Show checkout form
        subtotal = sum(
            item['price'] * item['quantity'] for item in cart_data.values()
        )
        delivery = 0 if subtotal >= app.config['FREE_DELIVERY_ABOVE'] else app.config['DELIVERY_CHARGE']

        return render_template('checkout.html',
                               subtotal=subtotal,
                               delivery=delivery,
                               grand_total=subtotal + delivery,
                               razorpay_available=RAZORPAY_AVAILABLE,
                               razorpay_key=app.config.get('RAZORPAY_KEY_ID', ''))

    @app.route('/order/<order_number>')
    def order_confirmation(order_number):
        """Show order confirmation page after successful checkout."""
        order = Order.query.filter_by(order_number=order_number).first_or_404()
        return render_template('order_confirmation.html', order=order)

    # ═══════════════════════════════════════════════════════════
    # RAZORPAY PAYMENT ROUTES
    # ═══════════════════════════════════════════════════════════

    @app.route('/create-razorpay-order', methods=['POST'])
    def create_razorpay_order():
        """Create a Razorpay order for online payment."""
        if not RAZORPAY_AVAILABLE or not app.config.get('RAZORPAY_KEY_ID'):
            return jsonify({'error': 'Razorpay not configured'}), 400

        cart_data = session.get('cart', {})
        if not cart_data:
            return jsonify({'error': 'Cart is empty'}), 400

        # Calculate totals
        subtotal = sum(
            float(item['price']) * item['quantity'] for item in cart_data.values()
        )
        delivery = 0 if subtotal >= app.config['FREE_DELIVERY_ABOVE'] else app.config['DELIVERY_CHARGE']
        total = subtotal + delivery

        try:
            client = razorpay.Client(
                auth=(
                    app.config['RAZORPAY_KEY_ID'],
                    app.config['RAZORPAY_KEY_SECRET']
                )
            )
            order_data = {
                'amount': int(total * 100),  # Razorpay expects paise
                'currency': 'INR',
                'payment_capture': 1
            }
            razorpay_order = client.order.create(data=order_data)
            return jsonify({
                'order_id': razorpay_order['id'],
                'amount': int(total * 100),
                'currency': 'INR',
                'key_id': app.config['RAZORPAY_KEY_ID']
            })
        except Exception as e:
            logger.error(f"Razorpay order creation failed: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/verify-payment', methods=['POST'])
    def verify_payment():
        """Verify Razorpay payment signature and complete order."""
        if not RAZORPAY_AVAILABLE or not app.config.get('RAZORPAY_KEY_SECRET'):
            return jsonify({'error': 'Razorpay not configured'}), 400

        try:
            payment_id = request.json.get('razorpay_payment_id')
            order_id = request.json.get('razorpay_order_id')
            signature = request.json.get('razorpay_signature')

            client = razorpay.Client(
                auth=(
                    app.config['RAZORPAY_KEY_ID'],
                    app.config['RAZORPAY_KEY_SECRET']
                )
            )

            # Verify payment signature
            params_dict = {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }

            client.utility.verify_payment_signature(params_dict)

            return jsonify({
                'success': True,
                'message': 'Payment verified successfully',
                'payment_id': payment_id
            })

        except razorpay.BadRequestError as e:
            logger.error(f"Payment verification failed: {e}")
            return jsonify({'error': 'Payment verification failed'}), 400
        except Exception as e:
            logger.error(f"Verification error: {e}")
            return jsonify({'error': str(e)}), 500

    # ═══════════════════════════════════════════════════════════
    # PRODUCT REVIEW ROUTES
    # ═══════════════════════════════════════════════════════════

    @app.route('/product/<slug>/review', methods=['POST'])
    def add_review(slug):
        """Add a review to a product."""
        product = Product.query.filter_by(slug=slug, is_active=True).first_or_404()

        customer_name = request.form.get('customer_name', '').strip()
        customer_email = request.form.get('customer_email', '').strip()
        rating = request.form.get('rating', 5, type=int)
        title = request.form.get('title', '').strip()
        comment = request.form.get('comment', '').strip()

        # Validate input
        if not customer_name or not rating or not comment:
            flash('Please fill in all required fields.', 'danger')
            return redirect(url_for('product_detail', slug=slug))

        if rating < 1 or rating > 5:
            flash('Rating must be between 1 and 5.', 'danger')
            return redirect(url_for('product_detail', slug=slug))

        # Create review (pending approval by default)
        review = Review(
            product_id=product.id,
            customer_name=customer_name,
            customer_email=customer_email,
            rating=rating,
            title=title,
            comment=comment,
            is_approved=False  # Admin must approve
        )

        db.session.add(review)
        db.session.commit()

        flash('Thank you for your review! It will be visible after approval.', 'success')
        return redirect(url_for('product_detail', slug=slug))

    @app.route('/admin/reviews')
    @login_required
    def admin_reviews():
        """List all reviews for admin approval."""
        status_filter = request.args.get('status', '')
        query = Review.query.order_by(Review.created_at.desc())

        if status_filter == 'approved':
            query = query.filter_by(is_approved=True)
        elif status_filter == 'pending':
            query = query.filter_by(is_approved=False)

        reviews_list = query.all()
        return render_template('admin/reviews.html',
                               reviews=reviews_list,
                               current_status=status_filter)

    @app.route('/admin/reviews/<int:review_id>/approve', methods=['POST'])
    @login_required
    def admin_review_approve(review_id):
        """Approve or reject a review."""
        review = Review.query.get_or_404(review_id)
        action = request.form.get('action', 'approve')

        if action == 'approve':
            review.is_approved = True
            flash(f'Review approved!', 'success')
        elif action == 'reject':
            db.session.delete(review)
            flash(f'Review rejected.', 'info')

        db.session.commit()
        return redirect(url_for('admin_reviews'))

    # ═══════════════════════════════════════════════════════════
    # SEARCH & API ROUTES
    # ═══════════════════════════════════════════════════════════

    @app.route('/api/search')
    def api_search():
        """Live search endpoint for AJAX search bar."""
        q = request.args.get('q', '').strip()
        if len(q) < 2:
            return jsonify([])

        products = Product.query.filter(
            Product.is_active == True,
            db.or_(
                Product.name.ilike(f'%{q}%'),
                Product.description.ilike(f'%{q}%')
            )
        ).limit(8).all()

        return jsonify([{
            'name': p.name,
            'slug': p.slug,
            'price': p.price,
            'image': p.image_url,
            'category': p.category.name if p.category else ''
        } for p in products])

    @app.route('/api/wishlist/toggle', methods=['POST'])
    def toggle_wishlist():
        """Toggle product in wishlist using session ID."""
        product_id = request.json.get('product_id', type=int)
        product = Product.query.get_or_404(product_id)

        # Get or create session ID
        session_id = session.get('session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            session['session_id'] = session_id

        # Check if already in wishlist
        wishlist_item = WishlistItem.query.filter_by(
            session_id=session_id, product_id=product_id
        ).first()

        if wishlist_item:
            db.session.delete(wishlist_item)
            action = 'removed'
        else:
            wishlist_item = WishlistItem(
                session_id=session_id,
                product_id=product_id
            )
            db.session.add(wishlist_item)
            action = 'added'

        db.session.commit()

        return jsonify({
            'success': True,
            'action': action,
            'message': f'{product.name} {action} from wishlist!'
        })

    @app.route('/api/wishlist')
    def get_wishlist():
        """Return wishlist product IDs for current session."""
        session_id = session.get('session_id')
        if not session_id:
            return jsonify([])

        wishlist_items = WishlistItem.query.filter_by(session_id=session_id).all()
        return jsonify([item.product_id for item in wishlist_items])

    @app.route('/api/cart/count')
    def api_cart_count():
        """Return current cart count (used by JavaScript)."""
        cart = session.get('cart', {})
        count = sum(item['quantity'] for item in cart.values())
        return jsonify({'count': count})

    # ═══════════════════════════════════════════════════════════
    # ADMIN ROUTES (Dashboard for managing the store)
    # ═══════════════════════════════════════════════════════════

    @app.route('/admin/login', methods=['GET', 'POST'])
    def admin_login():
        """Admin login page with rate limiting."""
        if current_user.is_authenticated:
            return redirect(url_for('admin_dashboard'))

        if request.method == 'POST':
            # Rate limiting: Max 5 login attempts per 15 minutes
            client_ip = request.remote_addr
            if not rate_limiter.is_allowed(f"login_{client_ip}", max_attempts=5, window_seconds=900):
                flash('Too many login attempts. Please try again in 15 minutes.', 'danger')
                return redirect(url_for('admin_login'))

            username = request.form.get('username', '')
            password = request.form.get('password', '')

            user = AdminUser.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                flash('Welcome back!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('admin_dashboard'))
            else:
                flash('Invalid username or password.', 'danger')

        return render_template('admin/login.html')

    @app.route('/admin/logout')
    @login_required
    def admin_logout():
        """Log out the admin user."""
        logout_user()
        flash('Logged out successfully.', 'info')
        return redirect(url_for('home'))

    @app.route('/admin')
    @login_required
    def admin_dashboard():
        """
        Admin dashboard - Shows overview of orders, products, and inquiries.
        """
        stats = {
            'total_products': Product.query.filter_by(is_active=True).count(),
            'total_orders': Order.query.count(),
            'pending_orders': Order.query.filter(
                Order.order_status.in_(['pending', 'confirmed'])
            ).count(),
            'total_revenue': db.session.query(
                db.func.sum(Order.total_amount)
            ).filter(Order.order_status != 'cancelled').scalar() or 0,
            'total_inquiries': Inquiry.query.count(),
            'unread_inquiries': Inquiry.query.filter_by(is_read=False).count(),
            'pending_reviews': Review.query.filter_by(is_approved=False).count(),
        }

        recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
        recent_inquiries = Inquiry.query.order_by(Inquiry.created_at.desc()).limit(5).all()

        return render_template('admin/dashboard.html',
                               stats=stats,
                               recent_orders=recent_orders,
                               recent_inquiries=recent_inquiries)

    # ─── Admin: Product Management ──────────────────────────────

    @app.route('/admin/products')
    @login_required
    def admin_products():
        """List all products for admin management."""
        products_list = Product.query.order_by(Product.created_at.desc()).all()
        return render_template('admin/products.html', products=products_list)

    @app.route('/admin/products/add', methods=['GET', 'POST'])
    @login_required
    def admin_product_add():
        """Add a new product."""
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            slug = slugify(name)

            # Ensure slug is unique
            existing = Product.query.filter_by(slug=slug).first()
            if existing:
                slug = f"{slug}-{uuid.uuid4().hex[:4]}"

            product = Product(
                name=name,
                slug=slug,
                description=request.form.get('description', ''),
                price=float(request.form.get('price', 0)),
                cost_price=float(request.form.get('cost_price', 0) or 0),
                category_id=int(request.form.get('category_id', 1)),
                sku=request.form.get('sku', f"SKU-{uuid.uuid4().hex[:8].upper()}"),
                stock_quantity=int(request.form.get('stock_quantity', 0) or 0),
                is_featured='is_featured' in request.form,
                is_active='is_active' in request.form,
                discount_percentage=float(request.form.get('discount_percentage', 0) or 0),
            )

            # Handle main image upload
            file = request.files.get('image_url')
            if file and file.filename:
                filename = save_image(file)
                product.image_url = filename

            db.session.add(product)
            db.session.commit()
            flash(f'Product "{name}" added successfully!', 'success')
            return redirect(url_for('admin_products'))

        categories = Category.query.filter_by(is_active=True).all()
        return render_template('admin/product_form.html',
                               product=None, categories=categories,
                               title='Add New Product')

    @app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
    @login_required
    def admin_product_edit(product_id):
        """Edit an existing product."""
        product = Product.query.get_or_404(product_id)

        if request.method == 'POST':
            product.name = request.form.get('name', '').strip()
            product.description = request.form.get('description', '')
            product.price = float(request.form.get('price', 0))
            product.cost_price = float(request.form.get('cost_price', 0) or 0)
            product.category_id = int(request.form.get('category_id', 1))
            product.sku = request.form.get('sku', product.sku)
            product.stock_quantity = int(request.form.get('stock_quantity', 0) or 0)
            product.is_featured = 'is_featured' in request.form
            product.is_active = 'is_active' in request.form
            product.discount_percentage = float(request.form.get('discount_percentage', 0) or 0)

            # Handle image upload (only update if new file uploaded)
            file = request.files.get('image_url')
            if file and file.filename:
                filename = save_image(file)
                product.image_url = filename

            db.session.commit()
            flash(f'Product "{product.name}" updated!', 'success')
            return redirect(url_for('admin_products'))

        categories = Category.query.filter_by(is_active=True).all()
        return render_template('admin/product_form.html',
                               product=product, categories=categories,
                               title=f'Edit: {product.name}')

    @app.route('/admin/products/delete/<int:product_id>', methods=['POST'])
    @login_required
    def admin_product_delete(product_id):
        """Soft-delete a product (just hides it, doesn't remove from database)."""
        product = Product.query.get_or_404(product_id)
        product.is_active = False
        db.session.commit()
        flash(f'Product "{product.name}" has been deactivated.', 'info')
        return redirect(url_for('admin_products'))

    # ─── Admin: Category Management ─────────────────────────────

    @app.route('/admin/categories')
    @login_required
    def admin_categories():
        """List all categories."""
        cats = Category.query.order_by(Category.display_order).all()
        return render_template('admin/categories.html', categories_list=cats)

    @app.route('/admin/categories/add', methods=['POST'])
    @login_required
    def admin_category_add():
        """Add a new category."""
        name = request.form.get('name', '').strip()
        if name:
            cat = Category(
                name=name,
                slug=slugify(name),
                description=request.form.get('description', ''),
                display_order=int(request.form.get('display_order', 0) or 0),
            )
            db.session.add(cat)
            db.session.commit()
            flash(f'Category "{name}" added!', 'success')
        return redirect(url_for('admin_categories'))

    @app.route('/admin/categories/delete/<int:cat_id>', methods=['POST'])
    @login_required
    def admin_category_delete(cat_id):
        """Delete a category (only if no products use it)."""
        cat = Category.query.get_or_404(cat_id)
        if cat.products:
            flash(f'Cannot delete "{cat.name}" - it has {len(cat.products)} products.', 'danger')
        else:
            db.session.delete(cat)
            db.session.commit()
            flash(f'Category "{cat.name}" deleted.', 'info')
        return redirect(url_for('admin_categories'))

    # ─── Admin: Order Management ────────────────────────────────

    @app.route('/admin/orders')
    @login_required
    def admin_orders():
        """List all orders with filtering by status."""
        status_filter = request.args.get('status', '')
        query = Order.query.order_by(Order.created_at.desc())
        if status_filter:
            query = query.filter_by(order_status=status_filter)
        orders_list = query.all()
        return render_template('admin/orders.html',
                               orders=orders_list,
                               current_status=status_filter)

    @app.route('/admin/orders/<int:order_id>')
    @login_required
    def admin_order_detail(order_id):
        """View order details."""
        order = Order.query.get_or_404(order_id)
        return render_template('admin/order_detail.html', order=order)

    @app.route('/admin/orders/<int:order_id>/status', methods=['POST'])
    @login_required
    def admin_order_status(order_id):
        """Update order status."""
        order = Order.query.get_or_404(order_id)
        new_status = request.form.get('status', '')
        if new_status in ['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled']:
            order.order_status = new_status
            db.session.commit()
            flash(f'Order {order.order_number} status updated to {new_status}.', 'success')
        return redirect(url_for('admin_order_detail', order_id=order.id))

    # ─── Admin: Inquiry Management ──────────────────────────────

    @app.route('/admin/inquiries')
    @login_required
    def admin_inquiries():
        """List all customer inquiries."""
        inquiries_list = Inquiry.query.order_by(Inquiry.created_at.desc()).all()
        return render_template('admin/inquiries.html', inquiries=inquiries_list)

    @app.route('/admin/inquiries/<int:inquiry_id>')
    @login_required
    def admin_inquiry_detail(inquiry_id):
        """View and mark inquiry as read."""
        inquiry = Inquiry.query.get_or_404(inquiry_id)
        if not inquiry.is_read:
            inquiry.is_read = True
            db.session.commit()
        return render_template('admin/inquiry_detail.html', inquiry=inquiry)

    @app.route('/admin/inquiries/<int:inquiry_id>/delete', methods=['POST'])
    @login_required
    def admin_inquiry_delete(inquiry_id):
        """Delete an inquiry."""
        inquiry = Inquiry.query.get_or_404(inquiry_id)
        db.session.delete(inquiry)
        db.session.commit()
        flash('Inquiry deleted.', 'info')
        return redirect(url_for('admin_inquiries'))

    # ═══════════════════════════════════════════════════════════
    # ERROR HANDLERS
    # ═══════════════════════════════════════════════════════════

    @app.errorhandler(404)
    def page_not_found(e):
        """Custom 404 page."""
        return render_template('404.html'), 404

    @app.errorhandler(413)
    def file_too_large(e):
        """Handle file upload too large error."""
        flash('File too large! Maximum upload size is 16 MB. Please compress your image and try again.', 'danger')
        return redirect(request.referrer or url_for('admin_dashboard')), 413

    @app.errorhandler(500)
    def server_error(e):
        """Custom 500 page."""
        logger.error(f"Server error: {e}")
        return render_template('500.html'), 500

    # ═══════════════════════════════════════════════════════════
    # DATABASE INITIALIZATION
    # ═══════════════════════════════════════════════════════════

    with app.app_context():
        # Create all database tables
        db.create_all()

        # Create default admin user if none exists
        if not AdminUser.query.first():
            admin = AdminUser(
                username=app.config['ADMIN_USERNAME'],
                email=app.config.get('BUSINESS_EMAIL', 'admin@printcraft3d.com')
            )
            admin.set_password(app.config['ADMIN_PASSWORD'])
            db.session.add(admin)
            db.session.commit()
            print(f"Admin user created: {app.config['ADMIN_USERNAME']}")

        # Create default categories if none exist
        if not Category.query.first():
            default_categories = [
                ('Desk Accessories', 'desk-accessories', 'Organize your workspace in style', 1),
                ('Phone Stands', 'phone-stands', 'Sturdy and stylish phone holders', 2),
                ('Home Decor', 'home-decor', 'Beautiful 3D printed decorative items', 3),
                ('Custom Orders', 'custom-orders', 'Get your ideas 3D printed', 4),
                ('Keychains & Gifts', 'keychains-gifts', 'Perfect small gifts and accessories', 5),
            ]
            for name, slug, desc, order in default_categories:
                cat = Category(name=name, slug=slug, description=desc, display_order=order)
                db.session.add(cat)
            db.session.commit()
            print("Default categories created")

    return app


# ═══════════════════════════════════════════════════════════════
# RUN THE APPLICATION
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    app = create_app()
    print("\n" + "=" * 60)
    print("PrintCraft 3D Store v2.0 is running!")
    print("=" * 60)
    print(f"Open: http://localhost:5000")
    print(f"Admin: http://localhost:5000/admin")
    print(f"Username: {app.config['ADMIN_USERNAME']}")
    print(f"Password: {app.config['ADMIN_PASSWORD']}")
    print("=" * 60 + "\n")

    # debug=True enables:
    # - Auto-reload when you save code changes
    # - Detailed error pages in the browser
    # Turn OFF debug in production!
    app.run(debug=True, host='0.0.0.0', port=5000)
