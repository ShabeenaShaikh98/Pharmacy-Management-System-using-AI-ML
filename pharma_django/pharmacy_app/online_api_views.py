import datetime
from decimal import Decimal
from io import BytesIO

from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
except ImportError:
    A4 = None
    canvas = None

from .models import (
    CustomerProfile,
    Medicine,
    OnlineCart,
    OnlineCartItem,
    OnlineOrder,
    OnlinePayment,
    OnlinePrescription,
)
from .online_serializers import (
    AddCartItemSerializer,
    AssignDeliverySerializer,
    CheckoutSerializer,
    OnlineCartSerializer,
    OnlineMedicineCatalogSerializer,
    OnlineOrderDetailSerializer,
    OnlineOrderListSerializer,
    OnlinePaymentSerializer,
    OnlinePrescriptionSerializer,
    RefundPaymentSerializer,
    ReviewPrescriptionSerializer,
    UpdateCartItemSerializer,
    UpdateOrderStatusSerializer,
    UpdatePaymentStatusSerializer,
)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class IsStaffAdminMixin:
    def ensure_staff(self, request):
        if not request.user.is_staff:
            return Response({'detail': 'Only staff admin can perform this action.'}, status=403)
        return None


def _customer_profile(user):
    profile, _ = CustomerProfile.objects.get_or_create(user=user)
    return profile


def _customer_cart(user):
    profile = _customer_profile(user)
    cart, _ = OnlineCart.objects.get_or_create(customer=profile)
    return profile, cart


class OnlineDashboardAPI(APIView, IsStaffAdminMixin):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        staff_guard = self.ensure_staff(request)
        if staff_guard:
            return staff_guard

        today = timezone.now().date()
        month_start = today.replace(day=1)
        week_start = today - datetime.timedelta(days=6)

        recent_orders = OnlineOrder.objects.select_related('customer__user').order_by('-created_at')[:10]
        recent_data = OnlineOrderListSerializer(recent_orders, many=True).data

        data = {
            'total_revenue': float(
                OnlineOrder.objects.filter(
                    status__in=['approved', 'packed', 'out_for_delivery', 'delivered']
                ).aggregate(total=Sum('total_amount'))['total'] or 0
            ),
            'month_revenue': float(
                OnlineOrder.objects.filter(
                    created_at__date__gte=month_start,
                    status__in=['approved', 'packed', 'out_for_delivery', 'delivered']
                ).aggregate(total=Sum('total_amount'))['total'] or 0
            ),
            'week_revenue': float(
                OnlineOrder.objects.filter(
                    created_at__date__gte=week_start,
                    status__in=['approved', 'packed', 'out_for_delivery', 'delivered']
                ).aggregate(total=Sum('total_amount'))['total'] or 0
            ),
            'total_orders': OnlineOrder.objects.count(),
            'pending_orders': OnlineOrder.objects.filter(status='pending').count(),
            'total_customers': CustomerProfile.objects.count(),
            'low_stock_medicines': Medicine.objects.filter(
                quantity__gt=0, quantity__lt=20, is_online_available=True
            ).count(),
            'status_counts': list(
                OnlineOrder.objects.values('status').annotate(total=Count('id')).order_by('status')
            ),
            'recent_orders': recent_data,
        }
        return Response(data)


class OnlineMedicineCatalogAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Medicine.objects.filter(is_online_available=True, quantity__gt=0).select_related(
            'generic_name', 'presentation'
        )
        q = request.query_params.get('q', '').strip()
        prescription = request.query_params.get('prescription', '').strip().lower()
        near_expiry = request.query_params.get('near_expiry', '').strip().lower()
        low_stock = request.query_params.get('low_stock', '').strip().lower()
        sort = request.query_params.get('sort', 'name')

        if q:
            qs = qs.filter(
                Q(name__icontains=q) |
                Q(generic_name__name__icontains=q) |
                Q(description__icontains=q)
            )
        if prescription in {'true', '1', 'yes'}:
            qs = qs.filter(prescription_required=True)
        if near_expiry in {'true', '1', 'yes'}:
            qs = qs.filter(expire_date__lte=timezone.now().date() + datetime.timedelta(days=30))
        if low_stock in {'true', '1', 'yes'}:
            qs = qs.filter(quantity__gt=0, quantity__lt=20)

        if sort == '-price':
            qs = qs.order_by('-selling_price', 'name')
        elif sort == 'price':
            qs = qs.order_by('selling_price', 'name')
        elif sort == '-updated':
            qs = qs.order_by('-updated_at')
        else:
            qs = qs.order_by('name')

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = OnlineMedicineCatalogSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class OnlineCartAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        _, cart = _customer_cart(request.user)
        cart = OnlineCart.objects.prefetch_related('items__medicine').get(pk=cart.pk)
        return Response(OnlineCartSerializer(cart).data)


class OnlineCartItemsAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        _, cart = _customer_cart(request.user)
        medicine = serializer.validated_data['medicine']
        quantity = serializer.validated_data['quantity']

        cart_item, created = OnlineCartItem.objects.get_or_create(
            cart=cart,
            medicine=medicine,
            defaults={'quantity': quantity}
        )
        if not created:
            new_qty = cart_item.quantity + quantity
            if new_qty > medicine.quantity:
                return Response({'detail': f'Only {medicine.quantity} units available.'}, status=400)
            cart_item.quantity = new_qty
            cart_item.save(update_fields=['quantity'])

        cart = OnlineCart.objects.prefetch_related('items__medicine').get(pk=cart.pk)
        return Response(OnlineCartSerializer(cart).data, status=201)


class OnlineCartItemDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, item_id):
        serializer = UpdateCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        quantity = serializer.validated_data['quantity']

        item = get_object_or_404(OnlineCartItem, id=item_id, cart__customer__user=request.user)
        if quantity == 0:
            item.delete()
            return Response({'detail': 'Item removed from cart.'})
        if quantity > item.medicine.quantity:
            return Response({'detail': f'Only {item.medicine.quantity} units available.'}, status=400)
        item.quantity = quantity
        item.save(update_fields=['quantity'])
        return Response({'detail': 'Cart updated.'})

    def delete(self, request, item_id):
        item = get_object_or_404(OnlineCartItem, id=item_id, cart__customer__user=request.user)
        item.delete()
        return Response({'detail': 'Item removed from cart.'})


class OnlinePrescriptionAPI(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        profile = _customer_profile(request.user)
        queryset = OnlinePrescription.objects.filter(customer=profile).select_related('reviewed_by')
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = OnlinePrescriptionSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        profile = _customer_profile(request.user)
        image = request.FILES.get('image')
        if not image:
            return Response({'detail': 'Prescription file is required.'}, status=400)
        prescription = OnlinePrescription.objects.create(customer=profile, image=image, status='pending')
        return Response(OnlinePrescriptionSerializer(prescription).data, status=201)


class OnlinePrescriptionReviewAPI(APIView, IsStaffAdminMixin):
    permission_classes = [IsAuthenticated]

    def post(self, request, prescription_id):
        staff_guard = self.ensure_staff(request)
        if staff_guard:
            return staff_guard

        prescription = get_object_or_404(OnlinePrescription, id=prescription_id)
        serializer = ReviewPrescriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data['action']
        review_note = serializer.validated_data.get('review_note', '').strip()

        prescription.status = action
        prescription.review_note = review_note
        prescription.reviewed_by = request.user
        prescription.reviewed_at = timezone.now()
        prescription.save(update_fields=['status', 'review_note', 'reviewed_by', 'reviewed_at'])
        return Response(OnlinePrescriptionSerializer(prescription).data)


class OnlineCheckoutAPI(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        profile, cart = _customer_cart(request.user)
        items = list(cart.items.select_related('medicine').all())
        if not items:
            return Response({'detail': 'Cart is empty.'}, status=400)

        needs_prescription = any(item.medicine.prescription_required for item in items)
        selected_prescription = None
        prescription_id = payload.get('prescription_id')

        if needs_prescription:
            if not prescription_id:
                return Response({'detail': 'Prescription is required for restricted medicines.'}, status=400)
            selected_prescription = get_object_or_404(OnlinePrescription, id=prescription_id, customer=profile)
            if selected_prescription.status != 'approved':
                return Response({'detail': 'Selected prescription is not approved yet.'}, status=400)

        medicine_ids = [item.medicine_id for item in items]
        locked_medicines = {
            med.id: med for med in Medicine.objects.select_for_update().filter(id__in=medicine_ids)
        }
        cart_total = Decimal('0')
        for item in items:
            medicine = locked_medicines.get(item.medicine_id)
            if not medicine or medicine.quantity < item.quantity:
                return Response({'detail': f'Insufficient stock for {item.medicine.name}.'}, status=400)
            cart_total += item.quantity * medicine.selling_price

        order = OnlineOrder.objects.create(
            customer=profile,
            prescription=selected_prescription,
            status='pending',
            payment_method=payload['payment_method'],
            customer_name=payload.get('customer_name') or request.user.get_full_name() or request.user.username,
            customer_phone=payload['customer_phone'],
            delivery_address=payload['delivery_address'],
            notes=payload.get('notes', ''),
            total_amount=cart_total,
        )
        order.log_status('pending', changed_by=request.user, note='Order placed')

        for item in items:
            medicine = locked_medicines[item.medicine_id]
            line_total = item.quantity * medicine.selling_price
            order.items.create(
                medicine=medicine,
                quantity=item.quantity,
                unit_price=medicine.selling_price,
                line_total=line_total,
            )
            medicine.quantity -= item.quantity
            medicine.save(update_fields=['quantity', 'updated_at'])

        gateway = 'cod' if payload['payment_method'] == 'cod' else 'online'
        OnlinePayment.objects.create(
            order=order,
            method=payload['payment_method'],
            status='pending',
            gateway=gateway,
            amount=cart_total,
        )

        cart.items.all().delete()
        order = OnlineOrder.objects.select_related('payment', 'customer__user').prefetch_related(
            'items__medicine', 'status_logs'
        ).get(id=order.id)
        return Response(OnlineOrderDetailSerializer(order).data, status=201)


class OnlineOrdersAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = OnlineOrder.objects.select_related('customer__user', 'payment', 'delivery_partner').all()
        status_filter = request.query_params.get('status', '').strip()
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if not request.user.is_staff:
            queryset = queryset.filter(customer__user=request.user)
        queryset = queryset.order_by('-created_at')

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = OnlineOrderListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class OnlineOrderDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        order = get_object_or_404(
            OnlineOrder.objects.select_related(
                'customer__user', 'payment', 'prescription', 'delivery_partner'
            ).prefetch_related('items__medicine', 'status_logs__changed_by'),
            id=order_id
        )
        if not request.user.is_staff and order.customer.user_id != request.user.id:
            return Response({'detail': 'You are not allowed to view this order.'}, status=403)
        return Response(OnlineOrderDetailSerializer(order).data)


class OnlineOrderStatusAPI(APIView, IsStaffAdminMixin):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        staff_guard = self.ensure_staff(request)
        if staff_guard:
            return staff_guard

        order = get_object_or_404(OnlineOrder, id=order_id)
        serializer = UpdateOrderStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data['status']
        note = serializer.validated_data.get('note', '').strip()

        order.status = new_status
        order.save(update_fields=['status', 'updated_at'])
        order.log_status(new_status, changed_by=request.user, note=note or 'Status updated')
        return Response({'detail': f'Order status updated to {order.get_status_display()}.'})


class OnlineAssignDeliveryAPI(APIView, IsStaffAdminMixin):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        staff_guard = self.ensure_staff(request)
        if staff_guard:
            return staff_guard

        order = get_object_or_404(OnlineOrder, id=order_id)
        serializer = AssignDeliverySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        delivery_partner = get_object_or_404(User, id=serializer.validated_data['delivery_partner_id'])
        order.delivery_partner = delivery_partner
        order.delivery_assigned_at = timezone.now()
        order.save(update_fields=['delivery_partner', 'delivery_assigned_at', 'updated_at'])
        order.log_status(order.status, changed_by=request.user, note=serializer.validated_data.get('note', 'Delivery assigned'))
        return Response({'detail': f'Delivery assigned to {delivery_partner.username}.'})


class OnlinePaymentsAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = OnlinePayment.objects.select_related('order', 'order__customer__user').all()
        status_filter = request.query_params.get('status', '').strip()
        if status_filter:
            qs = qs.filter(status=status_filter)
        if not request.user.is_staff:
            qs = qs.filter(order__customer__user=request.user)
        qs = qs.order_by('-created_at')

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = OnlinePaymentSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class OnlinePaymentStatusAPI(APIView, IsStaffAdminMixin):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        staff_guard = self.ensure_staff(request)
        if staff_guard:
            return staff_guard

        payment = get_object_or_404(OnlinePayment, order_id=order_id)
        serializer = UpdatePaymentStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        payment.status = payload['status']
        payment.gateway = payload.get('gateway', payment.gateway)
        payment.reference = payload.get('reference', payment.reference)
        payment.gateway_payment_id = payload.get('gateway_payment_id', payment.gateway_payment_id)
        payment.failure_reason = payload.get('failure_reason', payment.failure_reason)
        if payment.amount <= 0:
            payment.amount = payment.order.total_amount
        payment.save()
        return Response(OnlinePaymentSerializer(payment).data)


class OnlinePaymentRefundAPI(APIView, IsStaffAdminMixin):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        staff_guard = self.ensure_staff(request)
        if staff_guard:
            return staff_guard

        payment = get_object_or_404(OnlinePayment, order_id=order_id)
        serializer = RefundPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refunded_amount = serializer.validated_data['refunded_amount']

        if payment.status != 'paid':
            return Response({'detail': 'Refund is allowed only for paid transactions.'}, status=400)
        if refunded_amount > payment.amount:
            return Response({'detail': 'Refund amount cannot exceed paid amount.'}, status=400)

        payment.refund_status = 'processed'
        payment.refunded_amount = refunded_amount
        payment.refunded_at = timezone.now()
        reference = serializer.validated_data.get('reference')
        if reference:
            payment.reference = reference
        payment.save(update_fields=['refund_status', 'refunded_amount', 'refunded_at', 'reference', 'updated_at'])
        return Response(OnlinePaymentSerializer(payment).data)


class OnlineInvoicePDFAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        if canvas is None or A4 is None:
            return Response(
                {'detail': 'Invoice PDF feature requires reportlab. Install it with: pip install reportlab==4.0.7'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        order = get_object_or_404(
            OnlineOrder.objects.select_related('customer__user', 'payment').prefetch_related('items__medicine'),
            id=order_id
        )
        if not request.user.is_staff and order.customer.user_id != request.user.id:
            return Response({'detail': 'You are not allowed to access this invoice.'}, status=403)

        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        y = height - 50
        pdf.setFont('Helvetica-Bold', 16)
        pdf.drawString(40, y, 'Pharmacy Online Invoice')
        y -= 28
        pdf.setFont('Helvetica', 10)
        pdf.drawString(40, y, f'Order ID: {order.order_id}')
        y -= 16
        pdf.drawString(40, y, f'Date: {order.created_at:%d %b %Y %H:%M}')
        y -= 16
        pdf.drawString(40, y, f'Customer: {order.customer_name or order.customer.user.username}')
        y -= 16
        pdf.drawString(40, y, f'Phone: {order.customer_phone}')
        y -= 16
        pdf.drawString(40, y, f'Address: {order.delivery_address[:85]}')
        y -= 24

        pdf.setFont('Helvetica-Bold', 11)
        pdf.drawString(40, y, 'Medicine')
        pdf.drawString(290, y, 'Qty')
        pdf.drawString(340, y, 'Price')
        pdf.drawString(430, y, 'Line Total')
        y -= 14
        pdf.line(40, y, width - 40, y)
        y -= 14

        pdf.setFont('Helvetica', 10)
        for item in order.items.all():
            if y < 90:
                pdf.showPage()
                y = height - 50
            pdf.drawString(40, y, item.medicine.name[:38])
            pdf.drawRightString(320, y, str(item.quantity))
            pdf.drawRightString(400, y, f'Rs.{item.unit_price}')
            pdf.drawRightString(520, y, f'Rs.{item.line_total}')
            y -= 16

        y -= 8
        pdf.line(330, y, width - 40, y)
        y -= 18
        pdf.setFont('Helvetica-Bold', 12)
        pdf.drawRightString(520, y, f'Total: Rs.{order.total_amount}')

        if hasattr(order, 'payment'):
            y -= 20
            pdf.setFont('Helvetica', 10)
            pdf.drawRightString(
                520, y,
                f'Payment: {order.payment.method.upper()} | Status: {order.payment.status.upper()}'
            )

        pdf.showPage()
        pdf.save()
        buffer.seek(0)

        response = HttpResponse(buffer.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{order.order_id}.pdf"'
        return response
