# 🛒 ZENTRO E-COMMERCE PLATFORM

A **Production-Oriented E-commerce Web Application** Built with **Flask**, Designed using **Industry-Grade Authentication, Security pPractices, and modular Architecture**.

This project is under **active development** and follows a **real-world incremental build approach** (features are added module-by-module).

---

## 🚀 Key Highlights

- 🔐 **Enterprise-grade authentication system**
- 🧑‍💼 **Dedicated Admin Panel with security controls**
- 📧 Email-based OTP & verification flows
- 🛡️ Security-first Design (rate limiting, account lock, Suspicious activity, audit logs)
- 🧱 Scalable & modular Flask architecture
- 🧪 Database-driven with structured relational schema
- 🔒 Planned Secure Payment Gateway Integration with Razorpay (In Progress)
  
---

## 📌 Project Status

> ⚠️ **This project is a WORK IN PROGRESS (WIP)**  
> Core Authentication & Security layers are complete.  
> Commerce features are under active development.

---

## ✅ Completed Features

### 👤 User (Customer) Side
- Signup with:
  - Password strength validation
  - Duplicate username/email protection
- Email verification with secure token
- Login with:
  - Rate limiting
  - Account lock after multiple failures
- Forgot password (OTP based)
- Reset password with OTP expiry validation
- Session management & forced logout on reset
- Suspicious Activity Detection (CAPTCHA V3)
- Profile management:
  - Update profile
  - Change password
  - Manage addresses
- Wishlist (add / view)
- Secure logout
- Full CSRF protection

---

### 🧑‍💼 Admin Panel (Security & Governance)
- Admin authentication flow:
  - Login / Forgot password / OTP verify / Reset password
- Admin account lock mechanism
- Admin activity logging
- 🔍 **Audit Logs** ✅ (Completed)
- 🛡️ **Security Health Monitoring** ✅ (Completed)

---

## ⏳ In-Progress / Pending Features

### 🧑‍💼 Admin Side (In Progress)
- Product management (Add / Edit / Delete)
- Product listing & Pagination
- Category management
- Inventory & stock tracking
- User management dashboard
- Order management workflow
- Reviews moderation
- Revenue & Order analytics
- Sales & Performance Dashboards

---

### 👤 User (Customer) Side (In Progress)
- Product cards & listings (partial)
- Add-to-cart functionality (partial)
- Product filters & search
- Product reviews & ratings (partial)
- Checkout flow
- Payment Gateway Integration with Razorpay
- Order placement & tracking

---

## 🗄️ Database Schema (Current)

The database schema is already structured and migrated.

```text
+------------------------------+
| Database Tables_in_zentro    |
+------------------------------+
| admin_activity_logs          |
| admin_otps                   |
| admins                       |
| alembic_version              |
| audit_insights               |
| cart_items                   |
| categories                   |
| login_activities             |
| order_items                  |
| orders                       |
| otps                         |
| product_ratings              |
| product_reviews              |
| products                     |
| user_addresses               |
| user_status_reasons          |
| users                        |
| wishlists                    |
+------------------------------+

⚠️ Some tables are fully wired, others are partially integrated and under development.

```
---
## 🧱 zentro-ecommerce Project Structure

```text
E-COMMERCE-PROJECT/
├─ app/                # Core Flask application
│  ├─ auth/            # User authentication
│  ├─ admin/           # Admin panel & security
│  ├─ main/            # Public storefront
│  ├─ services/        # Email, OTP, payments
│  ├─ models.py        # SQLAlchemy models
│  └─ extensions.py    # Flask extensions
│
├─ templates/          # Jinja2 templates
│  ├─ auth/            # User auth pages
│  ├─ user/            # Customer pages
│  ├─ admin/           # Admin dashboard
│  └─ components/      # Reusable UI components
│
├─ static/             # CSS, JS, images
├─ migrations/         # Database migrations
├─ scripts/            # Utility & admin scripts
├─ docker/             # Docker setup (dev/prod)
├─ tests/              # Unit & integration tests
│
├─ config.py           # Environment-based config
├─ app.py              # Local entrypoint
├─ wsgi.py             # Production WSGI entry
├─ requirements.txt
├─ .env.example        # Environment template
└─ README.md


📌 Folder structure is designed for scalability.
New modules will be added as development progresses.

```
---

## ⚙️ Environment Setup 

1️⃣ Clone the repository
git clone https://github.com/AtharvPanchal/zentro-ecommerce.git
cd zentro-ecommerce

2️⃣ Create virtual environment
python -m venv venv
venv\Scripts\activate   # Windows

3️⃣ Install dependencies
pip install -r requirements.txt

4️⃣ Configure environment variables
copy .env.example .env

Fill in:

- SECRET_KEY

- DATABASE credentials

- SMTP / Mail credentials

- reCAPTCHA keys

- Payment gateway keys (later)

>❗ .env is never committed (see .gitignore)

---

## ▶️ Run the Application

flask db upgrade
python app.py


Access:

User site → http://localhost:5000

Admin panel → /admin/login

---

### 🛡️ Security Practices Used

- CSRF protection (Flask-WTF)
- Rate limiting (Flask-Limiter)
- OTP-based password resets
- Session invalidation on password change
- Account lockout on brute-force attempts
- Email verification enforcement
- Secure password hashing
- Admin audit logging

---

## 🧠 Development Philosophy

This project follows:

✅ Incremental development <br>
✅ Production-first mindset <br>
✅ Security before features <br>
❌ No fake demo data <br>
❌ No hardcoded secrets <br>

> Features are pushed progressively, just like real industry projects.

---

## 📌 Roadmap

- Complete checkout & payment Gateway Integration with Razorpay
- Finish admin product & order workflows
- Advanced analytics dashboards
- Redis-backed OTP & session store
- Deployment (Docker + cloud)

---  

## 👨‍💻 Author

Atharv Dattaram Panchal  <br>
Engineering Student | Backend Developer   <br>
Focused on real-world systems, security & scalability  <br>

📧 Email: atharvpanchal2006@gmail.com  
🔗 GitHub: https://github.com/AtharvPanchal  

🔹 Tech Stack: Flask, SQLAlchemy, MySQL, HTML/CSS, JavaScript  
🔹 Interests: Backend Engineering, Security, System Design  
🔹 Learning: Payments, Distributed Systems, Production Deployment, Generative AI 


---



