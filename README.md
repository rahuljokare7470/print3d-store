# PrintCraft 3D - E-Commerce Web Application

A full-stack web application for selling 3D printed products, built with Python Flask.

**Live Demo:** (Deploy using the guide below to get your URL)

---

## Quick Start (Get Running in 5 Minutes)

### Prerequisites
- Python 3.8 or higher installed ([Download Python](https://python.org/downloads))
- A text editor (VS Code recommended: [Download VS Code](https://code.visualstudio.com))

### Step 1: Set Up the Project

```bash
# Open terminal/command prompt and navigate to the project folder
cd print3d_store

# Create a virtual environment (keeps dependencies isolated)
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# You should see (venv) at the start of your terminal line
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Configure Settings

```bash
# Copy the example environment file
cp .env.example .env    # macOS/Linux
copy .env.example .env  # Windows

# Edit .env with your details (email, WhatsApp number, etc.)
```

### Step 4: Run the Application

```bash
python app.py
```

### Step 5: Open in Browser

```
Website:  http://localhost:5000
Admin:    http://localhost:5000/admin
```

### Step 6: Add Sample Products

```bash
# In a new terminal (keep the app running!)
python seed_data.py
```

---

## Admin Panel Access

```
URL:      http://localhost:5000/admin
Username: admin
Password: print3d@2026
```

**Change these immediately** by editing `.env`:
```
ADMIN_USERNAME=your_username
ADMIN_PASSWORD=your_secure_password
```

---

## Project Structure Explained

```
print3d_store/
├── app.py              # Main application (all routes and logic)
├── models.py           # Database models (tables and relationships)
├── config.py           # Settings (prices, email, business info)
├── seed_data.py        # Script to add sample products
├── wsgi.py             # Production server entry point
├── requirements.txt    # Python package dependencies
├── Procfile            # Deployment configuration
├── .env.example        # Template for secret settings
├── .gitignore          # Files to exclude from Git
├── store.db            # SQLite database (created on first run)
│
├── static/             # Static files (CSS, JS, images)
│   ├── css/
│   │   └── style.css   # All custom styles
│   ├── js/
│   │   └── main.js     # Cart, WhatsApp, interactivity
│   └── uploads/        # Product images (uploaded via admin)
│
└── templates/          # HTML templates (Jinja2)
    ├── base.html       # Base layout (navbar, footer)
    ├── index.html      # Homepage
    ├── products.html   # Product gallery with filters
    ├── product_detail.html  # Single product page
    ├── cart.html       # Shopping cart
    ├── checkout.html   # Checkout form
    ├── order_confirmation.html
    ├── about.html      # About Us page
    ├── contact.html    # Contact form
    ├── 404.html        # Page not found
    ├── 500.html        # Server error
    │
    └── admin/          # Admin panel templates
        ├── login.html
        ├── dashboard.html
        ├── products.html
        ├── product_form.html
        ├── orders.html
        ├── order_detail.html
        ├── categories.html
        ├── inquiries.html
        └── inquiry_detail.html
```

---

## Common Tasks

### Adding a New Product
1. Log into Admin Panel (`/admin`)
2. Click "Products" in sidebar
3. Click "Add New Product"
4. Fill in details, upload images
5. Click "Save"

### Changing Prices
1. Admin Panel → Products → Click "Edit" on the product
2. Change the price field
3. Optionally set "Original Price" (for showing discounts)
4. Click "Save"

### Adding a New Category
1. Admin Panel → Categories
2. Fill in the form at the top
3. Click "Add Category"

### Changing the Color Scheme
Open `static/css/style.css` and change the CSS variables at the top:
```css
:root {
    --primary: #2563eb;       /* Change this to your brand color */
    --secondary: #059669;     /* Change this for accents */
    --accent: #f59e0b;        /* Change this for highlights */
}
```

### Changing Business Details
Edit `config.py` or `.env`:
```python
BUSINESS_NAME = 'Your Business Name'
BUSINESS_EMAIL = 'your-email@gmail.com'
WHATSAPP_NUMBER = '91XXXXXXXXXX'  # Your WhatsApp number
```

---

## Email Setup (Gmail)

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable **2-Step Verification**
3. Go to **App passwords**
4. Select "Mail" and "Other (Custom name)"
5. Enter "PrintCraft 3D" and click Generate
6. Copy the 16-character password
7. Add to `.env`:

```
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=xxxx xxxx xxxx xxxx
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

---

## Deployment Guide (Free Hosting)

### Option 1: Render (Recommended - Easiest)

1. Push code to GitHub:
```bash
git init
git add .
git commit -m "Initial commit"
# Create a repository on github.com, then:
git remote add origin https://github.com/YOUR_USERNAME/print3d-store.git
git push -u origin main
```

2. Go to [render.com](https://render.com) and sign up (free)
3. Click "New" → "Web Service"
4. Connect your GitHub repository
5. Settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn wsgi:app`
6. Add Environment Variables (from your `.env` file)
7. Click "Create Web Service"
8. Your site will be live at `https://your-app.onrender.com`

### Option 2: PythonAnywhere (Free)

1. Go to [pythonanywhere.com](https://pythonanywhere.com) and sign up
2. Upload your project files via the "Files" tab
3. Open a Bash console and run:
```bash
cd print3d_store
pip install -r requirements.txt --user
python seed_data.py
```
4. Go to "Web" tab → "Add a new web app"
5. Choose Flask, set the path to your project
6. Edit the WSGI configuration file to point to your app
7. Click "Reload" - your site is live!

### Option 3: Railway

1. Push code to GitHub
2. Go to [railway.app](https://railway.app) and sign up
3. Click "New Project" → "Deploy from GitHub Repo"
4. Select your repository
5. Add environment variables
6. Railway auto-detects Python and deploys

### Custom Domain
All platforms above support custom domains:
1. Buy a domain from Namecheap, GoDaddy, or Google Domains
2. Follow the platform's DNS configuration guide
3. Point your domain to the platform's server

---

## Troubleshooting

### "Module not found" error
Make sure your virtual environment is activated:
```bash
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### Database errors
Delete `store.db` and restart the app - it will recreate the database:
```bash
rm store.db
python app.py
python seed_data.py
```

### Images not uploading
- Check file size (max 5MB per image)
- Ensure the `static/uploads/` folder exists
- Allowed formats: PNG, JPG, JPEG, WebP, GIF

### Email not sending
- Check your `.env` has correct email credentials
- Gmail requires an App Password (not your regular password)
- The app works fine without email - just no notifications

### Port already in use
Change the port in `app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Try 5001
```

---

## Technology Stack

| Component       | Technology                |
| --------------- | ------------------------- |
| Backend         | Python 3.8+, Flask 3.0   |
| Database        | SQLite (via SQLAlchemy)   |
| Frontend        | HTML5, CSS3, JavaScript   |
| CSS Framework   | Bootstrap 5.3             |
| Icons           | Font Awesome 6            |
| Fonts           | Google Fonts (Inter, Poppins) |
| Image Processing| Pillow (PIL)              |
| Authentication  | Flask-Login               |
| Email           | Flask-Mail                |
| Deployment      | Gunicorn + Render/Railway |

---

## Features Checklist

- [x] Responsive homepage with hero section
- [x] Product gallery with category filters
- [x] Product detail pages with image gallery
- [x] Shopping cart (session-based)
- [x] Checkout with order placement
- [x] WhatsApp quick-order integration
- [x] Contact form with email notifications
- [x] Admin dashboard with statistics
- [x] Product CRUD (Create, Read, Update, Delete)
- [x] Category management
- [x] Order management with status tracking
- [x] Customer inquiry management
- [x] Image upload with automatic optimization
- [x] SEO-friendly URLs and meta tags
- [x] Mobile-responsive design
- [x] Indian Rupee pricing
- [x] Google Maps location
- [x] Custom error pages (404, 500)

---

## Security Notes

1. **Always change** the default admin password before deploying
2. **Never commit** `.env` to Git (it's in `.gitignore`)
3. **Use HTTPS** in production (Render provides this free)
4. **Generate a proper SECRET_KEY**:
   ```python
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
5. **Turn off debug mode** in production (already handled in `wsgi.py`)

---

## Future Enhancements

Ideas to add later as you learn more:
- Payment gateway integration (Razorpay/PayU)
- User accounts and order history
- Product reviews and ratings
- Inventory management
- Discount coupons
- Blog section for 3D printing tips
- Multi-language support (Hindi, Marathi)
- Progressive Web App (PWA) support
- Analytics dashboard with charts

---

Built with care for the 3D printing community in Pune, Maharashtra, India.
