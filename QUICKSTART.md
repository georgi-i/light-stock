# Quick Start Guide

## Setup (First Time)

1. **Activate the virtual environment** (already created):
   ```bash
   source venv/bin/activate
   ```

2. **Initialize the database**:
   ```bash
   python init_db.py
   ```

   You'll be prompted to create an admin user. Use these example credentials:
   - Username: `admin`
   - Email: `admin@ims.local`
   - Password: (min 12 characters, e.g., `Str0ng!AdminP@ssw0rd2026#Secure`)

3. **Run the application**:
   ```bash
   python run.py
   ```

4. **Open your browser**:
   Navigate to `http://localhost:8000`

5. **Login** with your admin credentials

## Quick Commands

### Start the application
```bash
source venv/bin/activate
python run.py
```

### Initialize/Reset database
```bash
source venv/bin/activate
python init_db.py
```

### Run with Flask CLI (alternative)
```bash
source venv/bin/activate
export FLASK_APP=run.py
export FLASK_ENV=development
flask run
```

## First Steps After Login

1. **Enable 2FA** (optional but recommended):
   - Go to Profile → Enable 2FA
   - Scan QR code with Google Authenticator
   - Verify with 6-digit code

2. **Add a category**:
   - Navigate to Categories → Add Category
   - Example: "Electronics" / "Електроника"

3. **Add your first product**:
   - Navigate to Products → Add Product
   - Fill in product details in both languages
   - Set quantity and barcode if available

4. **Try the scanner**:
   - Navigate to Scanner
   - Use Quick Lookup to test barcode scanning
   - Try Stock In/Out operations

## Project Structure

```
light-stock/
├── app/                    # Main application package
│   ├── __init__.py        # Flask app factory
│   ├── models.py          # Database models
│   ├── auth.py            # Authentication routes
│   ├── inventory.py       # Inventory routes
│   ├── scanner.py         # Scanner routes
│   ├── routes.py          # Main routes
│   ├── utils.py           # Utility functions
│   ├── templates/         # HTML templates
│   └── static/            # CSS, JS, images
├── config.py              # Configuration settings
├── init_db.py             # Database initialization
├── run.py                 # Application entry point
├── requirements.txt       # Python dependencies
├── README.md              # Full documentation
└── QUICKSTART.md          # This file
```

## Features Overview

### Authentication & Security
- ✓ Secure login with bcrypt password hashing
- ✓ Optional Two-Factor Authentication (2FA)
- ✓ Role-based access control (Admin, Manager, Staff)
- ✓ Rate limiting on authentication endpoints
- ✓ CSRF protection on all forms

### Inventory Management
- ✓ Add, edit, delete products
- ✓ Bilingual support (English/Bulgarian)
- ✓ Search and filter products
- ✓ Category management
- ✓ Low stock alerts
- ✓ Stock movement tracking

### Barcode Scanning
- ✓ Quick lookup by barcode/RFID/SKU
- ✓ Stock in/out operations
- ✓ USB barcode scanner support (keyboard wedge)
- ✓ Manual code entry option

### Dashboard
- ✓ Real-time inventory statistics
- ✓ Low stock warnings
- ✓ Recent stock movements
- ✓ Quick action shortcuts

## Troubleshooting

### Port Already in Use
If port 5000 is already in use:
```bash
python run.py  # Will try to use port 5000
# Or specify a different port:
flask run --port=8000
```

### Database Issues
If you encounter database errors, reset the database:
```bash
rm instance/ims.db  # Delete the database
python init_db.py   # Recreate it
```

### Missing Dependencies
If you get import errors:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check [CLAUDE.md](CLAUDE.md) for the complete project specification
- Set up deployment on AWS Lightsail (see deployment guide)

## Support

For issues or questions, please refer to the project repository or documentation.

---

**Happy inventory management!** 📦
