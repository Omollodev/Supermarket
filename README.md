# Supermarket Management System

A comprehensive Django-based supermarket management system with role-based authentication, staff attendance tracking, billing system, and inventory management.

## Features

### 🔐 User Authentication System
- **Role-based access control** with three roles: Admin, Manager, and Staff
- **Secure registration and login** with session management
- **Password reset functionality** via email verification
- **Profile management** for updating personal details
- **Custom user model** with additional fields

### ⏰ Staff Attendance and Wage Tracking
- **Clock in/out system** with accurate time tracking
- **Automatic wage calculation** based on configurable hourly rates
- **Attendance history** with filtering options
- **Monthly wage summaries** with payment tracking
- **Manager dashboard** for monitoring staff attendance

### 💰 Billing and Payment System
- **Invoice generation** with itemized purchases
- **Multiple payment methods** support (Cash, Card, Mobile, QR Code)
- **Tax and discount calculations**
- **Printable PDF receipts** with professional formatting
- **Accounts receivable/payable** ledgers
- **Payment tracking** and status management
- **QR code generation** for mobile payments

### 📦 Inventory Management
- **Product catalog** with categories
- **Stock level monitoring** with low-stock alerts
- **SKU and barcode support**
- **Profit margin calculations**
- **Product image management**

### 🎨 Modern UI/UX
- **Bootstrap 5** responsive design
- **Font Awesome** icons
- **Jazzmin** admin interface
- **Mobile-friendly** design
- **Dark/light theme** support

## Technology Stack

- **Backend**: Django 4.2.7
- **Database**: MySQL
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Admin Interface**: Django Jazzmin
- **PDF Generation**: ReportLab
- **QR Codes**: qrcode library
- **Payment Processing**: Stripe integration ready

## Installation

### Prerequisites
- Python 3.8+
- MySQL 5.7+
- pip (Python package manager)

### Quick Setup

1. **Clone the repository**
```bash
git clone https://github.com/Omollodev/Supermarket.git
cd supermarket-management
```

2. **Run the setup script**
```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

3. **Update configuration**
   - Edit `.env` file with your database and email settings
   - Configure MySQL database connection

4. **Start the development server**
```bash
python manage.py runserver
```

5. **Access the application**
   - Main application: http://127.0.0.1:8000
   - Admin panel: http://127.0.0.1:8000/admin

### Manual Installation

1. **Create virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  
# On Windows: 
venv\Scripts\activate
```

2. **Install dependencies**
```bash
pip3 install -r requirements.txt
```

3. **Configure database**
   - Create MySQL database: `supermarket_db`
   - Update `.env` file with database credentials

4. **Run migrations**
```bash
python3 manage.py makemigrations \
python3 manage.py migrate
```

5. **Create superuser**
```bash
python3 manage.py createsuperuser
```

## Configuration

### Environment Variables (.env)
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DB_NAME=supermarket_db
DB_USER=root
DB_PASSWORD=your-mysql-password
DB_HOST=localhost
DB_PORT=3306
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_key
STRIPE_SECRET_KEY=sk_test_your_stripe_key
```

### Database Setup
```sql
CREATE DATABASE supermarket_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'supermarket_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON supermarket_db.* TO 'supermarket_user'@'localhost';
FLUSH PRIVILEGES;
```

## Usage

### Default Login Credentials
- **Admin**: `admin` / `pass@123`
- **Manager**: `manager` / `manager123`
- **Staff**: `staff1` / `staff123`

### User Roles and Permissions

#### Admin
- Full system access
- User management
- System configuration
- All billing and inventory operations
- Staff attendance monitoring

#### Manager
- Staff attendance monitoring
- Billing and invoice management
- Inventory management
- Customer management
- Reports and analytics

#### Staff
- Personal attendance tracking
- Clock in/out functionality
- View personal wage summaries
- Basic billing operations
- Profile management

### Key Workflows

#### Staff Attendance
1. Staff logs in to the system
2. Clicks "Clock In" on dashboard
3. Works their shift
4. Clicks "Clock Out" when leaving
5. System automatically calculates hours and wages

#### Invoice Creation
1. Navigate to Billing → Create Invoice
2. Select or create customer
3. Add items to invoice
4. Apply taxes and discounts
5. Process payment
6. Generate receipt

#### Inventory Management
1. Add product categories
2. Create products with SKU and pricing
3. Monitor stock levels
4. Receive low-stock alerts
5. Update inventory as needed

## API Endpoints

### Authentication
- `POST /accounts/login/` - User login
- `POST /accounts/logout/` - User logout
- `POST /accounts/register/` - User registration
- `GET /accounts/profile/` - User profile

### Attendance
- `POST /dashboard/clock-in/` - Clock in
- `POST /dashboard/clock-out/` - Clock out
- `GET /dashboard/history/` - Attendance history
- `GET /dashboard/wages/` - Wage summary

### Billing
- `GET /billing/` - Billing dashboard
- `POST /billing/invoices/create/` - Create invoice
- `GET /billing/invoices/<id>/` - Invoice details
- `POST /billing/invoices/<id>/payment/` - Add payment

## Customization

### Adding New User Roles
1. Update `ROLE_CHOICES` in `accounts/models.py`
2. Modify permission checks in views
3. Update navigation templates
4. Add role-specific functionality

### Custom Payment Methods
1. Add new choices to `PAYMENT_METHOD_CHOICES`
2. Implement payment processing logic
3. Update billing forms and templates
4. Add validation and error handling

### Email Configuration
Configure SMTP settings in `.env`:
```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

## Deployment

### Production Checklist
- [ ] Set `DEBUG=False` in settings
- [ ] Configure production database
- [ ] Set up static file serving
- [ ] Configure email backend
- [ ] Set up SSL/HTTPS
- [ ] Configure backup strategy
- [ ] Set up monitoring and logging

### Docker Deployment
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
docker build -t harny:latest
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Email: support@supermarket-system.com
- Documentation: [Wiki](link-to-wiki)

## Changelog

### Version 1.0.0
- Initial release
- User authentication system
- Staff attendance tracking
- Billing and payment system
- Inventory management
- Responsive UI with Bootstrap 5
- PDF receipt generation
- QR code support

---

**Built with using Django and Bootstrap**
