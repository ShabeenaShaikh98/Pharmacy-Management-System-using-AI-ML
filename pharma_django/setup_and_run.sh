#!/bin/bash
# ═══════════════════════════════════════════════════════════
#  AL-HAMD Pharmacy Management System — Quick Setup Script
# ═══════════════════════════════════════════════════════════
set -e

echo ""
echo "╔════════════════════════════════════════════╗"
echo "║   AL-HAMD Pharmacy ML System — Setup      ║"
echo "╚════════════════════════════════════════════╝"
echo ""

# Step 1: Create virtual environment
echo "📦 Step 1: Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate
echo "✅ Virtual environment activated"

# Step 2: Install dependencies
echo ""
echo "📥 Step 2: Installing dependencies..."
pip install -r requirements.txt -q
echo "✅ Dependencies installed"

# Step 3: Create PostgreSQL database
echo ""
echo "🐘 Step 3: Setting up PostgreSQL database..."
echo "   Make sure PostgreSQL is running and 'postgres' user exists."
psql -U postgres -c "CREATE DATABASE pharmacy_db;" 2>/dev/null && echo "✅ Database 'pharmacy_db' created" || echo "ℹ️  Database may already exist"

# Step 4: Run migrations
echo ""
echo "🔄 Step 4: Running Django migrations..."
python manage.py makemigrations
python manage.py migrate
echo "✅ Migrations complete"

# Step 5: Seed data
echo ""
echo "🌱 Step 5: Seeding initial data..."
python manage.py seed_data
echo "✅ Data seeded"

# Step 6: Collect static files
echo ""
echo "📁 Step 6: Collecting static files..."
python manage.py collectstatic --noinput --verbosity 0
echo "✅ Static files collected"

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  ✅ Setup Complete! Starting server...           ║"
echo "║                                                  ║"
echo "║  🌐 URL:      http://localhost:8000              ║"
echo "║  👤 Login:    admin / admin123                   ║"
echo "║  🤖 AI Chat:  Click robot icon (bottom-right)    ║"
echo "║  📊 Admin:    http://localhost:8000/admin/       ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

python manage.py runserver 0.0.0.0:8000
