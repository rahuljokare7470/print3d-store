"""
Database seeding script for PrintCraft 3D.
Creates initial categories, sample products, and admin user.
Run with: python seed_data.py
"""
from app import create_app, db
from app.models import Category, Product, User
import os
from datetime import datetime


def seed_database():
    """Seed the database with initial data."""
    app = create_app()

    with app.app_context():
        # Drop and recreate tables
        db.drop_all()
        db.create_all()
        print("Database tables created.")

        # Create categories
        categories_data = [
            {'name': 'Prototypes', 'description': 'Functional prototypes and test models'},
            {'name': 'Miniatures', 'description': 'Detailed miniature collectibles'},
            {'name': 'Custom Parts', 'description': 'Custom-designed replacement parts'},
            {'name': 'Jewelry', 'description': 'Elegant 3D printed jewelry pieces'},
            {'name': 'Home Decor', 'description': 'Home decoration and organizers'},
            {'name': 'Educational Models', 'description': 'Learning models and demonstrations'},
        ]

        categories = {}
        for cat_data in categories_data:
            category = Category(
                name=cat_data['name'],
                description=cat_data['description']
            )
            db.session.add(category)
            categories[cat_data['name']] = category

        db.session.commit()
        print(f"Created {len(categories)} categories.")

        # Create sample products
        products_data = [
            # Prototypes
            {
                'name': 'Motor Housing Prototype',
                'category': 'Prototypes',
                'description': 'High-precision motor housing for industrial applications. Perfect for testing fit and function.',
                'price': 1500,
                'stock': 15
            },
            {
                'name': 'Mechanical Bracket Assembly',
                'category': 'Prototypes',
                'description': 'Complex mechanical bracket with interlocking parts. Ideal for prototype testing.',
                'price': 2200,
                'stock': 12
            },
            # Miniatures
            {
                'name': 'Dragon Figure Collectible',
                'category': 'Miniatures',
                'description': '8cm detailed dragon with intricate scales and features. Gaming or display piece.',
                'price': 800,
                'stock': 30
            },
            {
                'name': 'Fantasy Castle Tower',
                'category': 'Miniatures',
                'description': 'Elaborate miniature castle tower with detailed stonework. 12cm tall.',
                'price': 1200,
                'stock': 20
            },
            # Custom Parts
            {
                'name': 'Phone Stand Custom Design',
                'category': 'Custom Parts',
                'description': 'Custom ergonomic phone stand with your design specifications included.',
                'price': 450,
                'stock': 50
            },
            {
                'name': 'Replacement Control Knob',
                'category': 'Custom Parts',
                'description': 'Precision-printed replacement control knob for machinery. Made to exact specifications.',
                'price': 350,
                'stock': 40
            },
            # Jewelry
            {
                'name': 'Geometric Pendant Necklace',
                'category': 'Jewelry',
                'description': 'Minimalist geometric pendant with delicate chain. Hypoallergenic resin.',
                'price': 650,
                'stock': 35
            },
            {
                'name': 'Hexagon Ring Series',
                'category': 'Jewelry',
                'description': 'Modern hexagon-patterned ring in multiple sizes. Smooth satin finish.',
                'price': 550,
                'stock': 45
            },
            # Home Decor
            {
                'name': 'Desk Organizer Tray',
                'category': 'Home Decor',
                'description': 'Multi-compartment desk organizer with modern hexagonal design. Keeps workspace organized.',
                'price': 750,
                'stock': 25
            },
            {
                'name': 'Decorative Wall Shelf Bracket',
                'category': 'Home Decor',
                'description': 'Stylish wall shelf bracket with organic flowing design. Load capacity: 5kg.',
                'price': 950,
                'stock': 18
            },
            # Educational Models
            {
                'name': 'DNA Helix Structure Model',
                'category': 'Educational Models',
                'description': 'Interactive DNA double helix model for science classes. Great for understanding molecular structure.',
                'price': 1800,
                'stock': 10
            },
            {
                'name': 'Solar System Planetary Model',
                'category': 'Educational Models',
                'description': 'Scale model of the solar system with all planets. Perfect for astronomy education.',
                'price': 2500,
                'stock': 8
            },
        ]

        for prod_data in products_data:
            product = Product(
                name=prod_data['name'],
                category_id=categories[prod_data['category']].id,
                description=prod_data['description'],
                price=prod_data['price'],
                stock=prod_data['stock'],
                created_at=datetime.utcnow()
            )
            db.session.add(product)

        db.session.commit()
        print(f"Created {len(products_data)} sample products.")

        # Create default admin user
        admin_username = os.getenv('ADMIN_USERNAME', 'admin')
        admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
        admin_email = os.getenv('ADMIN_EMAIL', 'admin@printcraft3d.com')

        existing_admin = User.query.filter_by(username=admin_username).first()
        if not existing_admin:
            admin = User(
                username=admin_username,
                email=admin_email,
                is_admin=True
            )
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()
            print(f"Created admin user: {admin_username}")
        else:
            print(f"Admin user {admin_username} already exists.")

        print("\nDatabase seeding completed successfully!")
        print(f"Admin credentials - Username: {admin_username}, Email: {admin_email}")


if __name__ == '__main__':
    seed_database()
