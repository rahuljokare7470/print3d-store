# PrintCraft 3D - v2.0 Deployment Guide

## What's New in v2.0

- Razorpay payment gateway (UPI, Cards, Net Banking)
- PostgreSQL database (no more data loss on Render)
- Product reviews & ratings system
- Live AJAX search
- Wishlist functionality
- Image compression pipeline
- Security headers (CSP, XSS protection, HSTS)
- Rate limiting on login & contact forms
- GZip compression
- Mobile-first responsive redesign
- Trust badges & floating WhatsApp button
- Admin review management panel
- Product recommendations
- Lazy loading images
- Recently viewed products

---

## Step-by-Step Render Deployment

### 1. Replace Your Local Files

Copy ALL files from this `print3d_store_v2` folder to your existing `print3d_store` project folder on your Desktop, replacing old files.

```bash
# On your Mac terminal:
cp -R ~/Desktop/print3d_store_v2/* ~/Desktop/print3d_store/
```

Keep your existing `static/uploads/` folder with product images intact.

### 2. Create PostgreSQL Database on Render

1. Go to https://dashboard.render.com
2. Click **New** > **PostgreSQL**
3. Name: `printcraft3d-db`
4. Plan: **Free** (or Starter $7/mo for production)
5. Click **Create Database**
6. Wait for it to provision, then copy the **Internal Database URL**

### 3. Set Environment Variables on Render

Go to your Web Service > **Environment** tab. Add these:

| Key | Value |
|-----|-------|
| `SECRET_KEY` | Generate a random string (use: `python3 -c "import secrets; print(secrets.token_hex(32))"`) |
| `DATABASE_URL` | Paste the Internal Database URL from Step 2 |
| `ADMIN_USERNAME` | `admin` (or your preferred username) |
| `ADMIN_PASSWORD` | Choose a strong password |
| `ADMIN_EMAIL` | Your email |
| `RAZORPAY_KEY_ID` | Get from https://dashboard.razorpay.com (Test mode first) |
| `RAZORPAY_KEY_SECRET` | Get from Razorpay dashboard |
| `MAIL_USERNAME` | Your Gmail address |
| `MAIL_PASSWORD` | Gmail App Password (not regular password) |
| `BUSINESS_WHATSAPP` | `91XXXXXXXXXX` (your WhatsApp number) |
| `BUSINESS_PHONE` | `+91-XXXXXXXXXX` |
| `BUSINESS_EMAIL` | Your business email |

### 4. Update Render Build Settings

- **Build Command**: `pip install --upgrade pip setuptools wheel && pip install --prefer-binary -r requirements.txt`
- **Start Command**: `gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`

### 5. Push to GitHub & Deploy

```bash
cd ~/Desktop/print3d_store
git add .
git commit -m "Upgrade to v2.0 - Razorpay, PostgreSQL, reviews, security"
git push origin main
```

Render will auto-deploy. Wait 2-3 minutes.

### 6. Initialize Database

After first deployment, go to Render **Shell** tab and run:

```bash
python3 -c "from app import create_app; app = create_app(); app.app_context().push(); from models import db; db.create_all(); print('Database tables created!')"
```

Then seed initial data:

```bash
python3 seed_data.py
```

### 7. Set Up Razorpay (When Ready for Live Payments)

1. Sign up at https://dashboard.razorpay.com
2. Complete KYC verification
3. Use **Test Mode** keys first for testing
4. Switch to **Live Mode** keys when ready for real payments
5. Update environment variables on Render

---

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your values

# Run locally
python app.py
# Open http://localhost:5000
```

---

## File Structure

```
print3d_store_v2/
├── app.py                    # Main Flask application
├── config.py                 # Configuration (PostgreSQL, Razorpay, etc.)
├── models.py                 # Database models
├── wsgi.py                   # WSGI entry point for Gunicorn
├── seed_data.py              # Database seeding script
├── requirements.txt          # Python dependencies
├── Procfile                  # Render/Heroku process file
├── runtime.txt               # Python version
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules
├── static/
│   ├── css/style.css         # Main stylesheet
│   ├── js/main.js            # Main JavaScript
│   └── uploads/              # Product images
└── templates/
    ├── base.html             # Master template
    ├── index.html            # Homepage
    ├── products.html         # Products listing
    ├── product_detail.html   # Single product page
    ├── cart.html             # Shopping cart
    ├── checkout.html         # Checkout with Razorpay
    ├── order_confirmation.html
    ├── about.html            # About us
    ├── contact.html          # Contact form
    ├── 404.html              # Not found page
    ├── 500.html              # Server error page
    └── admin/
        ├── login.html
        ├── dashboard.html
        ├── products.html
        ├── product_form.html
        ├── categories.html
        ├── orders.html
        ├── order_detail.html
        ├── inquiries.html
        ├── inquiry_detail.html
        └── reviews.html      # NEW: Review management
```

---

## Testing Checklist

- [ ] Homepage loads with all products
- [ ] Product categories filter correctly
- [ ] Product detail page shows images, reviews tab
- [ ] Add to cart works (AJAX)
- [ ] Cart quantity update works
- [ ] Checkout form validates properly
- [ ] COD order completes successfully
- [ ] Razorpay payment modal opens (test mode)
- [ ] Order confirmation page shows
- [ ] Admin login works
- [ ] Admin dashboard shows stats
- [ ] Admin can add/edit/delete products
- [ ] Admin can manage categories
- [ ] Admin can view/update orders
- [ ] Admin can approve/delete reviews
- [ ] Contact form submits
- [ ] Live search returns results
- [ ] WhatsApp button links correctly
- [ ] Mobile responsive on all pages
- [ ] 404 page shows for invalid URLs
- [ ] Images load with lazy loading
