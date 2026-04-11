# 💊 AL-HAMD Pharmacy Management System

> A full-stack Django + PostgreSQL pharmacy management system with AI chat assistant, ML recommendations, OCR prescription reading, and AG Grid-powered data tables.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 4.2 + Django REST Framework |
| Database | PostgreSQL |
| Frontend | HTML5 + CSS3 + Bootstrap 5 |
| Data Grid | AG Grid Community v31 |
| Charts | Chart.js 4 |
| ML Engine | scikit-learn (TF-IDF + KNN) |
| AI Chat | Custom NLP with Django ORM |
| OCR | pytesseract + Pillow |
| Icons | Bootstrap Icons |
| Fonts | Google Fonts (DM Sans + Space Grotesk) |

---

## 📁 Project Structure

```
pharma_django/
├── manage.py
├── requirements.txt
├── .env                          # Environment variables
├── setup_and_run.sh              # Quick setup script
│
├── pharmacy_project/             # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── pharmacy_app/                 # Main application
│   ├── models.py                 # All database models
│   ├── serializers.py            # DRF serializers
│   ├── views.py                  # Page views
│   ├── api_views.py              # REST API views
│   ├── urls.py                   # Page URLs
│   ├── api_urls.py               # API URLs
│   ├── admin.py                  # Django admin config
│   └── management/
│       └── commands/
│           └── seed_data.py      # Database seeder
│
├── ml_engine/                    # AI / ML modules
│   ├── chat_ai.py               # AI pharmacy chatbot
│   ├── recommender.py           # TF-IDF + KNN recommender
│   └── ocr_engine.py            # OCR prescription reader
│
├── templates/                    # HTML templates
│   ├── base.html                # Base layout + chat widget
│   ├── registration/
│   │   └── login.html
│   └── pharmacy_app/
│       ├── dashboard.html
│       ├── medicines.html
│       ├── generics.html
│       ├── suppliers.html
│       ├── inventory.html
│       ├── sales.html
│       ├── sales_list.html
│       ├── reports.html
│       ├── recommend.html
│       └── ocr.html
│
└── static/                       # Static assets
```

---

## 🚀 Quick Setup

### Prerequisites
- Python 3.10+
- PostgreSQL 14+
- pip

### 1. Clone and setup
```bash
cd pharma_django
chmod +x setup_and_run.sh
./setup_and_run.sh
```

### 2. Manual setup (if script fails)
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt

# Create PostgreSQL database
psql -U postgres -c "CREATE DATABASE pharmacy_db;"

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Seed initial data (medicines, suppliers, generics, sample sales)
python manage.py seed_data

# Start server
python manage.py runserver
```

### 3. Access the system
- **Main App**: http://localhost:8000
- **Login**: `admin` / `admin123`
- **Django Admin**: http://localhost:8000/admin/

---

## ✨ Features

### 📦 Inventory Management
- Full CRUD for medicines with AG Grid (sort, filter, export)
- Generic names management
- Medicine presentations (Tablet, Capsule, Syrup, etc.)
- Stock tracking with color-coded status badges
- Expiry date monitoring with alerts

### 🚚 Supplier Management
- CRUD for suppliers with AG Grid
- Track previous dues
- Link medicines to suppliers

### 🛒 Purchase / Restock
- Add purchase orders to restock inventory
- Auto-updates medicine quantity
- Track payment and due amounts
- Status tracking (Received / Pending / Partial)

### 💵 Sales & Billing
- Point-of-sale billing interface
- Multi-item cart
- Auto-deducts from stock
- Invoice generation
- Customer details tracking
- Discount support
- Change calculation

### 📊 Reports & Analytics
- Daily revenue trend chart (Chart.js)
- Stock distribution donut chart
- Medicine performance leaderboard (AG Grid)
- Daily sales summary (AG Grid)
- Date range filtering
- CSV export

### 🤖 AI Chat Assistant (PharmaBot)
- Floating chat widget (bottom-right)
- Natural language queries:
  - "Which medicines are out of stock?"
  - "Show expiring medicines"
  - "Today's sales revenue"
  - "Top selling medicines"
  - "Price of Crocin"
  - "Recommend fever medicine"
- Persistent chat history per user
- Quick-action buttons

### 🔬 ML Recommendation Engine
- **Algorithm**: TF-IDF + K-Nearest Neighbors (cosine similarity)
- Search by medicine name, generic name, symptom, or condition
- Built-in symptom mapping (fever → paracetamol, etc.)
- Real-time similarity scoring
- AG Grid table + card view
- Quick search tags (Fever, Antibiotic, Diabetes, etc.)

### 📋 OCR Prescription Reader
- Upload prescription image (uses pytesseract OCR)
- Paste prescription text manually
- Regex-based medicine name extraction
- ML-powered alternatives recommendation
- Recent prescriptions history

---

## 🔌 API Endpoints

All endpoints require authentication (session-based).

```
GET  /api/medicines/              — List medicines
POST /api/medicines/              — Create medicine
PUT  /api/medicines/{id}/         — Update medicine
DEL  /api/medicines/{id}/         — Delete medicine

GET  /api/generics/               — List generics
POST /api/generics/               — Create generic
GET  /api/suppliers/              — List suppliers
POST /api/suppliers/              — Create supplier

GET  /api/sales/                  — List sales
POST /api/sales/                  — Create sale (with items)
GET  /api/purchases/              — List purchases
POST /api/purchases/              — Add purchase

POST /api/chat/                   — Send chat message
GET  /api/chat/                   — Get chat history
DEL  /api/chat/                   — Clear chat history

GET  /api/recommend/?q=fever      — ML recommendations
POST /api/ocr/                    — Process prescription

GET  /api/stats/                  — Dashboard statistics
GET  /api/reports/sales-summary/  — Sales trend data
GET  /api/reports/medicine-performance/ — Medicine analytics
GET  /api/reports/stock-alerts/   — Stock/expiry alerts
```

---

## 🧠 ML Architecture

### Recommendation Engine (`ml_engine/recommender.py`)
```
Input Query
    ↓
Symptom Mapping (fever → paracetamol, ibuprofen...)
    ↓
TF-IDF Vectorization (name + generic + presentation + description)
    ↓
K-Nearest Neighbors (cosine distance, k=8)
    ↓
Similarity Scoring (0-100%)
    ↓
Ranked Results
```

### AI Chat (`ml_engine/chat_ai.py`)
```
User Message
    ↓
Intent Detection (keyword matching + regex)
    ↓
Django ORM Queries (real-time database data)
    ↓
Formatted Markdown Response
    ↓
Saved to ChatMessage model
```

---

## ⚙️ Environment Variables (`.env`)

```env
SECRET_KEY=your-secret-key
DEBUG=True
DB_NAME=pharmacy_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
ALLOWED_HOSTS=localhost,127.0.0.1
```

---

## 📝 License
MIT — Free to use and modify.


Sequence diagram: system me step-by-step interaction (kaun kis se baat karta hai)
Flowchart: process ka flow with decisions
DFD: data ka flow system me
ER diagram: database tables aur unke relations
Use case diagram: user system me kya actions karta hai