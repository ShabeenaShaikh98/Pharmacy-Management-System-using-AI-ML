from decimal import Decimal
import datetime
from django.contrib.auth import get_user_model
from django.utils import timezone
from pharmacy_app.models import (
    GenericName, MedicinePresentation, Supplier, Medicine,
    Sale, SaleItem, CustomerProfile, OnlineOrder, OnlineOrderItem, OnlinePayment
)

U = get_user_model()
now = timezone.now()
today = now.date()

# 1) Ensure pgadmin superuser in PostgreSQL
pgadmin, _ = U.objects.get_or_create(
    username='pgadmin',
    defaults={'email': 'pgadmin@example.com', 'is_staff': True, 'is_superuser': True}
)
pgadmin.is_staff = True
pgadmin.is_superuser = True
if not pgadmin.email:
    pgadmin.email = 'pgadmin@example.com'
pgadmin.set_password('PgAdmin@12345')
pgadmin.save()

# 2) Base refs
presentation_names = ['Tablet', 'Capsule', 'Syrup', 'Injection', 'Cream']
presentations = [MedicinePresentation.objects.get_or_create(name=n)[0] for n in presentation_names]

supplier_names = [
    'AL-HAMD Distributors', 'CarePlus Pharma', 'WellLife Medico',
    'Prime Health Suppliers', 'City Med Hub'
]
suppliers = [
    Supplier.objects.get_or_create(
        company_name=n,
        defaults={'contact_person': 'Manager', 'phone': '9000000000', 'email': f"{n.lower().replace(' ', '')}@example.com"}
    )[0]
    for n in supplier_names
]

generic_pool = [
    'Paracetamol', 'Ibuprofen', 'Amoxicillin', 'Cetirizine', 'Azithromycin',
    'Metformin', 'Omeprazole', 'Pantoprazole', 'Atorvastatin', 'Amlodipine'
]
generics = [GenericName.objects.get_or_create(name=n)[0] for n in generic_pool]

# 3) Medicine target for strong dashboard numbers
current_meds = Medicine.objects.count()
target_meds = 600
add_meds = max(0, target_meds - current_meds)

for i in range(add_meds):
    idx = current_meds + i + 1
    qty_pattern = [0, 5, 12, 35, 80, 140, 220]
    qty = qty_pattern[idx % len(qty_pattern)]

    if idx % 13 == 0:
        exp = today - datetime.timedelta(days=(idx % 25) + 1)
    elif idx % 7 == 0:
        exp = today + datetime.timedelta(days=(idx % 25) + 1)
    else:
        exp = today + datetime.timedelta(days=90 + (idx % 500))

    unit_price = Decimal(8 + (idx % 40))
    selling_price = unit_price + Decimal(3 + (idx % 9))

    Medicine.objects.create(
        name=f'PG Demo Medicine {idx:04d}',
        generic_name=generics[idx % len(generics)],
        presentation=presentations[idx % len(presentations)],
        volume=f'{100 + (idx % 900)}mg',
        unit_price=unit_price,
        selling_price=selling_price,
        quantity=qty,
        expire_date=exp,
        supplier=suppliers[idx % len(suppliers)],
        description='Auto-seeded for dashboard demo',
        prescription_required=(idx % 4 == 0),
        is_online_available=(idx % 9 != 0),
    )

meds = list(Medicine.objects.filter(quantity__gt=0).order_by('id')[:300])
if not meds:
    meds = list(Medicine.objects.order_by('id')[:100])

# 4) Customer users + profiles
customers = []
for i in range(1, 31):
    uname = f'cust{i:02d}'
    u, _ = U.objects.get_or_create(username=uname, defaults={'email': f'{uname}@example.com'})
    if not u.has_usable_password():
        u.set_password('Customer@123')
        u.save(update_fields=['password'])

    cp, _ = CustomerProfile.objects.get_or_create(
        user=u,
        defaults={
            'phone': f'98{(10000000 + i):08d}'[:10],
            'address_line': f'Street {i}, Main Area',
            'city': 'Kolkata',
            'state': 'West Bengal',
            'pincode': f'700{100 + i}',
        }
    )
    customers.append(cp)

# 5) POS Sales
sales_current = Sale.objects.count()
target_sales = 120
add_sales = max(0, target_sales - sales_current)

for i in range(add_sales):
    sale_day = now - datetime.timedelta(days=(i % 14), hours=(i % 10))
    invoice = f'PG{sale_day.strftime("%Y%m%d")}{sales_current + i + 1:05d}'
    if Sale.objects.filter(invoice_number=invoice).exists():
        continue

    sale = Sale.objects.create(
        invoice_number=invoice,
        customer_name=f'Walk-in {i+1}',
        customer_phone=f'9{(100000000 + i):09d}'[:10],
        sale_date=sale_day,
        discount=Decimal('0.00'),
        paid_amount=Decimal('0.00'),
        change_amount=Decimal('0.00'),
        notes='Demo sale for dashboard',
        created_by=pgadmin,
    )

    line_count = 1 + (i % 3)
    subtotal = Decimal('0.00')
    for j in range(line_count):
        m = meds[(i + j) % len(meds)]
        qty = 1 + ((i + j) % 4)
        unit = Decimal(m.selling_price)
        line_total = unit * qty

        SaleItem.objects.create(
            sale=sale,
            medicine=m,
            quantity=qty,
            unit_price=unit,
            discount=Decimal('0.00'),
            sub_total=line_total,
        )
        subtotal += line_total

    sale.sub_total = subtotal
    sale.total_amount = subtotal
    sale.paid_amount = subtotal
    sale.save(update_fields=['sub_total', 'total_amount', 'paid_amount'])

# 6) Online orders + payments
status_cycle = ['pending', 'approved', 'packed', 'out_for_delivery', 'delivered', 'cancelled']
payment_method_cycle = ['cod', 'upi', 'card']

online_current = OnlineOrder.objects.count()
target_online = 80
add_online = max(0, target_online - online_current)

for i in range(add_online):
    cp = customers[i % len(customers)]
    status = status_cycle[i % len(status_cycle)]
    method = payment_method_cycle[i % len(payment_method_cycle)]

    order = OnlineOrder.objects.create(
        customer=cp,
        status=status,
        payment_method=method,
        customer_name=cp.user.get_full_name() or cp.user.username,
        customer_phone=cp.phone or '9999999999',
        delivery_address=cp.full_address or 'Demo Address',
        notes='Demo online order',
        total_amount=Decimal('0.00'),
    )

    item_count = 1 + (i % 3)
    total = Decimal('0.00')
    for j in range(item_count):
        m = meds[(i * 2 + j) % len(meds)]
        qty = 1 + ((i + j) % 2)
        unit = Decimal(m.selling_price)
        line_total = unit * qty
        OnlineOrderItem.objects.create(
            order=order,
            medicine=m,
            quantity=qty,
            unit_price=unit,
            line_total=line_total,
        )
        total += line_total

    order.total_amount = total
    order.save(update_fields=['total_amount', 'updated_at'])

    pay_status = 'paid' if status in ['approved', 'packed', 'out_for_delivery', 'delivered'] else 'pending'
    OnlinePayment.objects.create(
        order=order,
        method=method,
        status=pay_status,
        gateway='cod' if method == 'cod' else 'online',
        amount=total,
    )

print('seed_complete')
print('users=', U.objects.count())
print('medicines=', Medicine.objects.count())
print('suppliers=', Supplier.objects.count())
print('generics=', GenericName.objects.count())
print('sales=', Sale.objects.count())
print('sale_items=', SaleItem.objects.count())
print('online_orders=', OnlineOrder.objects.count())
print('online_payments=', OnlinePayment.objects.count())
print('customer_profiles=', CustomerProfile.objects.count())
print('pgadmin_ready=', U.objects.filter(username='pgadmin', is_superuser=True, is_staff=True).exists())
