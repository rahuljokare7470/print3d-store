"""
Database Models for the 3D Print Store
=======================================

Think of models as blueprints for your database tables.
Each class below becomes a table in your SQLite database.

HOW DATABASES WORK (Simple Explanation):
- A database is like an Excel file with multiple sheets
- Each "model" (class) below is one sheet
- Each "field" (db.Column) is one column in that sheet
- Each row is one record (e.g., one product, one order)

RELATIONSHIPS:
- A Product belongs to a Category (many products → one category)
- An Order has many OrderItems (one order → many items)
- An OrderItem links to one Product
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize the database object
# This gets connected to our Flask app in app.py
db = SQLAlchemy()


# ═══════════════════════════════════════════════════════════════
# ADMIN USER MODEL
# ═══════════════════════════════════════════════════════════════
class AdminUser(UserMixin, db.Model):
    """
    Admin user who can log into the dashboard.
    UserMixin adds required methods for Flask-Login.

    Fields:
        id          - Unique identifier (auto-generated)
        username    - Login username
        password_hash - Encrypted password (never store plain text!)
        created_at  - When this admin was created
    """
    __tablename__ = 'admin_users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        """Encrypt and store the password. Never store plain text passwords!"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if the provided password matches the stored hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<AdminUser {self.username}>'


# ═══════════════════════════════════════════════════════════════
# CATEGORY MODEL
# ═══════════════════════════════════════════════════════════════
class Category(db.Model):
    """
    Product categories (e.g., Desk Accessories, Phone Stands).

    Fields:
        id          - Unique identifier
        name        - Category name (e.g., "Desk Accessories")
        slug        - URL-friendly name (e.g., "desk-accessories")
        description - Short description of the category
        image       - Optional category image filename
        sort_order  - Controls display order (lower = first)
        is_active   - Show/hide category on the website
    """
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    slug = db.Column(db.String(120), nullable=False, unique=True)
    description = db.Column(db.Text, default='')
    image = db.Column(db.String(255), default='')
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)

    # Relationship: One category has many products
    products = db.relationship('Product', backref='category', lazy=True)

    def __repr__(self):
        return f'<Category {self.name}>'


# ═══════════════════════════════════════════════════════════════
# PRODUCT MODEL
# ═══════════════════════════════════════════════════════════════
class Product(db.Model):
    """
    Individual products in your store.

    Fields:
        id              - Unique product ID
        name            - Product name shown to customers
        slug            - URL-friendly name (for SEO-friendly URLs)
        description     - Full product description (supports multiple lines)
        short_desc      - Brief description for product cards
        price           - Price in INR (stored as integer paise for accuracy)
        original_price  - Strike-through price (for showing discounts)
        category_id     - Which category this product belongs to
        image_main      - Main product image filename
        image_2/3/4     - Additional product images
        is_featured     - Show on homepage featured section?
        is_active       - Show on website? (soft delete)
        stock_status    - "in_stock", "low_stock", "out_of_stock"
        material        - 3D printing material (PLA, ABS, etc.)
        colors          - Available colors (comma-separated)
        dimensions      - Product dimensions
        weight          - Weight in grams
        meta_title      - SEO title tag
        meta_description- SEO description tag
        views           - Number of times this product page was viewed
        created_at      - When product was added
        updated_at      - Last time product was modified
    """
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), nullable=False, unique=True)
    description = db.Column(db.Text, default='')
    short_desc = db.Column(db.String(300), default='')
    price = db.Column(db.Integer, nullable=False)  # Price in INR (whole rupees)
    original_price = db.Column(db.Integer, default=0)  # For discount display
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)

    # Product images (up to 4)
    image_main = db.Column(db.String(255), default='')
    image_2 = db.Column(db.String(255), default='')
    image_3 = db.Column(db.String(255), default='')
    image_4 = db.Column(db.String(255), default='')

    # Display options
    is_featured = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    stock_status = db.Column(db.String(20), default='in_stock')

    # Product specifications
    material = db.Column(db.String(100), default='PLA')
    colors = db.Column(db.String(300), default='')  # Comma-separated: "Red,Blue,Green"
    dimensions = db.Column(db.String(100), default='')
    weight = db.Column(db.Integer, default=0)  # Weight in grams

    # SEO fields
    meta_title = db.Column(db.String(200), default='')
    meta_description = db.Column(db.String(300), default='')

    # Analytics
    views = db.Column(db.Integer, default=0)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship: Product can appear in many order items
    order_items = db.relationship('OrderItem', backref='product', lazy=True)

    @property
    def discount_percent(self):
        """Calculate discount percentage if original_price is set."""
        if self.original_price and self.original_price > self.price:
            return round((1 - self.price / self.original_price) * 100)
        return 0

    @property
    def images(self):
        """Return list of all non-empty product images."""
        imgs = []
        for attr in ['image_main', 'image_2', 'image_3', 'image_4']:
            val = getattr(self, attr)
            if val:
                imgs.append(val)
        return imgs

    def __repr__(self):
        return f'<Product {self.name} - ₹{self.price}>'


# ═══════════════════════════════════════════════════════════════
# ORDER MODEL
# ═══════════════════════════════════════════════════════════════
class Order(db.Model):
    """
    Customer orders.

    Fields:
        id              - Unique order ID
        order_number    - Human-readable order number (e.g., "PC3D-00001")
        customer_name   - Customer's full name
        customer_email  - Customer's email address
        customer_phone  - Customer's phone number
        address         - Delivery address
        city            - City
        pincode         - PIN code
        subtotal        - Total before delivery charges
        delivery_charge - Delivery fee
        total           - Final amount to pay
        status          - Order status: pending, confirmed, processing,
                          shipped, delivered, cancelled
        payment_method  - COD, UPI, bank_transfer
        notes           - Customer notes or special instructions
        created_at      - When order was placed
        updated_at      - Last status update time
    """
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    customer_name = db.Column(db.String(200), nullable=False)
    customer_email = db.Column(db.String(200), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text, default='')
    city = db.Column(db.String(100), default='Pune')
    pincode = db.Column(db.String(10), default='')
    subtotal = db.Column(db.Integer, default=0)
    delivery_charge = db.Column(db.Integer, default=0)
    total = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='pending')
    payment_method = db.Column(db.String(30), default='cod')
    notes = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship: One order has many items
    items = db.relationship('OrderItem', backref='order', lazy=True,
                            cascade='all, delete-orphan')

    @staticmethod
    def generate_order_number():
        """Generate a unique order number like PC3D-00042."""
        last_order = Order.query.order_by(Order.id.desc()).first()
        next_num = (last_order.id + 1) if last_order else 1
        return f'PC3D-{next_num:05d}'

    def __repr__(self):
        return f'<Order {self.order_number} - ₹{self.total}>'


# ═══════════════════════════════════════════════════════════════
# ORDER ITEM MODEL
# ═══════════════════════════════════════════════════════════════
class OrderItem(db.Model):
    """
    Individual items within an order.
    Links an Order to a Product with quantity and price.

    Why store price here? Because product prices can change later,
    but the order should remember the price at the time of purchase.
    """
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    product_name = db.Column(db.String(200), nullable=False)  # Snapshot of name
    quantity = db.Column(db.Integer, default=1)
    price = db.Column(db.Integer, nullable=False)  # Price at time of order
    color = db.Column(db.String(50), default='')

    @property
    def line_total(self):
        """Total for this line item (price × quantity)."""
        return self.price * self.quantity

    def __repr__(self):
        return f'<OrderItem {self.product_name} x{self.quantity}>'


# ═══════════════════════════════════════════════════════════════
# INQUIRY MODEL
# ═══════════════════════════════════════════════════════════════
class Inquiry(db.Model):
    """
    Contact form submissions and customer inquiries.

    Fields:
        id          - Unique inquiry ID
        name        - Customer's name
        email       - Customer's email
        phone       - Customer's phone (optional)
        subject     - Subject of inquiry
        message     - Full message
        is_read     - Has admin read this? (for "new" badge)
        created_at  - When inquiry was submitted
    """
    __tablename__ = 'inquiries'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), default='')
    subject = db.Column(db.String(300), default='General Inquiry')
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Inquiry from {self.name}: {self.subject}>'


# ═══════════════════════════════════════════════════════════════
# SITE SETTINGS MODEL (Optional)
# ═══════════════════════════════════════════════════════════════
class SiteSetting(db.Model):
    """
    Key-value store for site-wide settings.
    This lets you change things like the site title, delivery charge, etc.
    from the admin panel without editing code.
    """
    __tablename__ = 'site_settings'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, default='')

    @staticmethod
    def get(key, default=''):
        """Get a setting value by key."""
        setting = SiteSetting.query.filter_by(key=key).first()
        return setting.value if setting else default

    @staticmethod
    def set(key, value):
        """Set a setting value (create or update)."""
        setting = SiteSetting.query.filter_by(key=key).first()
        if setting:
            setting.value = str(value)
        else:
            setting = SiteSetting(key=key, value=str(value))
            db.session.add(setting)
        db.session.commit()

    def __repr__(self):
        return f'<Setting {self.key}={self.value}>'
