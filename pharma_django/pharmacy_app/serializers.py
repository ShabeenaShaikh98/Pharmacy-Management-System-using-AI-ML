from django.db import transaction
from rest_framework import serializers
from .models import (
    GenericName, MedicinePresentation, Supplier,
    Medicine, Purchase, Sale, SaleItem, ChatMessage, OCRPrescription
)


class GenericNameSerializer(serializers.ModelSerializer):
    medicine_count = serializers.SerializerMethodField()

    class Meta:
        model = GenericName
        fields = '__all__'

    def get_medicine_count(self, obj):
        return obj.medicines.count()


class MedicinePresentationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicinePresentation
        fields = '__all__'


class SupplierSerializer(serializers.ModelSerializer):
    total_medicines = serializers.ReadOnlyField()

    class Meta:
        model = Supplier
        fields = '__all__'


class MedicineSerializer(serializers.ModelSerializer):
    generic_name_display = serializers.CharField(source='generic_name.name', read_only=True)
    presentation_display = serializers.CharField(source='presentation.name', read_only=True)
    supplier_display = serializers.CharField(source='supplier.company_name', read_only=True)
    stock_status = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    profit_margin = serializers.ReadOnlyField()

    class Meta:
        model = Medicine
        fields = '__all__'


class MedicineListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for dropdowns"""
    class Meta:
        model = Medicine
        fields = ['id', 'name', 'selling_price', 'quantity', 'volume']


class PurchaseSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.company_name', read_only=True)

    class Meta:
        model = Purchase
        fields = '__all__'


class SaleItemSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)

    class Meta:
        model = SaleItem
        fields = '__all__'


class SaleItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleItem
        fields = ['medicine', 'quantity', 'unit_price', 'discount']


class SaleSerializer(serializers.ModelSerializer):
    items = SaleItemSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = Sale
        fields = '__all__'


class SaleCreateSerializer(serializers.ModelSerializer):
    items = SaleItemCreateSerializer(many=True)

    class Meta:
        model = Sale
        fields = ['customer_name', 'customer_email', 'customer_phone',
                  'discount', 'paid_amount', 'notes', 'items']

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError('At least one sale item is required.')

        for item in items:
            medicine = item['medicine']
            quantity = item['quantity']
            if quantity <= 0:
                raise serializers.ValidationError(f'Quantity for {medicine.name} must be greater than zero.')
            if medicine.quantity < quantity:
                raise serializers.ValidationError(
                    f'Insufficient stock for {medicine.name}. Available: {medicine.quantity}, requested: {quantity}.'
                )
        return items

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        request = self.context.get('request')
        with transaction.atomic():
            sale = Sale.objects.create(
                invoice_number=Sale.generate_invoice_number(),
                created_by=request.user if request else None,
                **validated_data
            )
            total = 0
            for item_data in items_data:
                med = item_data['medicine']
                qty = item_data['quantity']
                price = item_data.get('unit_price', med.selling_price)
                discount = item_data.get('discount', 0)
                sub = (price * qty) - discount

                SaleItem.objects.create(
                    sale=sale,
                    medicine=med,
                    quantity=qty,
                    unit_price=price,
                    discount=discount,
                    sub_total=sub
                )
                med.quantity -= qty
                med.save(update_fields=['quantity', 'updated_at'])
                total += sub

            sale.total_amount = total
            sale.sub_total = total - sale.discount
            sale.change_amount = max(0, sale.paid_amount - sale.sub_total)
            sale.save()
        return sale


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'role', 'message', 'created_at']


class OCRPrescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = OCRPrescription
        fields = '__all__'
