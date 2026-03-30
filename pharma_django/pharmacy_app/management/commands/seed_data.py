"""
Management command to seed the database with initial pharmacy data.
Run with: python manage.py seed_data
"""

import datetime
import random

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from pharmacy_app.models import (
    GenericName,
    Medicine,
    MedicinePresentation,
    Sale,
    SaleItem,
    Supplier,
)


class Command(BaseCommand):
    help = "Seed initial pharmacy data"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Seeding database..."))

        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@pharmacy.com", "admin123")
            self.stdout.write("Created admin user: admin / admin123")

        presentations = [
            "Tablet",
            "Capsule",
            "Syrup",
            "Injection",
            "Cream",
            "Gel",
            "Eye Drops",
            "Ear Drops",
            "Inhaler",
            "Powder",
            "Suspension",
            "Ointment",
            "Lotion",
            "Patch",
            "Suppository",
        ]
        for presentation in presentations:
            MedicinePresentation.objects.get_or_create(name=presentation)
        self.stdout.write(f"Created or verified {len(presentations)} presentations")

        generics = [
            ("Paracetamol", "Analgesic and antipyretic"),
            ("Ibuprofen", "NSAID anti-inflammatory"),
            ("Amoxicillin", "Penicillin-type antibiotic"),
            ("Cetirizine", "Antihistamine for allergies"),
            ("Omeprazole", "Proton pump inhibitor for acidity"),
            ("Metformin", "Biguanide for type 2 diabetes"),
            ("Atorvastatin", "Statin for high cholesterol"),
            ("Amlodipine", "Calcium channel blocker for BP"),
            ("Azithromycin", "Macrolide antibiotic"),
            ("Diclofenac", "NSAID for pain and inflammation"),
            ("Pantoprazole", "Proton pump inhibitor"),
            ("Ciprofloxacin", "Fluoroquinolone antibiotic"),
            ("Salbutamol", "Beta-2 agonist bronchodilator"),
            ("Loratadine", "Non-drowsy antihistamine"),
            ("Ranitidine", "H2 blocker for ulcers"),
            ("Doxycycline", "Tetracycline antibiotic"),
            ("Metronidazole", "Antiprotozoal and antibacterial"),
            ("Aspirin", "Analgesic and antiplatelet"),
            ("Clopidogrel", "Antiplatelet agent"),
            ("Losartan", "ARB for hypertension"),
            ("Glibenclamide", "Sulfonylurea for diabetes"),
            ("Insulin", "Hormone for diabetes management"),
            ("Vitamin C", "Ascorbic acid supplement"),
            ("Vitamin D3", "Cholecalciferol supplement"),
            ("Calcium", "Mineral supplement"),
            ("Aceclofenac", "NSAID for pain and inflammation"),
            ("Montelukast", "Anti-allergic leukotriene receptor antagonist"),
            ("Ondansetron", "Antiemetic for nausea and vomiting"),
            ("Domperidone", "Prokinetic antiemetic"),
            ("Loperamide", "Antidiarrheal agent"),
            ("Lactulose", "Osmotic laxative"),
            ("Clotrimazole", "Antifungal medication"),
            ("Fluconazole", "Systemic antifungal"),
            ("Mupirocin", "Topical antibacterial"),
            ("Carboxymethylcellulose", "Lubricating eye drops"),
            ("Moxifloxacin", "Broad spectrum antibiotic"),
            ("Olopatadine", "Antihistamine eye drops"),
            ("Dicyclomine", "Antispasmodic for abdominal pain"),
            ("Antacid", "Acid neutralizing agent"),
            ("Telmisartan", "ARB for hypertension"),
            ("Glimepiride", "Sulfonylurea for diabetes"),
            ("Rosuvastatin", "Statin for lipid lowering"),
            ("Cefixime", "Cephalosporin antibiotic"),
            ("Amoxyclav", "Amoxicillin with clavulanate"),
            ("Probiotic", "Supports gut flora balance"),
            ("Levocetirizine", "Antihistamine for allergy relief"),
            ("Fexofenadine", "Non-sedating antihistamine"),
            ("Budesonide", "Corticosteroid for respiratory inflammation"),
            ("Ipratropium", "Bronchodilator for airway opening"),
            ("Ambroxol", "Mucolytic expectorant"),
            ("Dextromethorphan", "Cough suppressant"),
            ("Guaifenesin", "Expectorant for productive cough"),
            ("Bromhexine", "Mucolytic for chest congestion"),
            ("Naproxen", "NSAID pain reliever"),
            ("Melatonin", "Sleep support supplement"),
            ("Clonazepam", "Anxiolytic and anticonvulsant"),
            ("Alprazolam", "Anxiolytic for anxiety"),
            ("Sitagliptin", "DPP-4 inhibitor for diabetes"),
            ("Enalapril", "ACE inhibitor for blood pressure"),
            ("Atenolol", "Beta blocker for blood pressure"),
            ("Simvastatin", "Statin for cholesterol control"),
            ("Oral Rehydration Salts", "Electrolyte replacement for dehydration"),
            ("Terbinafine", "Antifungal medication"),
            ("Adapalene", "Topical retinoid for acne"),
            ("Benzoyl Peroxide", "Topical acne treatment"),
            ("Mometasone", "Topical steroid for skin inflammation"),
            ("Ciprofloxacin Ear Drops", "Antibiotic ear drops"),
            ("Fusidic Acid", "Topical antibiotic for skin infection"),
            ("Ispaghula", "Bulk-forming laxative"),
            ("Bisacodyl", "Stimulant laxative"),
        ]
        generic_map = {}
        for name, description in generics:
            obj, _ = GenericName.objects.get_or_create(
                name=name,
                defaults={"description": description},
            )
            generic_map[name] = obj
        self.stdout.write(f"Created or verified {len(generics)} generic names")

        suppliers_data = [
            ("Sun Pharmaceuticals Ltd", "Rajesh Sharma", "9876543210", "info@sunpharma.com", "Mumbai, Maharashtra", 0),
            ("Cipla Ltd", "Priya Patel", "9123456789", "contact@cipla.com", "Pune, Maharashtra", 15000),
            ("Dr Reddys Laboratories", "Anand Kumar", "9234567890", "supply@drreddys.com", "Hyderabad, Telangana", 0),
            ("Lupin Ltd", "Meena Gupta", "9345678901", "orders@lupin.com", "Mumbai, Maharashtra", 8500),
            ("Mankind Pharma", "Suresh Nair", "9456789012", "info@mankind.com", "New Delhi", 0),
        ]
        supplier_map = {}
        for company_name, contact_person, phone, email, address, previous_due in suppliers_data:
            obj, _ = Supplier.objects.get_or_create(
                company_name=company_name,
                defaults={
                    "contact_person": contact_person,
                    "phone": phone,
                    "email": email,
                    "address": address,
                    "previous_due": previous_due,
                },
            )
            supplier_map[company_name] = obj
        self.stdout.write(f"Created or verified {len(suppliers_data)} suppliers")

        tablet = MedicinePresentation.objects.get(name="Tablet")
        capsule = MedicinePresentation.objects.get(name="Capsule")
        syrup = MedicinePresentation.objects.get(name="Syrup")
        inhaler = MedicinePresentation.objects.get(name="Inhaler")
        gel = MedicinePresentation.objects.get(name="Gel")

        medicines_data = [
            ("Crocin 500mg", "Paracetamol", tablet, "500mg", 8, 15, 250, 18, "Sun Pharmaceuticals Ltd", "Fever and pain relief"),
            ("Dolo 650", "Paracetamol", tablet, "650mg", 10, 18, 180, 14, "Mankind Pharma", "Antipyretic for fever"),
            ("Ibugesic Plus Syrup", "Ibuprofen", syrup, "100ml", 28, 45, 90, 10, "Cipla Ltd", "Anti-inflammatory pain syrup"),
            ("Mox 500", "Amoxicillin", capsule, "500mg", 42, 70, 140, 20, "Dr Reddys Laboratories", "Broad spectrum antibiotic"),
            ("Cetirizine 10mg", "Cetirizine", tablet, "10mg", 5, 10, 300, 24, "Sun Pharmaceuticals Ltd", "Non-drowsy antihistamine for allergies"),
            ("Omez 20", "Omeprazole", capsule, "20mg", 14, 25, 220, 16, "Cipla Ltd", "Gastric acid secretion inhibitor"),
            ("Glycomet 500", "Metformin", tablet, "500mg", 12, 22, 260, 22, "Sun Pharmaceuticals Ltd", "Type 2 diabetes management"),
            ("Atorva 10", "Atorvastatin", tablet, "10mg", 22, 40, 200, 20, "Lupin Ltd", "Cholesterol lowering"),
            ("Amlokind 5", "Amlodipine", tablet, "5mg", 16, 28, 230, 18, "Mankind Pharma", "Blood pressure control"),
            ("Azithral 500", "Azithromycin", tablet, "500mg", 82, 135, 110, 16, "Cipla Ltd", "Macrolide antibiotic for infections"),
            ("Voveran Gel", "Diclofenac", gel, "30g", 55, 95, 70, 12, "Cipla Ltd", "Topical pain relief gel"),
            ("Pan 40", "Pantoprazole", tablet, "40mg", 20, 35, 240, 20, "Dr Reddys Laboratories", "Acid reflux management"),
            ("Ciplox 500", "Ciprofloxacin", tablet, "500mg", 32, 55, 160, 18, "Cipla Ltd", "Broad spectrum antibiotic"),
            ("Asthalin Inhaler", "Salbutamol", inhaler, "200 doses", 175, 280, 45, 24, "Cipla Ltd", "Bronchodilator for asthma"),
            ("Lorfast 10mg", "Loratadine", tablet, "10mg", 8, 15, 310, 20, "Sun Pharmaceuticals Ltd", "Non-drowsy allergy tablet"),
            ("Doxycycline 100mg", "Doxycycline", capsule, "100mg", 18, 30, 150, 16, "Dr Reddys Laboratories", "Tetracycline for infections"),
            ("Metrogyl 400", "Metronidazole", tablet, "400mg", 12, 22, 200, 20, "Mankind Pharma", "Anaerobic infections treatment"),
            ("Vitamin C 500mg", "Vitamin C", tablet, "500mg", 6, 12, 400, 24, "Sun Pharmaceuticals Ltd", "Immune system supplement"),
            ("D-Rise 60K", "Vitamin D3", capsule, "60000 IU", 45, 75, 120, 20, "Lupin Ltd", "Vitamin D3 supplement sachet"),
            ("Shelcal 500", "Calcium", tablet, "500mg", 18, 30, 180, 22, "Dr Reddys Laboratories", "Calcium supplement"),
            ("Glynase 5mg", "Glibenclamide", tablet, "5mg", 10, 18, 200, 20, "Cipla Ltd", "Sulfonylurea for diabetes"),
            ("Aspirin 75mg", "Aspirin", tablet, "75mg", 5, 10, 350, 24, "Mankind Pharma", "Antiplatelet for heart health"),
            ("Clopivas 75", "Clopidogrel", tablet, "75mg", 30, 50, 180, 20, "Sun Pharmaceuticals Ltd", "Antiplatelet therapy"),
            ("Losartan 50mg", "Losartan", tablet, "50mg", 22, 38, 210, 18, "Dr Reddys Laboratories", "ARB for hypertension"),
            ("Ranitidine 150mg", "Ranitidine", tablet, "150mg", 8, 15, 0, 12, "Lupin Ltd", "H2 blocker currently out of stock"),
            ("Aceclo Plus", "Aceclofenac", tablet, "100mg", 24, 42, 140, 16, "Sun Pharmaceuticals Ltd", "Pain and inflammation relief"),
            ("Montair 10", "Montelukast", tablet, "10mg", 14, 28, 160, 18, "Cipla Ltd", "Allergy and asthma support"),
            ("Emeset 4", "Ondansetron", tablet, "4mg", 18, 34, 110, 14, "Dr Reddys Laboratories", "Controls nausea and vomiting"),
            ("Domstal", "Domperidone", tablet, "10mg", 12, 24, 125, 14, "Mankind Pharma", "Anti-nausea and gastric motility aid"),
            ("Eldoper", "Loperamide", capsule, "2mg", 10, 22, 90, 16, "Lupin Ltd", "Used in loose motion and diarrhea"),
            ("Duphalac Syrup", "Lactulose", syrup, "100ml", 65, 110, 55, 10, "Sun Pharmaceuticals Ltd", "Relieves constipation gently"),
            ("Candid Cream", "Clotrimazole", MedicinePresentation.objects.get(name="Cream"), "20g", 38, 68, 80, 14, "Cipla Ltd", "Topical antifungal cream"),
            ("Fluka 150", "Fluconazole", tablet, "150mg", 22, 45, 75, 18, "Dr Reddys Laboratories", "Systemic antifungal tablet"),
            ("T-Bact Ointment", "Mupirocin", MedicinePresentation.objects.get(name="Ointment"), "5g", 72, 125, 60, 12, "Sun Pharmaceuticals Ltd", "Topical antibacterial ointment"),
            ("Refresh Tears", "Carboxymethylcellulose", MedicinePresentation.objects.get(name="Eye Drops"), "10ml", 95, 145, 70, 10, "Lupin Ltd", "Lubricating eye drops for dryness"),
            ("Moxicip Eye Drops", "Moxifloxacin", MedicinePresentation.objects.get(name="Eye Drops"), "5ml", 78, 128, 65, 12, "Cipla Ltd", "Antibiotic eye drops"),
            ("Olopat Eye Drops", "Olopatadine", MedicinePresentation.objects.get(name="Eye Drops"), "5ml", 88, 142, 50, 12, "Sun Pharmaceuticals Ltd", "Anti-allergy eye drops"),
            ("Cyclopam", "Dicyclomine", tablet, "20mg", 16, 30, 115, 16, "Mankind Pharma", "Abdominal cramp relief"),
            ("Gelusil", "Antacid", tablet, "Tablet", 6, 12, 220, 18, "Lupin Ltd", "Fast relief in acidity and gas"),
            ("Telma 40", "Telmisartan", tablet, "40mg", 28, 48, 135, 18, "Sun Pharmaceuticals Ltd", "Blood pressure management"),
            ("Amaryl 1", "Glimepiride", tablet, "1mg", 20, 34, 145, 20, "Cipla Ltd", "Blood sugar control"),
            ("Rosuvas 10", "Rosuvastatin", tablet, "10mg", 24, 46, 125, 18, "Dr Reddys Laboratories", "Lipid lowering statin"),
            ("Taxim-O 200", "Cefixime", tablet, "200mg", 48, 85, 95, 14, "Mankind Pharma", "Oral cephalosporin antibiotic"),
            ("Augmentin 625", "Amoxyclav", tablet, "625mg", 85, 145, 90, 14, "Sun Pharmaceuticals Ltd", "Broad spectrum antibiotic combination"),
            ("Vizylac", "Probiotic", capsule, "Capsule", 12, 24, 130, 16, "Cipla Ltd", "Supports gut health during diarrhea"),
            ("Xyzal 5", "Levocetirizine", tablet, "5mg", 12, 24, 150, 18, "Sun Pharmaceuticals Ltd", "Fast allergy relief tablet"),
            ("Allegra 120", "Fexofenadine", tablet, "120mg", 18, 36, 120, 18, "San Pharmaceuticals Ltd", "Non-drowsy allergy medicine"),
            ("Budecort Respules", "Budesonide", MedicinePresentation.objects.get(name="Suspension"), "2ml", 95, 155, 60, 12, "Cipla Ltd", "Nebulizer suspension for asthma"),
            ("Duolin Inhaler", "Ipratropium", inhaler, "200 doses", 190, 295, 42, 20, "Cipla Ltd", "Bronchodilator inhaler for COPD and asthma"),
            ("Mucosolvan Syrup", "Ambroxol", syrup, "100ml", 42, 74, 98, 14, "Mankind Pharma", "Relieves chest congestion"),
            ("Benadryl Cough", "Dextromethorphan", syrup, "100ml", 58, 96, 88, 12, "Johnson Pharma", "Dry cough suppressant syrup"),
            ("Ascoril LS", "Guaifenesin", syrup, "100ml", 65, 108, 92, 12, "Lupin Ltd", "Productive cough syrup"),
            ("Bromhexine Syrup", "Bromhexine", syrup, "100ml", 38, 68, 85, 12, "Mankind Pharma", "Mucolytic syrup for cough"),
            ("Naprosyn 250", "Naproxen", tablet, "250mg", 24, 42, 110, 16, "Dr Reddys Laboratories", "Pain relief for headache and joint pain"),
            ("Meloset 3", "Melatonin", tablet, "3mg", 14, 28, 76, 18, "Sun Pharmaceuticals Ltd", "Sleep support tablet"),
            ("Clonotril 0.5", "Clonazepam", tablet, "0.5mg", 20, 38, 84, 20, "Cipla Ltd", "For anxiety and sleep disorders"),
            ("Alprax 0.25", "Alprazolam", tablet, "0.25mg", 18, 34, 90, 20, "Lupin Ltd", "Anxiety relief tablet"),
            ("Januvia 50", "Sitagliptin", tablet, "50mg", 42, 72, 96, 18, "Sun Pharmaceuticals Ltd", "Diabetes control tablet"),
            ("Envas 5", "Enalapril", tablet, "5mg", 16, 30, 128, 20, "Dr Reddys Laboratories", "ACE inhibitor for BP control"),
            ("Aten 50", "Atenolol", tablet, "50mg", 14, 27, 140, 20, "Mankind Pharma", "Beta blocker for blood pressure"),
            ("Simvotin 10", "Simvastatin", tablet, "10mg", 18, 34, 118, 18, "Lupin Ltd", "Cholesterol lowering tablet"),
            ("Electral Sachet", "Oral Rehydration Salts", MedicinePresentation.objects.get(name="Powder"), "21g", 12, 22, 160, 24, "Cipla Ltd", "Prevents dehydration in diarrhea and vomiting"),
            ("Terbest Cream", "Terbinafine", MedicinePresentation.objects.get(name="Cream"), "15g", 45, 78, 72, 14, "Sun Pharmaceuticals Ltd", "Antifungal cream"),
            ("Adaferin Gel", "Adapalene", gel, "15g", 58, 96, 60, 14, "Galderma Pharma", "Topical acne gel"),
            ("Persol AC", "Benzoyl Peroxide", gel, "20g", 36, 64, 70, 14, "Johnson Pharma", "Acne treatment gel"),
            ("Elocon Cream", "Mometasone", MedicinePresentation.objects.get(name="Cream"), "15g", 52, 88, 62, 14, "Sun Pharmaceuticals Ltd", "Topical steroid cream"),
            ("Cipro Ear Drops", "Ciprofloxacin Ear Drops", MedicinePresentation.objects.get(name="Ear Drops"), "10ml", 66, 112, 54, 12, "Cipla Ltd", "Ear drops for bacterial ear infection"),
            ("Fucidin Cream", "Fusidic Acid", MedicinePresentation.objects.get(name="Cream"), "15g", 62, 105, 58, 14, "Lupin Ltd", "Topical antibiotic cream"),
            ("Isabgol Husk", "Ispaghula", MedicinePresentation.objects.get(name="Powder"), "100g", 44, 76, 95, 18, "Dabur Pharma", "Fiber supplement for constipation"),
            ("Dulcolax 5", "Bisacodyl", tablet, "5mg", 10, 21, 105, 18, "Sanofi India", "Stimulant laxative tablet"),
        ]

        today = datetime.date.today()
        created_medicine_count = 0
        for name, generic_name, presentation, volume, unit_price, selling_price, quantity, expire_months, supplier_name, description in medicines_data:
            if Medicine.objects.filter(name=name).exists():
                continue

            expire_date = today + datetime.timedelta(days=30 * expire_months)
            if random.random() < 0.1:
                expire_date = today + datetime.timedelta(days=random.randint(5, 25))

            Medicine.objects.create(
                name=name,
                generic_name=generic_map.get(generic_name),
                presentation=presentation,
                volume=volume,
                unit_price=unit_price,
                selling_price=selling_price,
                quantity=quantity,
                expire_date=expire_date,
                supplier=supplier_map.get(supplier_name),
                purchase_paid=unit_price * quantity,
                purchase_due=0,
                description=description,
            )
            created_medicine_count += 1
        self.stdout.write(f"Created {created_medicine_count} medicines")

        available_medicines = list(Medicine.objects.filter(quantity__gt=0)[:10])
        if available_medicines and not Sale.objects.exists():
            admin_user = User.objects.filter(is_superuser=True).first()
            for i in range(20):
                sale_date = timezone.now() - datetime.timedelta(days=random.randint(0, 30))
                sale = Sale.objects.create(
                    invoice_number=Sale.generate_invoice_number(),
                    customer_name=random.choice(["Ravi Kumar", "Priya Singh", "Mohammed Ali", "Sunita Devi", "Walk-in"]),
                    customer_email=f"patient{i}@email.com",
                    sale_date=sale_date,
                    discount=random.choice([0, 5, 10, 0, 0]),
                    paid_amount=0,
                    created_by=admin_user,
                )
                total = 0
                for _ in range(random.randint(1, 3)):
                    medicine = random.choice(available_medicines)
                    quantity = random.randint(1, 3)
                    line_total = float(medicine.selling_price) * quantity
                    SaleItem.objects.create(
                        sale=sale,
                        medicine=medicine,
                        quantity=quantity,
                        unit_price=medicine.selling_price,
                        discount=0,
                        sub_total=line_total,
                    )
                    total += line_total
                    if medicine.quantity >= quantity:
                        medicine.quantity -= quantity
                        medicine.save(update_fields=["quantity", "updated_at"])
                sale.total_amount = total
                sale.sub_total = total - float(sale.discount)
                sale.paid_amount = sale.sub_total
                sale.save()
            self.stdout.write("Created 20 sample sales")

        self.stdout.write(self.style.SUCCESS("Database seeded successfully"))
        self.stdout.write(self.style.SUCCESS("Login: admin / admin123"))
        self.stdout.write(self.style.SUCCESS("Run: python manage.py runserver"))
