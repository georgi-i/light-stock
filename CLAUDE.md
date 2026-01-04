# Inventory Management System (IMS) - Project Specification

## Project Overview
Build a lightweight, secure web-based Inventory Management System optimized for AWS Lightsail deployment. The system should track products with barcode/RFID scanning capabilities, featuring a minimalistic Apple-inspired interface.

## Technical Requirements

### Backend
- **Language**: Python 3.11+
- **Framework**: Flask or FastAPI (choose based on simplicity vs. performance needs)
- **Database**: SQLite for development, PostgreSQL for production (stick with SQLite, more logical for such small project)
- **ORM**: SQLAlchemy
- **Authentication**: Flask-Login or FastAPI JWT with bcrypt password hashing AND Flask-Security-Too 2FA with Google Authenticator

### Frontend
- **Framework**: Vanilla JavaScript or lightweight framework (Alpine.js recommended for minimal overhead)
- **Styling**: Tailwind CSS for Apple-inspired minimalistic design
- **Responsive**: Mobile-first design, works on tablets and desktops
- **UI Principles**: Clean, spacious, intuitive - inspired by iOS/macOS design language

### Deployment
- **Platform**: AWS Lightsail ($3.50-$5/month tier)
- **Web Server**: Nginx as reverse proxy
- **WSGI**: Gunicorn
- **Process Manager**: systemd or supervisor
- **SSL**: Let's Encrypt via Certbot

## Core Features

### 1. Product Management
- Add, edit, delete products
- Product fields:
  - Name (bilingual: Bulgarian/English)
  - SKU/Barcode number
  - Description
  - Quantity in stock
  - Minimum stock level (alert threshold)
  - Unit price
  - Category
  - Location/warehouse section
  - Date added/last modified
- Search and filter products
- Low stock alerts/warnings

### 2. Barcode/RFID Scanning
- Support for USB barcode scanners (input as keyboard wedge)
- Support for RFID readers (USB/Serial connection)
- Quick lookup by scanning
- Add stock by scanning
- Remove stock by scanning
- Barcode generation for new products (Code128 or EAN-13)

### 3. Authentication & User Management
- Secure user registration and login
- Password requirements (min 12 chars, complexity rules)
- Role-based access control (Admin, Manager, Staff)
- Session management with timeout
- Login attempt limiting (rate limiting)
- Password reset functionality
- Two-factor authentication (Flask-Security-Too)

### 4. Internationalization (i18n)
- Language toggle in settings (Bulgarian/English)
- All UI text translatable
- Store language preference per user
- Use Flask-Babel or similar i18n library
- Product names/descriptions stored in both languages

### 5. Dashboard & Reports
- Overview dashboard:
  - Total products
  - Low stock items
  - Recent activities
  - Quick stats
- Simple reports:
  - Inventory value
  - Stock movement history
  - Export to CSV

## Security Best Practices

### Application Security
- **Password Security**: 
  - Bcrypt hashing (cost factor 12+)
  - Enforce strong password policy
  - Secure password reset flow with time-limited tokens
  
- **Session Management**:
  - Secure, HTTPOnly, SameSite cookies
  - CSRF protection on all forms
  - Session timeout after inactivity (30 min default)
  
- **Input Validation**:
  - Sanitize all user inputs
  - Use parameterized queries (SQLAlchemy ORM)
  - Validate file uploads (if any)
  
- **API Security**:
  - Rate limiting on authentication endpoints
  - JWT tokens with short expiration (if using FastAPI)
  - API endpoint authentication required

### Infrastructure Security
- **HTTPS Only**: Force HTTPS redirect
- **Security Headers**:
  - Content-Security-Policy
  - X-Frame-Options: DENY
  - X-Content-Type-Options: nosniff
  - Strict-Transport-Security
  
- **Database**:
  - No default credentials
  - Database connection over localhost only
  - Regular backups
  
- **Server Hardening**:
  - Disable SSH password auth (keys only)
  - Configure firewall (only 80, 443, SSH)
  - Keep system packages updated
  - Non-root application user

### Logging & Monitoring
- Log authentication attempts
- Log inventory changes (audit trail)
- Error logging (without sensitive data)
- Monitor for suspicious activity

## Design Guidelines

### Visual Design (Apple-inspired)
- **Colors**: 
  - Light mode default (white/light gray backgrounds)
  - Optional dark mode
  - Accent color: system blue (#007AFF) or custom brand color
  - Subtle shadows and borders
  
- **Typography**:
  - San Francisco font (or SF Pro substitute like Inter)
  - Clear hierarchy (large titles, regular body)
  - Ample line spacing
  
- **Layout**:
  - Generous whitespace
  - Card-based components
  - Rounded corners (8-12px radius)
  - Smooth transitions and micro-animations
  - Focus on content, minimal chrome

- **Navigation**:
  - Simple sidebar or top navigation
  - Breadcrumbs for context
  - Clear action buttons (primary/secondary hierarchy)

### UX Principles
- Minimal clicks to complete tasks
- Clear feedback on actions (success/error messages)
- Keyboard shortcuts for power users
- Scanner input works seamlessly (auto-submit on scan)
- Responsive on all screen sizes
- Loading states for async operations

## Project Structure
```
ims/
├── app/
│   ├── __init__.py
│   ├── models.py          # Database models
│   ├── auth.py            # Authentication routes
│   ├── inventory.py       # Inventory routes
│   ├── scanner.py         # Barcode/RFID handling
│   ├── utils.py           # Helper functions
│   └── templates/         # HTML templates
│       ├── base.html
│       ├── login.html
│       ├── dashboard.html
│       └── ...
├── static/
│   ├── css/
│   ├── js/
│   └── img/
├── translations/          # i18n files
│   ├── bg/
│   └── en/
├── migrations/            # Database migrations
├── config.py              # Configuration
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── .gitignore
├── README.md
└── deploy/
    ├── nginx.conf
    ├── gunicorn.conf.py
    └── setup.sh
```

## Development Phases

### Phase 1: Core Setup
- Set up Flask/FastAPI project structure
- Database models and migrations
- Basic authentication system
- Minimal UI framework

### Phase 2: Inventory Features
- Product CRUD operations
- Search and filtering
- Dashboard with stats

### Phase 3: Scanner Integration
- Barcode scanner support (USB keyboard wedge)
- RFID reader integration
- Quick scan workflows

### Phase 4: Internationalization
- Set up Flask-Babel
- Create translation files (Bulgarian/English)
- Language switcher in UI

### Phase 5: Security Hardening
- Implement all security best practices
- Rate limiting
- Security headers
- Audit logging

### Phase 6: Deployment
- AWS Lightsail setup
- Nginx configuration
- SSL certificate
- Database backup strategy
- Monitoring setup

### Phase 7: Polish & Documentation
- UI refinements
- Comprehensive README
- Deployment documentation
- User guide (bilingual)

## Open Source Considerations
- Use MIT License (permissive)
- Comprehensive README with:
  - Feature list
  - Screenshots
  - Installation guide
  - Configuration instructions
  - Deployment guide
- Contributing guidelines
- Keep sensitive data (credentials) in .env file
- Document all environment variables in .env.example
- Include Docker setup for easy local development

## Success Criteria
- Clean, intuitive interface that feels native and responsive
- Sub-second response times for all operations
- Secure by default (passes OWASP top 10 checks)
- Works seamlessly with standard USB barcode scanners
- Fully bilingual (Bulgarian/English)
- Easy to deploy on AWS Lightsail
- Well-documented and ready for portfolio/open source

## Technology Stack Summary
- **Backend**: Python 3.11+ with Flask/FastAPI
- **Database**: PostgreSQL (production), SQLite (dev)
- **Frontend**: HTML5, Tailwind CSS, Alpine.js/Vanilla JS
- **Authentication**: Flask-Login or JWT
- **i18n**: Flask-Babel
- **Deployment**: AWS Lightsail, Nginx, Gunicorn
- **Security**: bcrypt, HTTPS, CSRF protection, rate limiting

---

**Note**: This specification is designed for Claude Code to understand the full scope and build a production-ready, secure, and user-friendly inventory management system.