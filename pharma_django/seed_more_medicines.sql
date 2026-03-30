BEGIN;

INSERT INTO pharmacy_app_supplier (company_name, contact_person, phone, email, address, previous_due, created_at)
SELECT 'Johnson Pharma', 'Support Team', '9000000001', 'contact@johnsonpharma.com', 'Mumbai, Maharashtra', 0, CURRENT_TIMESTAMP
WHERE NOT EXISTS (
    SELECT 1 FROM pharmacy_app_supplier WHERE company_name = 'Johnson Pharma'
);

INSERT INTO pharmacy_app_supplier (company_name, contact_person, phone, email, address, previous_due, created_at)
SELECT 'Galderma Pharma', 'Sales Desk', '9000000002', 'info@galderma.example', 'Bengaluru, Karnataka', 0, CURRENT_TIMESTAMP
WHERE NOT EXISTS (
    SELECT 1 FROM pharmacy_app_supplier WHERE company_name = 'Galderma Pharma'
);

INSERT INTO pharmacy_app_supplier (company_name, contact_person, phone, email, address, previous_due, created_at)
SELECT 'Dabur Pharma', 'Care Desk', '9000000003', 'orders@dabur.example', 'New Delhi', 0, CURRENT_TIMESTAMP
WHERE NOT EXISTS (
    SELECT 1 FROM pharmacy_app_supplier WHERE company_name = 'Dabur Pharma'
);

INSERT INTO pharmacy_app_supplier (company_name, contact_person, phone, email, address, previous_due, created_at)
SELECT 'Sanofi India', 'Enterprise Desk', '9000000004', 'orders@sanofi.example', 'Hyderabad, Telangana', 0, CURRENT_TIMESTAMP
WHERE NOT EXISTS (
    SELECT 1 FROM pharmacy_app_supplier WHERE company_name = 'Sanofi India'
);

INSERT INTO pharmacy_app_supplier (company_name, contact_person, phone, email, address, previous_due, created_at)
SELECT 'San Pharmaceuticals Ltd', 'Regional Sales', '9000000005', 'support@sanpharma.example', 'Pune, Maharashtra', 0, CURRENT_TIMESTAMP
WHERE NOT EXISTS (
    SELECT 1 FROM pharmacy_app_supplier WHERE company_name = 'San Pharmaceuticals Ltd'
);

INSERT INTO pharmacy_app_genericname (name, description, created_at)
SELECT 'Levocetirizine', 'Antihistamine for allergy relief', CURRENT_TIMESTAMP
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_genericname WHERE name = 'Levocetirizine');
INSERT INTO pharmacy_app_genericname (name, description, created_at)
SELECT 'Fexofenadine', 'Non-sedating antihistamine', CURRENT_TIMESTAMP
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_genericname WHERE name = 'Fexofenadine');
INSERT INTO pharmacy_app_genericname (name, description, created_at)
SELECT 'Budesonide', 'Corticosteroid for respiratory inflammation', CURRENT_TIMESTAMP
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_genericname WHERE name = 'Budesonide');
INSERT INTO pharmacy_app_genericname (name, description, created_at)
SELECT 'Ipratropium', 'Bronchodilator for airway opening', CURRENT_TIMESTAMP
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_genericname WHERE name = 'Ipratropium');
INSERT INTO pharmacy_app_genericname (name, description, created_at)
SELECT 'Ambroxol', 'Mucolytic expectorant', CURRENT_TIMESTAMP
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_genericname WHERE name = 'Ambroxol');
INSERT INTO pharmacy_app_genericname (name, description, created_at)
SELECT 'Dextromethorphan', 'Cough suppressant', CURRENT_TIMESTAMP
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_genericname WHERE name = 'Dextromethorphan');
INSERT INTO pharmacy_app_genericname (name, description, created_at)
SELECT 'Guaifenesin', 'Expectorant for productive cough', CURRENT_TIMESTAMP
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_genericname WHERE name = 'Guaifenesin');
INSERT INTO pharmacy_app_genericname (name, description, created_at)
SELECT 'Bromhexine', 'Mucolytic for chest congestion', CURRENT_TIMESTAMP
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_genericname WHERE name = 'Bromhexine');
INSERT INTO pharmacy_app_genericname (name, description, created_at)
SELECT 'Naproxen', 'NSAID pain reliever', CURRENT_TIMESTAMP
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_genericname WHERE name = 'Naproxen');
INSERT INTO pharmacy_app_genericname (name, description, created_at)
SELECT 'Melatonin', 'Sleep support supplement', CURRENT_TIMESTAMP
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_genericname WHERE name = 'Melatonin');
INSERT INTO pharmacy_app_genericname (name, description, created_at)
SELECT 'Clonazepam', 'Anxiolytic and anticonvulsant', CURRENT_TIMESTAMP
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_genericname WHERE name = 'Clonazepam');
INSERT INTO pharmacy_app_genericname (name, description, created_at)
SELECT 'Alprazolam', 'Anxiolytic for anxiety', CURRENT_TIMESTAMP
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_genericname WHERE name = 'Alprazolam');
INSERT INTO pharmacy_app_genericname (name, description, created_at)
SELECT 'Sitagliptin', 'DPP-4 inhibitor for diabetes', CURRENT_TIMESTAMP
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_genericname WHERE name = 'Sitagliptin');
INSERT INTO pharmacy_app_genericname (name, description, created_at)
SELECT 'Enalapril', 'ACE inhibitor for blood pressure', CURRENT_TIMESTAMP
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_genericname WHERE name = 'Enalapril');
INSERT INTO pharmacy_app_genericname (name, description, created_at)
SELECT 'Atenolol', 'Beta blocker for blood pressure', CURRENT_TIMESTAMP
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_genericname WHERE name = 'Atenolol');
INSERT INTO pharmacy_app_genericname (name, description, created_at)
SELECT 'Simvastatin', 'Statin for cholesterol control', CURRENT_TIMESTAMP
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_genericname WHERE name = 'Simvastatin');
INSERT INTO pharmacy_app_genericname (name, description, created_at)
SELECT 'Oral Rehydration Salts', 'Electrolyte replacement for dehydration', CURRENT_TIMESTAMP
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_genericname WHERE name = 'Oral Rehydration Salts');
INSERT INTO pharmacy_app_genericname (name, description, created_at)
SELECT 'Terbinafine', 'Antifungal medication', CURRENT_TIMESTAMP
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_genericname WHERE name = 'Terbinafine');
INSERT INTO pharmacy_app_genericname (name, description, created_at)
SELECT 'Adapalene', 'Topical retinoid for acne', CURRENT_TIMESTAMP
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_genericname WHERE name = 'Adapalene');
INSERT INTO pharmacy_app_genericname (name, description, created_at)
SELECT 'Benzoyl Peroxide', 'Topical acne treatment', CURRENT_TIMESTAMP
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_genericname WHERE name = 'Benzoyl Peroxide');
INSERT INTO pharmacy_app_genericname (name, description, created_at)
SELECT 'Mometasone', 'Topical steroid for skin inflammation', CURRENT_TIMESTAMP
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_genericname WHERE name = 'Mometasone');
INSERT INTO pharmacy_app_genericname (name, description, created_at)
SELECT 'Ciprofloxacin Ear Drops', 'Antibiotic ear drops', CURRENT_TIMESTAMP
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_genericname WHERE name = 'Ciprofloxacin Ear Drops');
INSERT INTO pharmacy_app_genericname (name, description, created_at)
SELECT 'Fusidic Acid', 'Topical antibiotic for skin infection', CURRENT_TIMESTAMP
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_genericname WHERE name = 'Fusidic Acid');
INSERT INTO pharmacy_app_genericname (name, description, created_at)
SELECT 'Ispaghula', 'Bulk-forming laxative', CURRENT_TIMESTAMP
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_genericname WHERE name = 'Ispaghula');
INSERT INTO pharmacy_app_genericname (name, description, created_at)
SELECT 'Bisacodyl', 'Stimulant laxative', CURRENT_TIMESTAMP
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_genericname WHERE name = 'Bisacodyl');

INSERT INTO pharmacy_app_medicine (
    name, volume, unit_price, selling_price, quantity, expire_date, purchase_paid, purchase_due,
    description, image, created_at, updated_at, generic_name_id, presentation_id, supplier_id
)
SELECT
    'Xyzal 5', '5mg', 12, 24, 150, '2027-09-30', 1800, 0,
    'Fast allergy relief tablet', '', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    (SELECT id FROM pharmacy_app_genericname WHERE name = 'Levocetirizine' LIMIT 1),
    (SELECT id FROM pharmacy_app_medicinepresentation WHERE name = 'Tablet' LIMIT 1),
    (SELECT id FROM pharmacy_app_supplier WHERE company_name = 'Sun Pharmaceuticals Ltd' LIMIT 1)
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_medicine WHERE name = 'Xyzal 5');

INSERT INTO pharmacy_app_medicine (
    name, volume, unit_price, selling_price, quantity, expire_date, purchase_paid, purchase_due,
    description, image, created_at, updated_at, generic_name_id, presentation_id, supplier_id
)
SELECT
    'Allegra 120', '120mg', 18, 36, 120, '2027-09-30', 2160, 0,
    'Non-drowsy allergy medicine', '', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    (SELECT id FROM pharmacy_app_genericname WHERE name = 'Fexofenadine' LIMIT 1),
    (SELECT id FROM pharmacy_app_medicinepresentation WHERE name = 'Tablet' LIMIT 1),
    (SELECT id FROM pharmacy_app_supplier WHERE company_name = 'San Pharmaceuticals Ltd' LIMIT 1)
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_medicine WHERE name = 'Allegra 120');

INSERT INTO pharmacy_app_medicine (
    name, volume, unit_price, selling_price, quantity, expire_date, purchase_paid, purchase_due,
    description, image, created_at, updated_at, generic_name_id, presentation_id, supplier_id
)
SELECT
    'Budecort Respules', '2ml', 95, 155, 60, '2027-03-31', 5700, 0,
    'Nebulizer suspension for asthma', '', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    (SELECT id FROM pharmacy_app_genericname WHERE name = 'Budesonide' LIMIT 1),
    (SELECT id FROM pharmacy_app_medicinepresentation WHERE name = 'Suspension' LIMIT 1),
    (SELECT id FROM pharmacy_app_supplier WHERE company_name = 'Cipla Ltd' LIMIT 1)
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_medicine WHERE name = 'Budecort Respules');

INSERT INTO pharmacy_app_medicine (
    name, volume, unit_price, selling_price, quantity, expire_date, purchase_paid, purchase_due,
    description, image, created_at, updated_at, generic_name_id, presentation_id, supplier_id
)
SELECT
    'Duolin Inhaler', '200 doses', 190, 295, 42, '2027-11-30', 7980, 0,
    'Bronchodilator inhaler for COPD and asthma', '', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    (SELECT id FROM pharmacy_app_genericname WHERE name = 'Ipratropium' LIMIT 1),
    (SELECT id FROM pharmacy_app_medicinepresentation WHERE name = 'Inhaler' LIMIT 1),
    (SELECT id FROM pharmacy_app_supplier WHERE company_name = 'Cipla Ltd' LIMIT 1)
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_medicine WHERE name = 'Duolin Inhaler');

INSERT INTO pharmacy_app_medicine (
    name, volume, unit_price, selling_price, quantity, expire_date, purchase_paid, purchase_due,
    description, image, created_at, updated_at, generic_name_id, presentation_id, supplier_id
)
SELECT
    'Mucosolvan Syrup', '100ml', 42, 74, 98, '2027-03-31', 4116, 0,
    'Relieves chest congestion', '', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    (SELECT id FROM pharmacy_app_genericname WHERE name = 'Ambroxol' LIMIT 1),
    (SELECT id FROM pharmacy_app_medicinepresentation WHERE name = 'Syrup' LIMIT 1),
    (SELECT id FROM pharmacy_app_supplier WHERE company_name = 'Mankind Pharma' LIMIT 1)
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_medicine WHERE name = 'Mucosolvan Syrup');

INSERT INTO pharmacy_app_medicine (
    name, volume, unit_price, selling_price, quantity, expire_date, purchase_paid, purchase_due,
    description, image, created_at, updated_at, generic_name_id, presentation_id, supplier_id
)
SELECT
    'Benadryl Cough', '100ml', 58, 96, 88, '2027-01-31', 5104, 0,
    'Dry cough suppressant syrup', '', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    (SELECT id FROM pharmacy_app_genericname WHERE name = 'Dextromethorphan' LIMIT 1),
    (SELECT id FROM pharmacy_app_medicinepresentation WHERE name = 'Syrup' LIMIT 1),
    (SELECT id FROM pharmacy_app_supplier WHERE company_name = 'Johnson Pharma' LIMIT 1)
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_medicine WHERE name = 'Benadryl Cough');

INSERT INTO pharmacy_app_medicine (
    name, volume, unit_price, selling_price, quantity, expire_date, purchase_paid, purchase_due,
    description, image, created_at, updated_at, generic_name_id, presentation_id, supplier_id
)
SELECT
    'Ascoril LS', '100ml', 65, 108, 92, '2027-01-31', 5980, 0,
    'Productive cough syrup', '', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    (SELECT id FROM pharmacy_app_genericname WHERE name = 'Guaifenesin' LIMIT 1),
    (SELECT id FROM pharmacy_app_medicinepresentation WHERE name = 'Syrup' LIMIT 1),
    (SELECT id FROM pharmacy_app_supplier WHERE company_name = 'Lupin Ltd' LIMIT 1)
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_medicine WHERE name = 'Ascoril LS');

INSERT INTO pharmacy_app_medicine (
    name, volume, unit_price, selling_price, quantity, expire_date, purchase_paid, purchase_due,
    description, image, created_at, updated_at, generic_name_id, presentation_id, supplier_id
)
SELECT
    'Bromhexine Syrup', '100ml', 38, 68, 85, '2027-01-31', 3230, 0,
    'Mucolytic syrup for cough', '', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    (SELECT id FROM pharmacy_app_genericname WHERE name = 'Bromhexine' LIMIT 1),
    (SELECT id FROM pharmacy_app_medicinepresentation WHERE name = 'Syrup' LIMIT 1),
    (SELECT id FROM pharmacy_app_supplier WHERE company_name = 'Mankind Pharma' LIMIT 1)
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_medicine WHERE name = 'Bromhexine Syrup');

INSERT INTO pharmacy_app_medicine (
    name, volume, unit_price, selling_price, quantity, expire_date, purchase_paid, purchase_due,
    description, image, created_at, updated_at, generic_name_id, presentation_id, supplier_id
)
SELECT
    'Naprosyn 250', '250mg', 24, 42, 110, '2027-05-31', 2640, 0,
    'Pain relief for headache and joint pain', '', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    (SELECT id FROM pharmacy_app_genericname WHERE name = 'Naproxen' LIMIT 1),
    (SELECT id FROM pharmacy_app_medicinepresentation WHERE name = 'Tablet' LIMIT 1),
    (SELECT id FROM pharmacy_app_supplier WHERE company_name = 'Dr Reddys Laboratories' LIMIT 1)
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_medicine WHERE name = 'Naprosyn 250');

INSERT INTO pharmacy_app_medicine (
    name, volume, unit_price, selling_price, quantity, expire_date, purchase_paid, purchase_due,
    description, image, created_at, updated_at, generic_name_id, presentation_id, supplier_id
)
SELECT
    'Meloset 3', '3mg', 14, 28, 76, '2027-09-30', 1064, 0,
    'Sleep support tablet', '', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    (SELECT id FROM pharmacy_app_genericname WHERE name = 'Melatonin' LIMIT 1),
    (SELECT id FROM pharmacy_app_medicinepresentation WHERE name = 'Tablet' LIMIT 1),
    (SELECT id FROM pharmacy_app_supplier WHERE company_name = 'Sun Pharmaceuticals Ltd' LIMIT 1)
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_medicine WHERE name = 'Meloset 3');

INSERT INTO pharmacy_app_medicine (
    name, volume, unit_price, selling_price, quantity, expire_date, purchase_paid, purchase_due,
    description, image, created_at, updated_at, generic_name_id, presentation_id, supplier_id
)
SELECT
    'Clonotril 0.5', '0.5mg', 20, 38, 84, '2027-11-30', 1680, 0,
    'For anxiety and sleep disorders', '', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    (SELECT id FROM pharmacy_app_genericname WHERE name = 'Clonazepam' LIMIT 1),
    (SELECT id FROM pharmacy_app_medicinepresentation WHERE name = 'Tablet' LIMIT 1),
    (SELECT id FROM pharmacy_app_supplier WHERE company_name = 'Cipla Ltd' LIMIT 1)
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_medicine WHERE name = 'Clonotril 0.5');

INSERT INTO pharmacy_app_medicine (
    name, volume, unit_price, selling_price, quantity, expire_date, purchase_paid, purchase_due,
    description, image, created_at, updated_at, generic_name_id, presentation_id, supplier_id
)
SELECT
    'Alprax 0.25', '0.25mg', 18, 34, 90, '2027-11-30', 1620, 0,
    'Anxiety relief tablet', '', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    (SELECT id FROM pharmacy_app_genericname WHERE name = 'Alprazolam' LIMIT 1),
    (SELECT id FROM pharmacy_app_medicinepresentation WHERE name = 'Tablet' LIMIT 1),
    (SELECT id FROM pharmacy_app_supplier WHERE company_name = 'Lupin Ltd' LIMIT 1)
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_medicine WHERE name = 'Alprax 0.25');

INSERT INTO pharmacy_app_medicine (
    name, volume, unit_price, selling_price, quantity, expire_date, purchase_paid, purchase_due,
    description, image, created_at, updated_at, generic_name_id, presentation_id, supplier_id
)
SELECT
    'Januvia 50', '50mg', 42, 72, 96, '2027-09-30', 4032, 0,
    'Diabetes control tablet', '', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    (SELECT id FROM pharmacy_app_genericname WHERE name = 'Sitagliptin' LIMIT 1),
    (SELECT id FROM pharmacy_app_medicinepresentation WHERE name = 'Tablet' LIMIT 1),
    (SELECT id FROM pharmacy_app_supplier WHERE company_name = 'Sun Pharmaceuticals Ltd' LIMIT 1)
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_medicine WHERE name = 'Januvia 50');

INSERT INTO pharmacy_app_medicine (
    name, volume, unit_price, selling_price, quantity, expire_date, purchase_paid, purchase_due,
    description, image, created_at, updated_at, generic_name_id, presentation_id, supplier_id
)
SELECT
    'Envas 5', '5mg', 16, 30, 128, '2027-11-30', 2048, 0,
    'ACE inhibitor for BP control', '', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    (SELECT id FROM pharmacy_app_genericname WHERE name = 'Enalapril' LIMIT 1),
    (SELECT id FROM pharmacy_app_medicinepresentation WHERE name = 'Tablet' LIMIT 1),
    (SELECT id FROM pharmacy_app_supplier WHERE company_name = 'Dr Reddys Laboratories' LIMIT 1)
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_medicine WHERE name = 'Envas 5');

INSERT INTO pharmacy_app_medicine (
    name, volume, unit_price, selling_price, quantity, expire_date, purchase_paid, purchase_due,
    description, image, created_at, updated_at, generic_name_id, presentation_id, supplier_id
)
SELECT
    'Aten 50', '50mg', 14, 27, 140, '2027-11-30', 1960, 0,
    'Beta blocker for blood pressure', '', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    (SELECT id FROM pharmacy_app_genericname WHERE name = 'Atenolol' LIMIT 1),
    (SELECT id FROM pharmacy_app_medicinepresentation WHERE name = 'Tablet' LIMIT 1),
    (SELECT id FROM pharmacy_app_supplier WHERE company_name = 'Mankind Pharma' LIMIT 1)
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_medicine WHERE name = 'Aten 50');

INSERT INTO pharmacy_app_medicine (
    name, volume, unit_price, selling_price, quantity, expire_date, purchase_paid, purchase_due,
    description, image, created_at, updated_at, generic_name_id, presentation_id, supplier_id
)
SELECT
    'Simvotin 10', '10mg', 18, 34, 118, '2027-09-30', 2124, 0,
    'Cholesterol lowering tablet', '', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    (SELECT id FROM pharmacy_app_genericname WHERE name = 'Simvastatin' LIMIT 1),
    (SELECT id FROM pharmacy_app_medicinepresentation WHERE name = 'Tablet' LIMIT 1),
    (SELECT id FROM pharmacy_app_supplier WHERE company_name = 'Lupin Ltd' LIMIT 1)
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_medicine WHERE name = 'Simvotin 10');

INSERT INTO pharmacy_app_medicine (
    name, volume, unit_price, selling_price, quantity, expire_date, purchase_paid, purchase_due,
    description, image, created_at, updated_at, generic_name_id, presentation_id, supplier_id
)
SELECT
    'Electral Sachet', '21g', 12, 22, 160, '2028-03-31', 1920, 0,
    'Prevents dehydration in diarrhea and vomiting', '', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    (SELECT id FROM pharmacy_app_genericname WHERE name = 'Oral Rehydration Salts' LIMIT 1),
    (SELECT id FROM pharmacy_app_medicinepresentation WHERE name = 'Powder' LIMIT 1),
    (SELECT id FROM pharmacy_app_supplier WHERE company_name = 'Cipla Ltd' LIMIT 1)
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_medicine WHERE name = 'Electral Sachet');

INSERT INTO pharmacy_app_medicine (
    name, volume, unit_price, selling_price, quantity, expire_date, purchase_paid, purchase_due,
    description, image, created_at, updated_at, generic_name_id, presentation_id, supplier_id
)
SELECT
    'Terbest Cream', '15g', 45, 78, 72, '2027-03-31', 3240, 0,
    'Antifungal cream', '', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    (SELECT id FROM pharmacy_app_genericname WHERE name = 'Terbinafine' LIMIT 1),
    (SELECT id FROM pharmacy_app_medicinepresentation WHERE name = 'Cream' LIMIT 1),
    (SELECT id FROM pharmacy_app_supplier WHERE company_name = 'Sun Pharmaceuticals Ltd' LIMIT 1)
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_medicine WHERE name = 'Terbest Cream');

INSERT INTO pharmacy_app_medicine (
    name, volume, unit_price, selling_price, quantity, expire_date, purchase_paid, purchase_due,
    description, image, created_at, updated_at, generic_name_id, presentation_id, supplier_id
)
SELECT
    'Adaferin Gel', '15g', 58, 96, 60, '2027-03-31', 3480, 0,
    'Topical acne gel', '', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    (SELECT id FROM pharmacy_app_genericname WHERE name = 'Adapalene' LIMIT 1),
    (SELECT id FROM pharmacy_app_medicinepresentation WHERE name = 'Gel' LIMIT 1),
    (SELECT id FROM pharmacy_app_supplier WHERE company_name = 'Galderma Pharma' LIMIT 1)
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_medicine WHERE name = 'Adaferin Gel');

INSERT INTO pharmacy_app_medicine (
    name, volume, unit_price, selling_price, quantity, expire_date, purchase_paid, purchase_due,
    description, image, created_at, updated_at, generic_name_id, presentation_id, supplier_id
)
SELECT
    'Persol AC', '20g', 36, 64, 70, '2027-03-31', 2520, 0,
    'Acne treatment gel', '', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    (SELECT id FROM pharmacy_app_genericname WHERE name = 'Benzoyl Peroxide' LIMIT 1),
    (SELECT id FROM pharmacy_app_medicinepresentation WHERE name = 'Gel' LIMIT 1),
    (SELECT id FROM pharmacy_app_supplier WHERE company_name = 'Johnson Pharma' LIMIT 1)
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_medicine WHERE name = 'Persol AC');

INSERT INTO pharmacy_app_medicine (
    name, volume, unit_price, selling_price, quantity, expire_date, purchase_paid, purchase_due,
    description, image, created_at, updated_at, generic_name_id, presentation_id, supplier_id
)
SELECT
    'Elocon Cream', '15g', 52, 88, 62, '2027-03-31', 3224, 0,
    'Topical steroid cream', '', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    (SELECT id FROM pharmacy_app_genericname WHERE name = 'Mometasone' LIMIT 1),
    (SELECT id FROM pharmacy_app_medicinepresentation WHERE name = 'Cream' LIMIT 1),
    (SELECT id FROM pharmacy_app_supplier WHERE company_name = 'Sun Pharmaceuticals Ltd' LIMIT 1)
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_medicine WHERE name = 'Elocon Cream');

INSERT INTO pharmacy_app_medicine (
    name, volume, unit_price, selling_price, quantity, expire_date, purchase_paid, purchase_due,
    description, image, created_at, updated_at, generic_name_id, presentation_id, supplier_id
)
SELECT
    'Cipro Ear Drops', '10ml', 66, 112, 54, '2027-01-31', 3564, 0,
    'Ear drops for bacterial ear infection', '', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    (SELECT id FROM pharmacy_app_genericname WHERE name = 'Ciprofloxacin Ear Drops' LIMIT 1),
    (SELECT id FROM pharmacy_app_medicinepresentation WHERE name = 'Ear Drops' LIMIT 1),
    (SELECT id FROM pharmacy_app_supplier WHERE company_name = 'Cipla Ltd' LIMIT 1)
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_medicine WHERE name = 'Cipro Ear Drops');

INSERT INTO pharmacy_app_medicine (
    name, volume, unit_price, selling_price, quantity, expire_date, purchase_paid, purchase_due,
    description, image, created_at, updated_at, generic_name_id, presentation_id, supplier_id
)
SELECT
    'Fucidin Cream', '15g', 62, 105, 58, '2027-03-31', 3596, 0,
    'Topical antibiotic cream', '', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    (SELECT id FROM pharmacy_app_genericname WHERE name = 'Fusidic Acid' LIMIT 1),
    (SELECT id FROM pharmacy_app_medicinepresentation WHERE name = 'Cream' LIMIT 1),
    (SELECT id FROM pharmacy_app_supplier WHERE company_name = 'Lupin Ltd' LIMIT 1)
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_medicine WHERE name = 'Fucidin Cream');

INSERT INTO pharmacy_app_medicine (
    name, volume, unit_price, selling_price, quantity, expire_date, purchase_paid, purchase_due,
    description, image, created_at, updated_at, generic_name_id, presentation_id, supplier_id
)
SELECT
    'Isabgol Husk', '100g', 44, 76, 95, '2027-09-30', 4180, 0,
    'Fiber supplement for constipation', '', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    (SELECT id FROM pharmacy_app_genericname WHERE name = 'Ispaghula' LIMIT 1),
    (SELECT id FROM pharmacy_app_medicinepresentation WHERE name = 'Powder' LIMIT 1),
    (SELECT id FROM pharmacy_app_supplier WHERE company_name = 'Dabur Pharma' LIMIT 1)
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_medicine WHERE name = 'Isabgol Husk');

INSERT INTO pharmacy_app_medicine (
    name, volume, unit_price, selling_price, quantity, expire_date, purchase_paid, purchase_due,
    description, image, created_at, updated_at, generic_name_id, presentation_id, supplier_id
)
SELECT
    'Dulcolax 5', '5mg', 10, 21, 105, '2027-09-30', 1050, 0,
    'Stimulant laxative tablet', '', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    (SELECT id FROM pharmacy_app_genericname WHERE name = 'Bisacodyl' LIMIT 1),
    (SELECT id FROM pharmacy_app_medicinepresentation WHERE name = 'Tablet' LIMIT 1),
    (SELECT id FROM pharmacy_app_supplier WHERE company_name = 'Sanofi India' LIMIT 1)
WHERE NOT EXISTS (SELECT 1 FROM pharmacy_app_medicine WHERE name = 'Dulcolax 5');

COMMIT;
