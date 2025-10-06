# JiyashCreation - Django E-commerce Website

A secure and optimized Django e-commerce platform for jewelry products (Gold, Silver, and Imitation).

## Features

- **Multi-category Product Management**: Gold, Silver, and Imitation jewelry
- **JWT Authentication**: Secure user authentication system
- **Country-based Pricing**: Dynamic pricing based on user location
- **Wishlist & Cart**: Full shopping cart functionality with discounts
- **Admin Panel**: Comprehensive admin interface for product management
- **Responsive Design**: Mobile-friendly user interface
- **Security Hardened**: Following Django security best practices

## Security Improvements Made

### 1. Environment Variables
- Moved sensitive settings to environment variables
- Added `.env.example` template
- Secure SECRET_KEY management

### 2. Security Headers
- HSTS (HTTP Strict Transport Security)
- XSS Protection
- Content Type Nosniff
- Secure cookies in production
- CSRF protection

### 3. Authentication Security
- Secure JWT token handling
- Password hashing with Django's built-in hashers
- Session security improvements
- Removed sensitive data from API responses

### 4. Database Optimizations
- Added `select_related()` for foreign key queries
- Optimized N+1 query problems
- Efficient ContentType handling

### 5. Code Quality
- Removed duplicate functions
- Cleaned up unused imports
- Added proper error logging
- Improved exception handling

## Installation

### Prerequisites
- Python 3.8+
- pip
- Virtual environment (recommended)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd jiyash
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   
   **Option A: Quick Setup (Recommended)**
   ```bash
   python setup.py
   ```
   
   **Option B: Manual Setup**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` file with your settings:
   ```
   SECRET_KEY=your-generated-secret-key-here
   DEBUG=True  # Set to False in production
   ALLOWED_HOSTS=localhost,127.0.0.1
   ```

5. **Database Setup**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create Superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Collect Static Files** (for production)
   ```bash
   python manage.py collectstatic
   ```

8. **Run Development Server**
   ```bash
   python manage.py runserver
   ```

## Production Deployment

### Security Checklist

1. **Environment Variables**
   - Set `DEBUG=False`
   - Use a strong, unique `SECRET_KEY`
   - Configure proper `ALLOWED_HOSTS`

2. **Database**
   - Use PostgreSQL or MySQL instead of SQLite
   - Configure database backups

3. **Static Files**
   - Configure proper static file serving (nginx/Apache)
   - Set up CDN for media files

4. **SSL/HTTPS**
   - Enable SSL certificates
   - Set `SECURE_SSL_REDIRECT=True`

5. **Monitoring**
   - Set up error monitoring (Sentry)
   - Configure log rotation
   - Monitor performance

### Recommended Production Settings

Add to your production `.env`:
```
DEBUG=False
SECURE_SSL_REDIRECT=True
SECURE_PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

## API Endpoints

### Authentication
- `POST /login/` - User login
- `POST /signup/` - User registration
- `POST /forgot-password/` - Password reset request
- `POST /api/verify-reset-otp/` - OTP verification
- `POST /api/reset-password-otp/` - Password reset with OTP

### Products
- `GET /` - Homepage with featured products
- `GET /shop-all/` - All products with filtering
- `GET /product/<type>/<id>/` - Product details
- `GET /category/<type>/<id>/` - Category products
- `GET /subcategory/<type>/<id>/` - Subcategory products

### Cart & Wishlist
- `GET /cart/` - View cart
- `POST /cart/add/<id>/` - Add to cart
- `PUT /cart/update/<id>/` - Update cart item
- `DELETE /cart/remove/<id>/` - Remove from cart
- `GET /wishlist/` - View wishlist
- `POST /wishlist/add/<type>/<id>/` - Add to wishlist
- `DELETE /wishlist/remove/<type>/<id>/` - Remove from wishlist

### User Profile
- `GET /profile/` - User profile page
- `GET /api/profile/` - Get profile data
- `POST /api/profile/update/` - Update profile

## File Structure

```
jiyash/
├── app/                          # Main application
│   ├── management/commands/      # Custom Django commands
│   ├── migrations/              # Database migrations
│   ├── templates/app/           # HTML templates
│   ├── templatetags/            # Custom template tags
│   ├── admin.py                 # Admin configuration
│   ├── context_processors.py    # Template context processors
│   ├── managers.py              # Custom model managers
│   ├── middleware.py            # Custom middleware
│   ├── models.py                # Database models
│   ├── urls.py                  # URL patterns
│   └── views.py                 # View functions
├── jiyash/                      # Project settings
│   ├── settings.py              # Django settings
│   ├── urls.py                  # Root URL configuration
│   └── wsgi.py                  # WSGI configuration
├── static/                      # Static files
├── media/                       # User uploads
├── logs/                        # Application logs
├── .env.example                 # Environment template
├── requirements.txt             # Python dependencies
└── manage.py                    # Django management script
```

## Models

### Core Models
- **User**: Custom user model with address fields
- **Category**: Top-level categories (Gold, Silver, Imitation)
- **GoldCategory/SilverCategory/ImitationCategory**: Specific categories
- **GoldProduct/SilverProduct/ImitationProduct**: Product models
- **Cart**: Shopping cart items
- **Wishlist**: User wishlist items
- **Order**: Order management
- **CountryMultiplier**: Country-based pricing

### Key Features
- Generic foreign keys for flexible product relationships
- Active/inactive status management with cascading
- Country-based pricing system
- Comprehensive admin interface

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Security

If you discover any security vulnerabilities, please email [security@example.com] instead of using the issue tracker.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Email: support@jiyashcreation.com
- Documentation: [Link to docs]

## Changelog

### v2.0.0 (Current)
- **Security Hardening**: Implemented comprehensive security measures
- **Performance Optimization**: Added database query optimizations
- **Code Cleanup**: Removed duplicated code and improved structure
- **Environment Configuration**: Added proper environment variable support
- **Logging**: Implemented structured logging system
- **Documentation**: Added comprehensive setup and security documentation

### v1.0.0
- Initial release with basic e-commerce functionality
