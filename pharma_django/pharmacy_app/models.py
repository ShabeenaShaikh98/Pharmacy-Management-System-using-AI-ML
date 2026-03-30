from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class GenericName(models.Model):
    """Generic drug names e.g. Paracetamol, Ibuprofen"""
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Generic Name"

    def __str__(self):
        return self.name


class MedicinePresentation(models.Model):
    """Presentation types: Tablet, Capsule, Syrup, etc."""
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Medicine Presentation"

    def __str__(self):
        return self.name


class Supplier(models.Model):
    """Medicine suppliers / companies"""
    company_name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    previous_due = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['company_name']
        verbose_name = "Supplier"

    def __str__(self):
        return self.company_name

    @property
    def total_medicines(self):
        return self.medicine_set.count()


class Medicine(models.Model):
    """Core medicine inventory"""
    name = models.CharField(max_length=250)
    generic_name = models.ForeignKey(
        GenericName, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='medicines'
    )
    presentation = models.ForeignKey(
        MedicinePresentation, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='medicines'
    )
    volume = models.CharField(max_length=100, blank=True, help_text="e.g. 500mg, 100ml")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity = models.PositiveIntegerField(default=0)
    expire_date = models.DateField(null=True, blank=True)
    supplier = models.ForeignKey(
        Supplier, on_delete=models.SET_NULL, null=True, blank=True
    )
    purchase_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    purchase_due = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='medicines/', null=True, blank=True)
    prescription_required = models.BooleanField(default=False)
    is_online_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Medicine"

    def __str__(self):
        return self.name

    @property
    def is_expired(self):
        if self.expire_date:
            return self.expire_date < timezone.now().date()
        return False

    @property
    def is_low_stock(self):
        return 0 < self.quantity < 20

    @property
    def is_out_of_stock(self):
        return self.quantity == 0

    @property
    def stock_status(self):
        if self.is_out_of_stock:
            return 'out_of_stock'
        elif self.is_low_stock:
            return 'low_stock'
        elif self.quantity < 50:
            return 'adequate'
        return 'well_stocked'

    @property
    def profit_margin(self):
        if self.unit_price > 0:
            return round(float((self.selling_price - self.unit_price) / self.unit_price * 100), 2)
        return 0


class Purchase(models.Model):
    """Purchase / Stock-in records"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('received', 'Received'),
        ('partial', 'Partial'),
        ('cancelled', 'Cancelled'),
    ]
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='purchases')
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    due_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received')
    purchase_date = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-purchase_date']

    def __str__(self):
        return f"PO-{self.id} | {self.medicine.name}"

    def save(self, *args, **kwargs):
        self.total_amount = self.quantity * self.unit_price
        self.due_amount = self.total_amount - self.amount_paid
        super().save(*args, **kwargs)


class Sale(models.Model):
    """Sales / billing records"""
    invoice_number = models.CharField(max_length=50, unique=True)
    customer_name = models.CharField(max_length=200, blank=True)
    customer_email = models.EmailField(blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    sale_date = models.DateTimeField(default=timezone.now)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sub_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    change_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-sale_date']

    def __str__(self):
        return f"INV-{self.invoice_number}"

    @classmethod
    def generate_invoice_number(cls):
        import datetime
        today = datetime.date.today()
        prefix = f"INV{today.strftime('%Y%m%d')}"
        last = cls.objects.filter(invoice_number__startswith=prefix).order_by('-invoice_number').first()
        if last:
            last_num = int(last.invoice_number[-4:])
            return f"{prefix}{str(last_num + 1).zfill(4)}"
        return f"{prefix}0001"


class SaleItem(models.Model):
    """Individual line items in a sale"""
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sub_total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.medicine.name} x {self.quantity}"

    def save(self, *args, **kwargs):
        self.sub_total = (self.unit_price * self.quantity) - self.discount
        super().save(*args, **kwargs)


class ChatMessage(models.Model):
    """AI Chat assistant message history"""
    ROLE_CHOICES = [('user', 'User'), ('assistant', 'Assistant')]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_messages')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.role}] {self.message[:50]}"


class OCRPrescription(models.Model):
    """OCR prescription scan results"""
    image = models.ImageField(upload_to='prescriptions/', null=True, blank=True)
    prescription_text = models.TextField(blank=True)
    extracted_medicines = models.JSONField(default=list)
    recommendations = models.JSONField(default=list)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Prescription #{self.id}"


class CustomerProfile(models.Model):
    """Online-customer profile mapped to auth user."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_profile')
    phone = models.CharField(max_length=20, blank=True)
    address_line = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} profile"

    @property
    def full_address(self):
        parts = [self.address_line, self.city, self.state, self.pincode]
        return ", ".join([p for p in parts if p]).strip()


class OnlineCart(models.Model):
    """One active cart per customer profile."""
    customer = models.OneToOneField(CustomerProfile, on_delete=models.CASCADE, related_name='online_cart')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Cart - {self.customer.user.username}"


class OnlineCartItem(models.Model):
    cart = models.ForeignKey(OnlineCart, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='online_cart_items')
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'medicine')
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.medicine.name} x {self.quantity}"

    @property
    def line_total(self):
        return self.quantity * self.medicine.selling_price


class OnlinePrescription(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='online_prescriptions')
    image = models.ImageField(upload_to='online_prescriptions/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    review_note = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_online_prescriptions')
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Rx #{self.id} - {self.customer.user.username}"


class OnlineOrder(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('packed', 'Packed'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    PAYMENT_CHOICES = [
        ('cod', 'Cash on Delivery'),
        ('upi', 'UPI'),
        ('card', 'Card'),
    ]

    order_id = models.CharField(max_length=30, unique=True, editable=False)
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='online_orders')
    prescription = models.ForeignKey(OnlinePrescription, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cod')
    customer_name = models.CharField(max_length=200, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    delivery_address = models.TextField(blank=True)
    delivery_partner = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_online_orders'
    )
    delivery_assigned_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.order_id

    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = f"ONL-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    def log_status(self, status, changed_by=None, note=''):
        """Track every order status transition for timeline UI/API."""
        return OnlineOrderStatusLog.objects.create(
            order=self,
            status=status,
            changed_by=changed_by,
            note=note,
        )


class OnlineOrderItem(models.Model):
    order = models.ForeignKey(OnlineOrder, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.PROTECT, related_name='online_order_items')
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.order.order_id} - {self.medicine.name}"


class OnlinePayment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]

    order = models.OneToOneField(OnlineOrder, on_delete=models.CASCADE, related_name='payment')
    method = models.CharField(max_length=20, choices=OnlineOrder.PAYMENT_CHOICES, default='cod')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    gateway = models.CharField(max_length=40, blank=True, help_text='e.g. razorpay, stripe, cod')
    reference = models.CharField(max_length=120, blank=True)
    gateway_payment_id = models.CharField(max_length=120, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    refund_status = models.CharField(
        max_length=20,
        choices=[('none', 'None'), ('requested', 'Requested'), ('processed', 'Processed'), ('failed', 'Failed')],
        default='none'
    )
    refunded_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    refunded_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order.order_id} payment"


class OnlineOrderStatusLog(models.Model):
    """Audit trail for order status and delivery progress."""

    order = models.ForeignKey(OnlineOrder, on_delete=models.CASCADE, related_name='status_logs')
    status = models.CharField(max_length=20, choices=OnlineOrder.STATUS_CHOICES)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    note = models.CharField(max_length=255, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-changed_at']

    def __str__(self):
        return f"{self.order.order_id} -> {self.status}"
