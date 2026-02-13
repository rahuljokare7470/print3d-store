"""
PrintCraft 3D - E-Commerce Web Application
============================================

This is the main application file. It ties everything together:
- Creates the Flask app
- Sets up the database
- Defines all the URL routes (pages)
- Handles admin authentication
- Manages file uploads and image optimization
- Sends emails

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
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, jsonify, abort, send_from_directory
)
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, current_user
)
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename

# Import our database models and config
from models import db, AdminUser, Category, Product, Order, OrderItem, Inquiry, SiteSetting
from config import Config

# Try to import Pillow for image optimization
try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    print("⚠️  Pillow not installed. Image optimization disabled.")
    print("   Install with: pip install Pillow")


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

    # ─── Template Context Processor ─────────────────────────────
    @app.context_processor
    def inject_globals():
        """
        Make these variables available in ALL templates automatically.
        No need to pass them in every render_template() call.
        """
        categories = Category.query.filter_by(is_active=True)\
            .order_by(Category.sort_order).all()
        cart = session.get('cart', {})
        cart_count = sum(item.get('quantity', 0) for item in cart.values())
        cart_total = sum(
            item.get('price', 0) * item.get('quantity', 0)
            for item in cart.values()
        )
        unread_inquiries = Inquiry.query.filter_by(is_read=False).count()
        pending_orders = Order.query.filter_by(status='pending').count()

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
        return text

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
                max_w = app.config['MAX_IMAGE_WIDTH']
                if img.width > max_w:
                    ratio = max_w / img.width
                    new_h = int(img.height * ratio)
                    img = img.resize((max_w, new_h), Image.LANCZOS)

                # Save optimized version
                if ext in ('jpg', 'jpeg'):
                    img.save(filepath, 'JPEG', quality=85, optimize=True)
                elif ext == 'png':
                    img.save(filepath, 'PNG', optimize=True)
                elif ext == 'webp':
                    img.save(filepath, 'WEBP', quality=85)
            except Exception as e:
                print(f"Image optimization failed: {e}")

        return filename

    def send_order_email(order):
        """Send order confirmation emails to the business and customer."""
        if not app.config.get('MAIL_USERNAME'):
            print("⚠️  Email not configured. Skipping email notification.")
            return

        try:
            # Build the items list for the email
            items_text = ""
            for item in order.items:
                items_text += f"  • {item.product_name} x{item.quantity} = ₹{item.line_total}\n"

            # Email to business owner
            owner_msg = Message(
                subject=f"🛒 New Order #{order.order_number}",
                recipients=[app.config['BUSINESS_EMAIL']],
                body=f"""New order received!

Order Number: {order.order_number}
Customer: {order.customer_name}
Phone: {order.customer_phone}
Email: {order.customer_email}
Address: {order.address}, {order.city} - {order.pincode}

Items:
{items_text}
Subtotal: ₹{order.subtotal}
Delivery: ₹{order.delivery_charge}
Total: ₹{order.total}

Payment: {order.payment_method.upper()}
Notes: {order.notes or 'None'}

Manage this order: {url_for('admin_order_detail', order_id=order.id, _external=True)}
"""
            )
            mail.send(owner_msg)

            # Email to customer
            if order.customer_email:
                customer_msg = Message(
                    subject=f"Order Confirmed - {order.order_number} | {app.config['BUSINESS_NAME']}",
                    recipients=[order.customer_email],
                    body=f"""Hi {order.customer_name}!

Thank you for your order with {app.config['BUSINESS_NAME']}! 🎉

Order Number: {order.order_number}

Items:
{items_text}
Subtotal: ₹{order.subtotal}
Delivery: ₹{order.delivery_charge}
Total: ₹{order.total}

Payment Method: {order.payment_method.upper()}

We'll start working on your order soon. For any questions, contact us:
📧 {app.config['BUSINESS_EMAIL']}
📱 {app.config['BUSINESS_PHONE']}

Thank you for choosing {app.config['BUSINESS_NAME']}!
"""
                )
                mail.send(customer_msg)

        except Exception as e:
            print(f"Email sending failed: {e}")

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
                    Product.short_desc.ilike(f'%{search}%'),
                )
            )

        # Apply sorting
        if sort_by == 'price_low':
            query = query.order_by(Product.price.asc())
        elif sort_by == 'price_high':
            query = query.order_by(Product.price.desc())
        elif sort_by == 'popular':
            query = query.order_by(Product.views.desc())
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

        # Increment view counter
        product.views += 1
        db.session.commit()

        # Get related products (same category, excluding current)
        related = Product.query.filter(
            Product.category_id == product.category_id,
            Product.id != product.id,
            Product.is_active == True
        ).limit(4).all()

        # Build WhatsApp message for this product
        whatsapp_msg = (
            f"Hi! I'm interested in *{product.name}* (₹{product.price}). "
            f"Please share more details. 🛒"
        )

        return render_template('product_detail.html',
                               product=product,
                               related_products=related,
                               whatsapp_msg=whatsapp_msg)

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
        """
        if request.method == 'POST':
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
                        subject=f"📩 New Inquiry: {inquiry.subject}",
                        recipients=[app.config['BUSINESS_EMAIL']],
                        body=f"New inquiry from {inquiry.name} ({inquiry.email}):\n\n"
                             f"Phone: {inquiry.phone}\n"
                             f"Subject: {inquiry.subject}\n\n"
                             f"Message:\n{inquiry.message}"
                    )
                    mail.send(msg)
            except Exception as e:
                print(f"Failed to send inquiry email: {e}")

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
                'image': product.image_main,
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
                        price=product.price,
                        color=item.get('color', ''),
                    ))

            delivery = 0 if subtotal >= app.config['FREE_DELIVERY_ABOVE'] else app.config['DELIVERY_CHARGE']

            # Create the order
            order = Order(
                order_number=Order.generate_order_number(),
                customer_name=request.form.get('name', '').strip(),
                customer_email=request.form.get('email', '').strip(),
                customer_phone=request.form.get('phone', '').strip(),
                address=request.form.get('address', '').strip(),
                city=request.form.get('city', 'Pune').strip(),
                pincode=request.form.get('pincode', '').strip(),
                subtotal=subtotal,
                delivery_charge=delivery,
                total=subtotal + delivery,
                payment_method=request.form.get('payment_method', 'cod'),
                notes=request.form.get('notes', '').strip(),
            )
            order.items = order_items

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
                               grand_total=subtotal + delivery)

    @app.route('/order/<order_number>')
    def order_confirmation(order_number):
        """Show order confirmation page after successful checkout."""
        order = Order.query.filter_by(order_number=order_number).first_or_404()
        return render_template('order_confirmation.html', order=order)

    # ═══════════════════════════════════════════════════════════
    # ADMIN ROUTES (Dashboard for managing the store)
    # ═══════════════════════════════════════════════════════════

    @app.route('/admin/login', methods=['GET', 'POST'])
    def admin_login():
        """Admin login page."""
        if current_user.is_authenticated:
            return redirect(url_for('admin_dashboard'))

        if request.method == 'POST':
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
            'pending_orders': Order.query.filter_by(status='pending').count(),
            'total_revenue': db.session.query(
                db.func.sum(Order.total)
            ).filter(Order.status != 'cancelled').scalar() or 0,
            'total_inquiries': Inquiry.query.count(),
            'unread_inquiries': Inquiry.query.filter_by(is_read=False).count(),
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
                short_desc=request.form.get('short_desc', ''),
                price=int(request.form.get('price', 0)),
                original_price=int(request.form.get('original_price', 0) or 0),
                category_id=int(request.form.get('category_id', 1)),
                material=request.form.get('material', 'PLA'),
                colors=request.form.get('colors', ''),
                dimensions=request.form.get('dimensions', ''),
                weight=int(request.form.get('weight', 0) or 0),
                stock_status=request.form.get('stock_status', 'in_stock'),
                is_featured='is_featured' in request.form,
                is_active='is_active' in request.form,
                meta_title=request.form.get('meta_title', '') or name,
                meta_description=request.form.get('meta_description', '') or request.form.get('short_desc', ''),
            )

            # Handle image uploads
            for field, attr in [
                ('image_main', 'image_main'),
                ('image_2', 'image_2'),
                ('image_3', 'image_3'),
                ('image_4', 'image_4'),
            ]:
                file = request.files.get(field)
                if file and file.filename:
                    filename = save_image(file)
                    setattr(product, attr, filename)

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
            product.short_desc = request.form.get('short_desc', '')
            product.price = int(request.form.get('price', 0))
            product.original_price = int(request.form.get('original_price', 0) or 0)
            product.category_id = int(request.form.get('category_id', 1))
            product.material = request.form.get('material', 'PLA')
            product.colors = request.form.get('colors', '')
            product.dimensions = request.form.get('dimensions', '')
            product.weight = int(request.form.get('weight', 0) or 0)
            product.stock_status = request.form.get('stock_status', 'in_stock')
            product.is_featured = 'is_featured' in request.form
            product.is_active = 'is_active' in request.form
            product.meta_title = request.form.get('meta_title', '') or product.name
            product.meta_description = request.form.get('meta_description', '') or product.short_desc

            # Handle image uploads (only update if new file uploaded)
            for field, attr in [
                ('image_main', 'image_main'),
                ('image_2', 'image_2'),
                ('image_3', 'image_3'),
                ('image_4', 'image_4'),
            ]:
                file = request.files.get(field)
                if file and file.filename:
                    filename = save_image(file)
                    setattr(product, attr, filename)

            # Handle image removal
            for attr in ['image_main', 'image_2', 'image_3', 'image_4']:
                if request.form.get(f'remove_{attr}'):
                    setattr(product, attr, '')

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
        cats = Category.query.order_by(Category.sort_order).all()
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
                sort_order=int(request.form.get('sort_order', 0) or 0),
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
            query = query.filter_by(status=status_filter)
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
            order.status = new_status
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
    # API ROUTES (For AJAX calls from JavaScript)
    # ═══════════════════════════════════════════════════════════

    @app.route('/api/cart/count')
    def api_cart_count():
        """Return current cart count (used by JavaScript)."""
        cart = session.get('cart', {})
        count = sum(item['quantity'] for item in cart.values())
        return jsonify({'count': count})

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
        return redirect(request.referrer or url_for('admin_dashboard'))

    @app.errorhandler(500)
    def server_error(e):
        """Custom 500 page."""
        return render_template('500.html'), 500

    # ═══════════════════════════════════════════════════════════
    # DATABASE INITIALIZATION
    # ═══════════════════════════════════════════════════════════

    with app.app_context():
        # Create all database tables
        db.create_all()

        # Create default admin user if none exists
        if not AdminUser.query.first():
            admin = AdminUser(username=app.config['ADMIN_USERNAME'])
            admin.set_password(app.config['ADMIN_PASSWORD'])
            db.session.add(admin)
            db.session.commit()
            print(f"✅ Admin user created: {app.config['ADMIN_USERNAME']}")

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
                cat = Category(name=name, slug=slug, description=desc, sort_order=order)
                db.session.add(cat)
            db.session.commit()
            print("✅ Default categories created")

    return app


# ═══════════════════════════════════════════════════════════════
# RUN THE APPLICATION
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    app = create_app()
    print("\n" + "=" * 50)
    print("🖨️  PrintCraft 3D Store is running!")
    print("=" * 50)
    print(f"🌐 Open: http://localhost:5001")
    print(f"🔧 Admin: http://localhost:5001/admin")
    print(f"   Username: {app.config['ADMIN_USERNAME']}")
    print(f"   Password: {app.config['ADMIN_PASSWORD']}")
    print("=" * 50 + "\n")

    # debug=True enables:
    # - Auto-reload when you save code changes
    # - Detailed error pages in the browser
    # Turn OFF debug in production!
    app.run(debug=True, host='0.0.0.0', port=5001)
