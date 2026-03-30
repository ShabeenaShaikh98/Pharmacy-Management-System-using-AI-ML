import datetime
from decimal import Decimal

from django.utils import timezone
from rest_framework import serializers

from .models import (
    CustomerProfile,
    Medicine,
    OnlineCart,
    OnlineCartItem,
    OnlineOrder,
    OnlineOrderItem,
    OnlineOrderStatusLog,
    OnlinePayment,
    OnlinePrescription,
)


class OnlineMedicineCatalogSerializer(serializers.ModelSerializer):
    generic_name = serializers.CharField(source='generic_name.name', default='')
    near_expiry = serializers.SerializerMethodField()
    low_stock = serializers.SerializerMethodField()

    class Meta:
        model = Medicine
        fields = [
            'id', 'name', 'generic_name', 'volume', 'description', 'selling_price',
            'quantity', 'prescription_required', 'is_online_available', 'expire_date',
            'near_expiry', 'low_stock',
        ]

    def get_near_expiry(self, obj):
        if not obj.expire_date:
            return False
        return obj.expire_date <= timezone.now().date() + datetime.timedelta(days=30)

    def get_low_stock(self, obj):
        return 0 < obj.quantity < 20


class OnlineCartItemSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    medicine_price = serializers.DecimalField(source='medicine.selling_price', max_digits=10, decimal_places=2, read_only=True)
    medicine_stock = serializers.IntegerField(source='medicine.quantity', read_only=True)
    prescription_required = serializers.BooleanField(source='medicine.prescription_required', read_only=True)
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = OnlineCartItem
        fields = [
            'id', 'medicine', 'medicine_name', 'medicine_price', 'medicine_stock',
            'prescription_required', 'quantity', 'line_total', 'added_at',
        ]

    def get_line_total(self, obj):
        return obj.quantity * obj.medicine.selling_price


class OnlineCartSerializer(serializers.ModelSerializer):
    items = OnlineCartItemSerializer(many=True, read_only=True)
    total_items = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = OnlineCart
        fields = ['id', 'updated_at', 'items', 'total_items', 'total_amount']

    def get_total_items(self, obj):
        return sum(item.quantity for item in obj.items.all())

    def get_total_amount(self, obj):
        total = sum((item.quantity * item.medicine.selling_price for item in obj.items.all()), Decimal('0'))
        return total


class AddCartItemSerializer(serializers.Serializer):
    medicine_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, default=1)

    def validate(self, attrs):
        medicine_id = attrs['medicine_id']
        quantity = attrs['quantity']
        medicine = Medicine.objects.filter(id=medicine_id, is_online_available=True).first()
        if not medicine:
            raise serializers.ValidationError('Medicine not found or not available online.')
        if medicine.quantity < quantity:
            raise serializers.ValidationError(f'Only {medicine.quantity} units available.')
        attrs['medicine'] = medicine
        return attrs


class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=0)


class OnlinePrescriptionSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.user.username', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.username', read_only=True, default='')

    class Meta:
        model = OnlinePrescription
        fields = [
            'id', 'customer', 'customer_name', 'image', 'status', 'review_note',
            'reviewed_by', 'reviewed_by_name', 'created_at', 'reviewed_at',
        ]
        read_only_fields = ['customer', 'status', 'review_note', 'reviewed_by', 'reviewed_at']


class ReviewPrescriptionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['approved', 'rejected'])
    review_note = serializers.CharField(required=False, allow_blank=True, max_length=500)

    def validate(self, attrs):
        if attrs['action'] == 'rejected' and not attrs.get('review_note', '').strip():
            raise serializers.ValidationError('Rejection requires a review note.')
        return attrs


class OnlineOrderItemSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)

    class Meta:
        model = OnlineOrderItem
        fields = ['id', 'medicine', 'medicine_name', 'quantity', 'unit_price', 'line_total']


class OnlinePaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnlinePayment
        fields = [
            'id', 'method', 'status', 'gateway', 'reference', 'gateway_payment_id',
            'amount', 'refund_status', 'refunded_amount', 'refunded_at',
            'failure_reason', 'created_at', 'updated_at',
        ]


class OnlineOrderStatusLogSerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source='changed_by.username', read_only=True, default='')

    class Meta:
        model = OnlineOrderStatusLog
        fields = ['id', 'status', 'note', 'changed_by', 'changed_by_name', 'changed_at']


class OnlineOrderListSerializer(serializers.ModelSerializer):
    customer_username = serializers.CharField(source='customer.user.username', read_only=True)
    payment = OnlinePaymentSerializer(read_only=True)

    class Meta:
        model = OnlineOrder
        fields = [
            'id', 'order_id', 'status', 'payment_method', 'customer_name',
            'customer_username', 'customer_phone', 'delivery_address',
            'delivery_partner', 'delivery_assigned_at', 'total_amount',
            'created_at', 'updated_at', 'payment',
        ]


class OnlineOrderDetailSerializer(serializers.ModelSerializer):
    customer_username = serializers.CharField(source='customer.user.username', read_only=True)
    items = OnlineOrderItemSerializer(many=True, read_only=True)
    payment = OnlinePaymentSerializer(read_only=True)
    prescription = OnlinePrescriptionSerializer(read_only=True)
    timeline = serializers.SerializerMethodField()

    class Meta:
        model = OnlineOrder
        fields = [
            'id', 'order_id', 'status', 'payment_method', 'customer_name', 'customer_username',
            'customer_phone', 'delivery_address', 'delivery_partner', 'delivery_assigned_at',
            'notes', 'total_amount', 'created_at', 'updated_at', 'prescription',
            'items', 'payment', 'timeline',
        ]

    def get_timeline(self, obj):
        logs = obj.status_logs.select_related('changed_by').all()
        return OnlineOrderStatusLogSerializer(logs, many=True).data


class CheckoutSerializer(serializers.Serializer):
    customer_name = serializers.CharField(required=False, allow_blank=True, max_length=200)
    customer_phone = serializers.CharField(max_length=20)
    delivery_address = serializers.CharField(max_length=1000)
    payment_method = serializers.ChoiceField(choices=OnlineOrder.PAYMENT_CHOICES)
    notes = serializers.CharField(required=False, allow_blank=True)
    prescription_id = serializers.IntegerField(required=False)


class AssignDeliverySerializer(serializers.Serializer):
    delivery_partner_id = serializers.IntegerField()
    note = serializers.CharField(required=False, allow_blank=True, max_length=255)


class UpdateOrderStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=OnlineOrder.STATUS_CHOICES)
    note = serializers.CharField(required=False, allow_blank=True, max_length=255)


class UpdatePaymentStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=OnlinePayment.STATUS_CHOICES)
    gateway = serializers.CharField(required=False, allow_blank=True, max_length=40)
    reference = serializers.CharField(required=False, allow_blank=True, max_length=120)
    gateway_payment_id = serializers.CharField(required=False, allow_blank=True, max_length=120)
    failure_reason = serializers.CharField(required=False, allow_blank=True, max_length=255)


class RefundPaymentSerializer(serializers.Serializer):
    refunded_amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.01'))
    reference = serializers.CharField(required=False, allow_blank=True, max_length=120)
