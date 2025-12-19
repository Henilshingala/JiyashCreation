# JiyashCreation - E-Commerce Platform

## 📋 Project Overview
JiyashCreation is a full-featured **Django-based e-commerce web application** designed for online retail operations. This platform provides a complete shopping experience with product management, user authentication, and media handling capabilities.

## 🛠️ Technology Stack
- **Backend Framework**: Django (Python)
- **Database**: SQLite3
- **Static Files Management**: Django's staticfiles
- **Media Storage**: Local file system
- **Middleware**: Custom category and security middleware

## ✨ Key Features

### 1. **Product Management**
- Multi-category product organization
- Product image uploads and management
- Inventory tracking
- Dynamic product display

### 2. **User Authentication & Security**
- User registration and login
- Password validation with Django's built-in validators
- Secure session management
- CSRF protection
- XSS filtering and clickjacking prevention
- HSTS (HTTP Strict Transport Security) support

### 3. **Admin Panel**
- Custom admin interface branded as "JiyashCreation"
- Product catalog management
- Category management
- User management
- Order tracking

### 4. **Media Management**
- Carousel images for homepage
- Product images
- Static assets organization
- Dynamic media serving

### 5. **Security Features**
- Secure browser XSS filter
- Content type nosniff
- Frame options protection (X-Frame-Options: DENY)
- HTTP-only cookies
- Secure cookies for production
- Referrer policy implementation

## 📁 Project Structure
```
JiyashCreation-main/
├── app/                    # Main application directory
├── jiyash/                 # Project configuration
│   ├── settings.py        # Django settings
│   ├── urls.py           # URL routing
│   └── wsgi.py           # WSGI configuration
├── carousel_images/        # Homepage carousel images
├── media/                  # User-uploaded media files
├── static/                 # Static files (CSS, JS, images)
├── staticfiles/            # Collected static files for production
├── db.sqlite3             # SQLite database
└── manage.py              # Django management script
```

## 🚀 Installation & Setup

### Prerequisites
- Python 3.x
- pip (Python package manager)

### Installation Steps

1. **Clone or navigate to the project directory**
   ```bash
   cd JiyashCreation-main/JiyashCreation-main
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Django**
   ```bash
   pip install django
   ```

4. **Apply database migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser account**
   ```bash
   python manage.py createsuperuser
   ```

6. **Collect static files**
   ```bash
   python manage.py collectstatic
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Main website: http://localhost:8000
   - Admin panel: http://localhost:8000/admin

## 📸 Output Screenshots

Experience the visual interface of JiyashCreation:

| | |
|---|---|
| ![Landing Page](https://raw.githubusercontent.com/Henilshingala/Output-images/master/JiyashCreation/1.png) | ![Product Catalog](https://raw.githubusercontent.com/Henilshingala/Output-images/master/JiyashCreation/2.png) |
| ![Product Detail](https://raw.githubusercontent.com/Henilshingala/Output-images/master/JiyashCreation/3.png) | ![Cart View](https://raw.githubusercontent.com/Henilshingala/Output-images/master/JiyashCreation/4.png) |
| ![Checkout Process](https://raw.githubusercontent.com/Henilshingala/Output-images/master/JiyashCreation/5.png) | ![User Login](https://raw.githubusercontent.com/Henilshingala/Output-images/master/JiyashCreation/6.png) |
| ![Admin Dashboard](https://raw.githubusercontent.com/Henilshingala/Output-images/master/JiyashCreation/7.png) | ![Order Management](https://raw.githubusercontent.com/Henilshingala/Output-images/master/JiyashCreation/8.png) |
| ![Category Management](https://raw.githubusercontent.com/Henilshingala/Output-images/master/JiyashCreation/9.png) | ![Static Pages](https://raw.githubusercontent.com/Henilshingala/Output-images/master/JiyashCreation/10.png) |
| ![Responsive Design](https://raw.githubusercontent.com/Henilshingala/Output-images/master/JiyashCreation/11.png) | ![Search Functionality](https://raw.githubusercontent.com/Henilshingala/Output-images/master/JiyashCreation/12.png) |
| ![User Profile](https://raw.githubusercontent.com/Henilshingala/Output-images/master/JiyashCreation/13.png) | ![Wishlist](https://raw.githubusercontent.com/Henilshingala/Output-images/master/JiyashCreation/14.png) |
| ![Payment Methods](https://raw.githubusercontent.com/Henilshingala/Output-images/master/JiyashCreation/15.png) | ![Review System](https://raw.githubusercontent.com/Henilshingala/Output-images/master/JiyashCreation/16.png) |
| ![Carousel Settings](https://raw.githubusercontent.com/Henilshingala/Output-images/master/JiyashCreation/17.png) | |

---
*Reference for Output Images:* [Henilshingala/Output-images](https://github.com/Henilshingala/Output-images/tree/master/JiyashCreation)

## 🔧 Configuration

### Settings Configuration (jiyash/settings.py)
- **DEBUG Mode**: Currently set to `True` (disable in production)
- **Allowed Hosts**: `localhost`, `127.0.0.1`
- **Secret Key**: Change this in production!
- **Media URL**: `/media/`
- **Static URL**: `/static/`

### Security Settings
All production security features are already configured:
- HSTS with 1-year max-age
- Secure cookies (when DEBUG=False)
- XSS and clickjacking protection
- CSRF protection enabled

## 📊 Database
The project uses SQLite3 database (`db.sqlite3`) which includes:
- User accounts
- Product catalog
- Categories
- Orders
- Session data

**Database Size**: ~425KB (includes sample data)

## 🎨 Features in Detail

### Custom Middleware
- **CategoryActiveMiddleware**: Manages active categories throughout the application
- Context processors for header categories and active categories

### Template System
- Django template engine
- Templates located in `app/templates/`
- Context processors for global data

### File Uploads
The media directory contains user-uploaded files:
- Product images
- Category images
- User avatars (if implemented)

## 🔐 Security Best Practices

This application implements:
- ✅ Password validation (similarity, minimum length, common passwords, numeric)
- ✅ Session security
- ✅ CSRF token validation
- ✅ XSS protection
- ✅ Clickjacking prevention
- ✅ Secure cookie handling

## 📝 Admin Panel Features
Access the admin panel to:
- Add/edit/delete products
- Manage product categories
- View and manage orders
- Manage user accounts
- Upload carousel images

## 🎯 Use Cases
Perfect for:
- Small to medium e-commerce businesses
- Online retail stores
- Product showcase websites
- Learning Django development
- Portfolio projects

## ⚙️ Customization
To customize the application:
1. Modify templates in `app/templates/`
2. Update static files in `static/`
3. Adjust models in `app/models.py`
4. Customize admin interface in `app/admin.py`

## 📦 Dependencies
Core dependencies:
- Django (Python web framework)
- SQLite3 (comes with Python)

## 🚨 Important Notes
- Change the `SECRET_KEY` before deploying to production
- Set `DEBUG = False` in production
- Configure a production-ready database (PostgreSQL, MySQL)
- Set up proper static file serving (nginx, Apache)
- Enable HTTPS for production deployment
- Update `ALLOWED_HOSTS` with your domain

## 📖 Additional Information
- **Admin Site Header**: "JiyashCreation"
- **Admin Site Title**: "Jiyash Admin"
- **Index Title**: "Admin Panel"

## 🔄 Development Workflow
1. Make changes to code
2. Run migrations if models changed: `python manage.py makemigrations && python manage.py migrate`
3. Test locally
4. Collect static files before deployment
5. Deploy to production server

---

**Created by**: JiyashCreation Team
**Framework**: Django
**License**: [Specify your license]
**Status**: Active Development
