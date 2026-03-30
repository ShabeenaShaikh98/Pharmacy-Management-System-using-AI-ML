from django.contrib import admin
from .models import (
    GenericName, MedicinePresentation, Supplier,
    Medicine, Purchase, Sale, SaleItem, ChatMessage, OCRPrescription,
    CustomerProfile, OnlineCart, OnlineCartItem, OnlinePrescription,
    OnlineOrder, OnlineOrderItem, OnlinePayment, OnlineOrderStatusLog
)


@admin.register(GenericName)
class GenericNameAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name']


@admin.register(MedicinePresentation)
class MedicinePresentationAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'contact_person', 'phone', 'email', 'previous_due']
    search_fields = ['company_name', 'email']


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ['name', 'generic_name', 'presentation', 'quantity', 'selling_price', 'prescription_required', 'is_online_available', 'expire_date', 'supplier']
    list_filter = ['presentation', 'supplier', 'generic_name', 'prescription_required', 'is_online_available']
    search_fields = ['name']
    date_hierarchy = 'created_at'


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'customer_name', 'sub_total', 'sale_date', 'created_by']
    search_fields = ['invoice_number', 'customer_name']
    inlines = [SaleItemInline]


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ['id', 'medicine', 'supplier', 'quantity', 'total_amount', 'amount_paid', 'status', 'purchase_date']
    list_filter = ['status', 'supplier']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'message', 'created_at']


@admin.register(OCRPrescription)
class OCRPrescriptionAdmin(admin.ModelAdmin):
    list_display = ['id', 'uploaded_by', 'created_at']


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'city', 'state', 'pincode']
    search_fields = ['user__username', 'phone', 'city']


class OnlineCartItemInline(admin.TabularInline):
    model = OnlineCartItem
    extra = 0
    readonly_fields = ['medicine', 'quantity', 'added_at']


@admin.register(OnlineCart)
class OnlineCartAdmin(admin.ModelAdmin):
    list_display = ['customer', 'updated_at']
    inlines = [OnlineCartItemInline]


@admin.register(OnlinePrescription)
class OnlinePrescriptionAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'status', 'created_at', 'reviewed_by']
    list_filter = ['status']
    search_fields = ['customer__user__username']
    list_editable = ['status']


class OnlineOrderItemInline(admin.TabularInline):
    model = OnlineOrderItem
    extra = 0
    readonly_fields = ['medicine', 'quantity', 'unit_price', 'line_total']


@admin.register(OnlineOrder)
class OnlineOrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'customer', 'status', 'delivery_partner', 'payment_method', 'total_amount', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at', 'delivery_partner']
    search_fields = ['order_id', 'customer__user__username', 'customer_name', 'customer_phone']
    list_editable = ['status']
    inlines = [OnlineOrderItemInline]


@admin.register(OnlinePayment)
class OnlinePaymentAdmin(admin.ModelAdmin):
    list_display = ['order', 'method', 'status', 'gateway', 'amount', 'refund_status', 'reference', 'created_at']
    list_filter = ['method', 'status', 'gateway', 'refund_status']


@admin.register(OnlineOrderStatusLog)
class OnlineOrderStatusLogAdmin(admin.ModelAdmin):
    list_display = ['order', 'status', 'changed_by', 'changed_at', 'note']
    list_filter = ['status', 'changed_at']
    search_fields = ['order__order_id', 'note', 'changed_by__username']
