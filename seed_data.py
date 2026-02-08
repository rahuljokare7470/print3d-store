"""
Seed Data Script - Populate the database with sample products
=============================================================

Run this AFTER starting the app for the first time to add sample products.
The app creates the database and categories automatically on first run.

USAGE:
    python seed_data.py

This will add sample 3D printed products to each category.
You can modify or add products below, then re-run this script.

NOTE: This script is safe to run multiple times - it checks for
existing products before adding duplicates.
"""

import os
import sys

# Add the project directory to Python's path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, Product, Category


def seed_products():
    """Add sample products to the database."""

    app = create_app()

    with app.app_context():
        # Check if products already exist
        existing = Product.query.count()
        if existing > 0:
            print(f"Database already has {existing} products.")
            response = input("Add more sample products? (y/n): ").strip().lower()
            if response != 'y':
                print("Skipping. No changes made.")
                return

        # Get category references
        categories = {cat.slug: cat.id for cat in Category.query.all()}

        # ─── Sample Products ────────────────────────────────────
        # Modify these to match your actual products!

        sample_products = [
            # ── Desk Accessories ──
            {
                'name': 'Multipurpose Desk Organiser',
                'slug': 'multipurpose-desk-organiser',
                'short_desc': '3D printed desk organizer with multiple compartments for pens, cards, and accessories.',
                'description': '''Keep your desk clean and organized with this beautifully designed 3D printed desk organizer!

Features:
- Multiple compartments for pens, pencils, and markers
- Card holder slot for business cards or sticky notes
- Phone stand slot (holds most smartphones)
- Small tray for paperclips, erasers, and small items
- Smooth finish with rounded edges
- Available in multiple colors

Perfect for students, professionals, and anyone who wants a tidy workspace.

Material: High-quality PLA plastic
Dimensions: 18cm x 12cm x 10cm
Weight: ~150g

Care Instructions: Wipe clean with a damp cloth. Keep away from direct heat sources.''',
                'price': 299,
                'original_price': 399,
                'category_slug': 'desk-accessories',
                'material': 'PLA',
                'colors': 'White,Black,Blue,Red,Green',
                'dimensions': '18cm x 12cm x 10cm',
                'weight': 150,
                'stock_status': 'in_stock',
                'is_featured': True,
            },
            {
                'name': 'Hexagonal Pen Holder',
                'slug': 'hexagonal-pen-holder',
                'short_desc': 'Modern hexagonal design pen holder. Looks great on any desk!',
                'description': '''A minimalist hexagonal pen holder that adds a modern touch to your workspace.

Features:
- Unique honeycomb-inspired design
- Holds 10-12 pens/pencils
- Weighted base for stability
- Anti-slip bottom padding

Material: PLA
Dimensions: 10cm x 10cm x 11cm''',
                'price': 149,
                'original_price': 199,
                'category_slug': 'desk-accessories',
                'material': 'PLA',
                'colors': 'White,Black,Grey,Yellow',
                'dimensions': '10cm x 10cm x 11cm',
                'weight': 80,
                'stock_status': 'in_stock',
                'is_featured': True,
            },
            {
                'name': 'Cable Management Clips (Set of 6)',
                'slug': 'cable-management-clips-set-6',
                'short_desc': 'Keep your cables organized with these adhesive cable clips.',
                'description': '''No more tangled cables! These 3D printed cable management clips keep your desk neat.

Set includes 6 clips in assorted sizes:
- 2x Small (single cable)
- 2x Medium (2-3 cables)
- 2x Large (4-5 cables)

Features self-adhesive backing for easy installation.''',
                'price': 99,
                'category_slug': 'desk-accessories',
                'material': 'PLA',
                'colors': 'White,Black,Grey',
                'dimensions': 'Various sizes',
                'weight': 30,
                'stock_status': 'in_stock',
                'is_featured': False,
            },

            # ── Phone Stands ──
            {
                'name': 'Adjustable Phone Stand',
                'slug': 'adjustable-phone-stand',
                'short_desc': 'Sturdy phone stand with adjustable viewing angle. Fits all phones.',
                'description': '''The perfect phone stand for video calls, watching content, or following recipes!

Features:
- Adjustable viewing angle (15° to 75°)
- Fits all smartphones (up to 6.7" screens)
- Works in portrait and landscape mode
- Non-slip base with rubber pads
- Built-in cable routing for charging while standing
- Foldable for easy carrying

Great for:
- Video calls (Zoom, Google Meet)
- Watching YouTube/Netflix
- Following cooking recipes
- Office desk use

Material: PLA with TPU grip pads
Dimensions: 12cm x 8cm x 2cm (folded)''',
                'price': 199,
                'original_price': 249,
                'category_slug': 'phone-stands',
                'material': 'PLA + TPU',
                'colors': 'White,Black,Blue,Pink',
                'dimensions': '12cm x 8cm x 2cm (folded)',
                'weight': 65,
                'stock_status': 'in_stock',
                'is_featured': True,
            },
            {
                'name': 'Minimal Phone Dock',
                'slug': 'minimal-phone-dock',
                'short_desc': 'Ultra-minimal phone dock. Clean design, solid hold.',
                'description': '''A beautifully simple phone dock for the minimalist.

Clean lines, solid construction, and perfect balance.
Holds your phone at the perfect viewing angle.

Compatible with most phones and slim cases.
Material: PLA
Dimensions: 8cm x 7cm x 6cm''',
                'price': 129,
                'category_slug': 'phone-stands',
                'material': 'PLA',
                'colors': 'White,Black,Wood-finish',
                'dimensions': '8cm x 7cm x 6cm',
                'weight': 45,
                'stock_status': 'in_stock',
                'is_featured': False,
            },

            # ── Home Decor ──
            {
                'name': 'Geometric Vase (Small)',
                'slug': 'geometric-vase-small',
                'short_desc': 'Low-poly geometric vase. Perfect for dried flowers or as standalone decor.',
                'description': '''Add a modern touch to your home with this stunning geometric vase!

The low-poly design creates beautiful light and shadow patterns.
Can be used with dried flowers, artificial plants, or as a standalone decor piece.

Note: Not waterproof. Use a glass insert for fresh flowers.

Material: PLA
Dimensions: 12cm diameter x 15cm tall''',
                'price': 349,
                'original_price': 449,
                'category_slug': 'home-decor',
                'material': 'PLA',
                'colors': 'White,Marble,Gold,Matte Black',
                'dimensions': '12cm x 12cm x 15cm',
                'weight': 120,
                'stock_status': 'in_stock',
                'is_featured': True,
            },
            {
                'name': 'Moon Lamp Shade',
                'slug': 'moon-lamp-shade',
                'short_desc': 'Detailed moon surface lamp shade. Creates magical ambient lighting.',
                'description': '''Transform your room with this detailed moon surface lamp shade!

Designed from actual NASA moon topology data for realistic surface detail.
Use with any standard LED bulb or fairy lights.

Creates a warm, ambient glow perfect for bedrooms and living rooms.

Diameter: 15cm
Material: White PLA (light-diffusing)''',
                'price': 499,
                'original_price': 649,
                'category_slug': 'home-decor',
                'material': 'PLA',
                'colors': 'White',
                'dimensions': '15cm diameter',
                'weight': 100,
                'stock_status': 'low_stock',
                'is_featured': True,
            },
            {
                'name': 'Wall-Mount Plant Shelf',
                'slug': 'wall-mount-plant-shelf',
                'short_desc': 'Elegant wall-mounted shelf for small plants and succulents.',
                'description': '''A charming wall-mounted shelf perfect for displaying small plants.

Comes with mounting hardware. Supports up to 500g.
Great for succulents, air plants, or small photo frames.

Material: PLA
Dimensions: 15cm x 10cm x 8cm''',
                'price': 199,
                'category_slug': 'home-decor',
                'material': 'PLA',
                'colors': 'White,Black,Wood-finish',
                'dimensions': '15cm x 10cm x 8cm',
                'weight': 70,
                'stock_status': 'in_stock',
                'is_featured': False,
            },

            # ── Keychains & Gifts ──
            {
                'name': 'Custom Name Keychain',
                'slug': 'custom-name-keychain',
                'short_desc': 'Personalized 3D printed keychain with your name. Great gift idea!',
                'description': '''Get a unique keychain with YOUR name on it!

Each keychain is custom 3D printed with your chosen name or text (up to 10 characters).

Perfect as:
- Personal accessory
- Birthday gift
- Corporate giveaway
- Party favors

After ordering, message us on WhatsApp with the name you want.

Material: PLA
Size: ~7cm x 2cm
Includes keyring attachment''',
                'price': 79,
                'original_price': 99,
                'category_slug': 'keychains-gifts',
                'material': 'PLA',
                'colors': 'Red,Blue,Green,Black,White,Pink,Yellow',
                'dimensions': '7cm x 2cm',
                'weight': 10,
                'stock_status': 'in_stock',
                'is_featured': True,
            },
            {
                'name': 'Miniature Taj Mahal',
                'slug': 'miniature-taj-mahal',
                'short_desc': 'Detailed miniature Taj Mahal model. Perfect desk decoration or souvenir.',
                'description': '''A beautifully detailed miniature replica of the Taj Mahal.

Great as a desk decoration, souvenir, or gift for tourists and history enthusiasts.

Material: White PLA
Dimensions: 10cm x 10cm x 8cm''',
                'price': 249,
                'category_slug': 'keychains-gifts',
                'material': 'PLA',
                'colors': 'White,Gold',
                'dimensions': '10cm x 10cm x 8cm',
                'weight': 60,
                'stock_status': 'in_stock',
                'is_featured': False,
            },

            # ── Custom Orders ──
            {
                'name': 'Custom 3D Print (Per Hour)',
                'slug': 'custom-3d-print-per-hour',
                'short_desc': 'Got a unique idea? We\'ll 3D print it for you! Pricing per print hour.',
                'description': '''Have a unique idea or design you want 3D printed? We can help!

How it works:
1. Share your idea or 3D model file (STL/OBJ) via WhatsApp
2. We'll review and provide a quote
3. Once approved, we print and deliver!

Pricing: ₹199 per print hour (minimum 1 hour)
Material cost included for standard PLA prints.

We accept:
- STL, OBJ, 3MF files
- Hand-drawn sketches (we'll model them for additional charge)
- Reference images

Contact us on WhatsApp to discuss your project!''',
                'price': 199,
                'category_slug': 'custom-orders',
                'material': 'PLA (other materials available)',
                'colors': 'All colors available',
                'dimensions': 'Custom',
                'weight': 0,
                'stock_status': 'in_stock',
                'is_featured': True,
            },
        ]

        # ─── Add products to database ───────────────────────────
        added = 0
        for p_data in sample_products:
            # Check if product with this slug already exists
            existing = Product.query.filter_by(slug=p_data['slug']).first()
            if existing:
                print(f"  ⏭  Skipping '{p_data['name']}' (already exists)")
                continue

            # Get category ID
            cat_slug = p_data.pop('category_slug')
            cat_id = categories.get(cat_slug, 1)

            product = Product(
                category_id=cat_id,
                meta_title=p_data['name'] + ' | PrintCraft 3D',
                meta_description=p_data['short_desc'],
                **p_data
            )
            db.session.add(product)
            added += 1
            print(f"  ✅ Added: {p_data['name']} (₹{p_data['price']})")

        db.session.commit()
        print(f"\n{'='*50}")
        print(f"✅ Added {added} new products to the database!")
        print(f"   Total products: {Product.query.count()}")
        print(f"{'='*50}")
        print(f"\nYou can now:")
        print(f"  1. Run the app: python app.py")
        print(f"  2. Visit: http://localhost:5000")
        print(f"  3. Admin: http://localhost:5000/admin")


if __name__ == '__main__':
    seed_products()
