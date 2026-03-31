from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.db.models import Sum, Count, Q, Avg
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
import datetime
import json

from .models import (
    Medicine, GenericName, MedicinePresentation, Supplier,
    Purchase, Sale, SaleItem, ChatMessage, OCRPrescription, OnlineOrder,
    OnlinePrescription
)
from .serializers import (
    MedicineSerializer, MedicineListSerializer,
    GenericNameSerializer, MedicinePresentationSerializer,
    SupplierSerializer, PurchaseSerializer,
    SaleSerializer, SaleCreateSerializer,
    ChatMessageSerializer, OCRPrescriptionSerializer
)
from ml_engine.chat_ai import PharmacyAI
from ml_engine.recommender import MedicineRecommender
from ml_engine.ocr import extract_prescription_text

# ─────────────────────────────────────────────
# GENERIC NAMES API
# ─────────────────────────────────────────────

class GenericNameListCreateAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = GenericName.objects.all()
        q = request.query_params.get('q', '')
        if q:
            qs = qs.filter(name__icontains=q)
        return Response(GenericNameSerializer(qs, many=True).data)

    def post(self, request):
        s = GenericNameSerializer(data=request.data)
        if s.is_valid():
            s.save()
            return Response(s.data, status=status.HTTP_201_CREATED)
        return Response(s.errors, status=400)


class GenericNameDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        obj = get_object_or_404(GenericName, pk=pk)
        s = GenericNameSerializer(obj, data=request.data, partial=True)
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=400)

    def delete(self, request, pk):
        get_object_or_404(GenericName, pk=pk).delete()
        return Response({'success': True})


# ─────────────────────────────────────────────
# PRESENTATIONS API
# ─────────────────────────────────────────────

class PresentationListCreateAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = MedicinePresentation.objects.all()
        return Response(MedicinePresentationSerializer(qs, many=True).data)

    def post(self, request):
        s = MedicinePresentationSerializer(data=request.data)
        if s.is_valid():
            s.save()
            return Response(s.data, status=201)
        return Response(s.errors, status=400)


class PresentationDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        get_object_or_404(MedicinePresentation, pk=pk).delete()
        return Response({'success': True})


# ─────────────────────────────────────────────
# SUPPLIERS API
# ─────────────────────────────────────────────

class SupplierListCreateAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Supplier.objects.all()
        q = request.query_params.get('q', '')
        if q:
            qs = qs.filter(company_name__icontains=q)
        return Response(SupplierSerializer(qs, many=True).data)

    def post(self, request):
        s = SupplierSerializer(data=request.data)
        if s.is_valid():
            s.save()
            return Response(s.data, status=201)
        return Response(s.errors, status=400)


class SupplierDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        obj = get_object_or_404(Supplier, pk=pk)
        return Response(SupplierSerializer(obj).data)

    def put(self, request, pk):
        obj = get_object_or_404(Supplier, pk=pk)
        s = SupplierSerializer(obj, data=request.data, partial=True)
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=400)

    def delete(self, request, pk):
        get_object_or_404(Supplier, pk=pk).delete()
        return Response({'success': True})


# ─────────────────────────────────────────────
# MEDICINES API
# ─────────────────────────────────────────────

class MedicineListCreateAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Medicine.objects.select_related('generic_name', 'presentation', 'supplier').all()
        q = request.query_params.get('q', '')
        stock = request.query_params.get('stock', '')
        generic = request.query_params.get('generic', '')
        presentation = request.query_params.get('presentation', '')

        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(generic_name__name__icontains=q))
        if stock == 'out':
            qs = qs.filter(quantity=0)
        elif stock == 'low':
            qs = qs.filter(quantity__gt=0, quantity__lt=20)
        elif stock == 'expired':
            qs = qs.filter(expire_date__lt=timezone.now().date())
        if generic:
            qs = qs.filter(generic_name_id=generic)
        if presentation:
            qs = qs.filter(presentation_id=presentation)

        return Response(MedicineSerializer(qs, many=True).data)

    def post(self, request):
        s = MedicineSerializer(data=request.data)
        if s.is_valid():
            s.save()
            return Response(s.data, status=201)
        return Response(s.errors, status=400)


class MedicineDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        obj = get_object_or_404(Medicine.objects.select_related('generic_name', 'presentation', 'supplier'), pk=pk)
        return Response(MedicineSerializer(obj).data)

    def put(self, request, pk):
        obj = get_object_or_404(Medicine, pk=pk)
        s = MedicineSerializer(obj, data=request.data, partial=True)
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=400)

    def delete(self, request, pk):
        get_object_or_404(Medicine, pk=pk).delete()
        return Response({'success': True})


# ─────────────────────────────────────────────
# PURCHASE API
# ─────────────────────────────────────────────

class PurchaseListCreateAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Purchase.objects.select_related('medicine', 'supplier').all()
        return Response(PurchaseSerializer(qs, many=True).data)

    def post(self, request):
        s = PurchaseSerializer(data=request.data)
        if s.is_valid():
            purchase = s.save(created_by=request.user)
            # Update medicine stock
            med = purchase.medicine
            med.quantity += purchase.quantity
            med.unit_price = purchase.unit_price
            med.save()
            return Response(PurchaseSerializer(purchase).data, status=201)
        return Response(s.errors, status=400)


class PurchaseDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        obj = get_object_or_404(Purchase.objects.select_related('medicine', 'supplier'), pk=pk)
        return Response(PurchaseSerializer(obj).data)

    def put(self, request, pk):
        obj = get_object_or_404(Purchase, pk=pk)
        s = PurchaseSerializer(obj, data=request.data, partial=True)
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=400)

    def delete(self, request, pk):
        get_object_or_404(Purchase, pk=pk).delete()
        return Response({'success': True})


# ─────────────────────────────────────────────
# SALES API
# ─────────────────────────────────────────────

class SaleListCreateAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Sale.objects.prefetch_related('items__medicine').select_related('created_by').all()
        date_from = request.query_params.get('from', '')
        date_to = request.query_params.get('to', '')
        if date_from:
            qs = qs.filter(sale_date__date__gte=date_from)
        if date_to:
            qs = qs.filter(sale_date__date__lte=date_to)
        return Response(SaleSerializer(qs[:200], many=True).data)

    def post(self, request):
        s = SaleCreateSerializer(data=request.data, context={'request': request})
        if s.is_valid():
            sale = s.save()
            return Response(SaleSerializer(sale).data, status=201)
        return Response(s.errors, status=400)


class SaleDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        obj = get_object_or_404(Sale.objects.prefetch_related('items__medicine'), pk=pk)
        return Response(SaleSerializer(obj).data)

    def delete(self, request, pk):
        get_object_or_404(Sale, pk=pk).delete()
        return Response({'success': True})


# ─────────────────────────────────────────────
# ANALYTICS / REPORTS API
# ─────────────────────────────────────────────

class DashboardStatsAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        month_start = today.replace(day=1)
        data = {
            'total_medicines': Medicine.objects.count(),
            'out_of_stock': Medicine.objects.filter(quantity=0).count(),
            'low_stock': Medicine.objects.filter(quantity__gt=0, quantity__lt=20).count(),
            'expiring_soon': Medicine.objects.filter(
                expire_date__lte=today + datetime.timedelta(days=30),
                expire_date__gte=today
            ).count(),
            'expired': Medicine.objects.filter(expire_date__lt=today).count(),
            'total_suppliers': Supplier.objects.count(),
            'today_sales': float(Sale.objects.filter(sale_date__date=today).aggregate(t=Sum('sub_total'))['t'] or 0),
            'month_sales': float(Sale.objects.filter(sale_date__date__gte=month_start).aggregate(t=Sum('sub_total'))['t'] or 0),
        }
        return Response(data)


class SalesSummaryAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            days = max(1, int(request.query_params.get('days', 30)))
        except (TypeError, ValueError):
            return Response({'error': 'days must be a positive integer'}, status=400)
        today = timezone.now().date()
        start = today - datetime.timedelta(days=days - 1)

        by_day = (
            Sale.objects.filter(sale_date__date__gte=start)
            .annotate(day=TruncDate('sale_date'))
            .values('day')
            .annotate(revenue=Sum('sub_total'), count=Count('id'))
            .order_by('day')
        )
        return Response(list(by_day))


class MedicinePerformanceAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = (
            SaleItem.objects
            .values('medicine__id', 'medicine__name')
            .annotate(
                total_sold=Sum('quantity'),
                revenue=Sum('sub_total'),
                transactions=Count('sale', distinct=True)
            )
            .order_by('-revenue')[:50]
        )
        return Response(list(data))


class StockAlertAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        qs = Medicine.objects.filter(
            Q(quantity=0) | Q(quantity__lt=20) |
            Q(expire_date__lt=today) |
            Q(expire_date__lte=today + datetime.timedelta(days=30))
        ).select_related('generic_name', 'presentation')
        return Response(MedicineSerializer(qs, many=True).data)


class InventoryReportAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Medicine.objects.select_related('generic_name', 'presentation', 'supplier').all()
        return Response(MedicineSerializer(qs, many=True).data)


# ─────────────────────────────────────────────
# CHAT AI API
# ─────────────────────────────────────────────

class ChatAPI(APIView):
    permission_classes = [IsAuthenticated]

    OVERVIEW_KEYWORDS = [
        'help', 'what can you do', 'all details', 'everything', 'full details',
        'system status', 'dashboard summary', 'overview', 'summary', 'report',
    ]
    STOCK_KEYWORDS = ['stock', 'inventory', 'out of stock', 'low stock', 'expiry', 'expired']
    SALES_KEYWORDS = ['sale', 'sales', 'revenue', 'invoice', 'billing', 'today', 'month', 'total']
    SUPPLIER_KEYWORDS = ['supplier', 'vendor', 'company']
    RECOMMEND_KEYWORDS = ['recommend', 'suggest', 'alternative', 'similar', 'price', 'search', 'find']
    ORDER_KEYWORDS = ['order', 'online order', 'checkout', 'cart', 'delivery', 'pending', 'packed', 'delivered']
    WORKFLOW_KEYWORDS = [
        'website', 'whole website', 'full website', 'all modules', 'all work', 'all workflow',
        'workflow', 'guide', 'how to', 'how to use', 'how to work', 'process', 'module',
        'poora website', 'sab kaam', 'kaise karu', 'kese karu', 'system guide',
    ]

    def _has_keyword(self, message, keywords):
        lowered = message.lower()
        return any(keyword in lowered for keyword in keywords)

    def _build_suggestions(self, message=''):
        base = [
            'Website workflow guide',
            'Show out of stock medicines',
            'Give me expiry alerts',
            "Show today's sales",
            'Search Crocin',
            'Recommend fever medicine',
            'Show online order status',
        ]
        lowered = message.lower()
        if self._has_keyword(lowered, self.WORKFLOW_KEYWORDS):
            return [
                'Show system overview',
                'How to create billing invoice',
                'How to import medicines from Excel',
                'How to process online orders',
            ]
        if self._has_keyword(lowered, self.SALES_KEYWORDS):
            return ['Show monthly sales', 'Show total sales', 'Top selling medicines', 'Recent invoices']
        if self._has_keyword(lowered, self.STOCK_KEYWORDS):
            return ['Low stock medicines', 'Expired medicines', 'Inventory summary', 'Search Paracetamol']
        if self._has_keyword(lowered, self.RECOMMEND_KEYWORDS):
            return ['Price of Crocin', 'Alternative for Ibuprofen', 'Search Dolo', 'Show suppliers']
        if self._has_keyword(lowered, self.ORDER_KEYWORDS):
            return ['Show pending online orders', 'Show delivered online orders', 'How to place online order', 'Open checkout flow']
        return base

    def _build_workflow_guide_response(self):
        return (
            "Here is your full website workflow guide:\n\n"
            "1) Dashboard: use `system overview` to check stock, sales, expiry, and online order status.\n"
            "2) Medicines: add/update medicine, generic, presentation, supplier, quantity, prices, expiry.\n"
            "3) Inventory & Purchase: add purchase entries to increase stock and update unit price.\n"
            "4) Excel Import/Export: export sample file, edit rows, then import to bulk update medicines.\n"
            "5) Sales/Billing: create invoice from New Sale, then view in Sales History and Reports.\n"
            "6) Reports & Analytics: check trends, top medicines, revenue summaries.\n"
            "7) Online Store: manage online medicines, cart, checkout, prescription approvals, order status.\n"
            "8) AI/ML Tools: use OCR Prescription and ML Recommender for smarter operations.\n"
            "9) User Management (Super Admin): manage users/roles from Manage Users or Django Admin.\n\n"
            "You can ask me anything in natural language, for example:\n"
            "- `show low stock medicines`\n"
            "- `today sales summary`\n"
            "- `show pending online orders`\n"
            "- `how to import medicines from excel`\n"
            "- `price of dolo`\n"
        )

    def _build_online_order_context(self):
        status_counts = list(
            OnlineOrder.objects.values('status').annotate(total=Count('id')).order_by('status')
        )
        items = [
            {
                'title': row['status'].replace('_', ' ').title(),
                'meta': f"{row['total']} orders",
                'kind': 'info' if row['status'] != 'pending' else 'warning',
            }
            for row in status_counts
        ]
        recent = OnlineOrder.objects.select_related('customer__user').order_by('-created_at')[:6]
        items.extend(
            {
                'title': order.order_id,
                'meta': f"{order.customer_name or order.customer.user.username} | Rs. {order.total_amount} | {order.get_status_display()}",
                'kind': 'success' if order.status == 'delivered' else 'warning' if order.status == 'pending' else 'info',
            }
            for order in recent
        )
        return {
            'title': 'Online order details',
            'summary_cards': [
                {'label': 'Online Orders', 'value': OnlineOrder.objects.count(), 'tone': 'info'},
                {'label': 'Pending', 'value': OnlineOrder.objects.filter(status='pending').count(), 'tone': 'warning'},
                {'label': 'Delivered', 'value': OnlineOrder.objects.filter(status='delivered').count(), 'tone': 'success'},
            ],
            'items': items[:12],
        }

    def _build_overview_context(self):
        today = timezone.now().date()
        month_start = today.replace(day=1)
        low_stock_qs = Medicine.objects.filter(quantity__gt=0, quantity__lt=20).select_related('generic_name')[:5]
        expiring_qs = Medicine.objects.filter(
            expire_date__gte=today,
            expire_date__lte=today + datetime.timedelta(days=30)
        ).select_related('generic_name')[:5]
        recent_sales = Sale.objects.select_related('created_by').order_by('-sale_date')[:5]

        items = []
        for medicine in low_stock_qs:
            items.append({
                'title': medicine.name,
                'meta': f'Low stock: {medicine.quantity} units left',
                'kind': 'warning',
            })
        for medicine in expiring_qs:
            items.append({
                'title': medicine.name,
                'meta': f'Expiry: {medicine.expire_date}',
                'kind': 'danger',
            })
        for sale in recent_sales:
            items.append({
                'title': sale.invoice_number,
                'meta': f'Sale {sale.sale_date:%d %b %Y} | Rs. {sale.sub_total}',
                'kind': 'info',
            })

        return {
            'title': 'System overview',
            'summary_cards': [
                {'label': 'Medicines', 'value': Medicine.objects.count(), 'tone': 'info'},
                {'label': 'Out of stock', 'value': Medicine.objects.filter(quantity=0).count(), 'tone': 'danger'},
                {'label': 'Low stock', 'value': Medicine.objects.filter(quantity__gt=0, quantity__lt=20).count(), 'tone': 'warning'},
                {'label': 'Expiring soon', 'value': Medicine.objects.filter(expire_date__gte=today, expire_date__lte=today + datetime.timedelta(days=30)).count(), 'tone': 'warning'},
                {'label': 'Suppliers', 'value': Supplier.objects.count(), 'tone': 'info'},
                {'label': 'Today sales', 'value': f"Rs. {float(Sale.objects.filter(sale_date__date=today).aggregate(total=Sum('sub_total'))['total'] or 0):.2f}", 'tone': 'success'},
                {'label': 'Month sales', 'value': f"Rs. {float(Sale.objects.filter(sale_date__date__gte=month_start).aggregate(total=Sum('sub_total'))['total'] or 0):.2f}", 'tone': 'success'},
            ],
            'items': items[:8],
        }

    def _build_workflow_context(self):
        return {
            'title': 'Website workflow',
            'summary_cards': [
                {'label': 'Total Users', 'value': User.objects.count(), 'tone': 'info'},
                {'label': 'Super Admin', 'value': User.objects.filter(is_superuser=True, is_staff=True).count(), 'tone': 'info'},
                {'label': 'Admin Staff', 'value': User.objects.filter(is_staff=True, is_superuser=False).count(), 'tone': 'info'},
                {'label': 'Customers', 'value': User.objects.filter(is_staff=False, is_superuser=False).count(), 'tone': 'info'},
                {'label': 'Medicines', 'value': Medicine.objects.count(), 'tone': 'info'},
                {'label': 'Suppliers', 'value': Supplier.objects.count(), 'tone': 'info'},
                {'label': 'Total Sales', 'value': Sale.objects.count(), 'tone': 'success'},
                {'label': 'Online Orders', 'value': OnlineOrder.objects.count(), 'tone': 'info'},
                {'label': 'Pending Orders', 'value': OnlineOrder.objects.filter(status='pending').count(), 'tone': 'warning'},
                {'label': 'Online RX', 'value': OnlinePrescription.objects.count(), 'tone': 'info'},
                {'label': 'OCR Records', 'value': OCRPrescription.objects.count(), 'tone': 'info'},
            ],
            'items': [
                {'title': 'Dashboard', 'meta': 'System overview, alerts, key metrics', 'kind': 'info'},
                {'title': 'Medicines', 'meta': 'Create/update medicines, stock, price, expiry', 'kind': 'info'},
                {'title': 'Inventory & Purchase', 'meta': 'Purchase entries and stock increase', 'kind': 'info'},
                {'title': 'Excel Tools', 'meta': 'Bulk export/import medicine data', 'kind': 'info'},
                {'title': 'Sales & Billing', 'meta': 'Invoice creation and sales history', 'kind': 'success'},
                {'title': 'Reports', 'meta': 'Revenue trends and top-selling analysis', 'kind': 'success'},
                {'title': 'Online Purchase', 'meta': 'Order processing and prescription review', 'kind': 'warning'},
                {'title': 'AI / ML', 'meta': 'OCR + medicine recommendation tools', 'kind': 'info'},
            ],
        }

    def _build_stock_context(self):
        today = timezone.now().date()
        items = []
        for medicine in Medicine.objects.filter(quantity=0).select_related('generic_name')[:5]:
            items.append({'title': medicine.name, 'meta': 'Out of stock', 'kind': 'danger'})
        for medicine in Medicine.objects.filter(quantity__gt=0, quantity__lt=20).select_related('generic_name')[:5]:
            items.append({'title': medicine.name, 'meta': f'Only {medicine.quantity} units left', 'kind': 'warning'})
        for medicine in Medicine.objects.filter(expire_date__lt=today).select_related('generic_name')[:5]:
            items.append({'title': medicine.name, 'meta': f'Expired on {medicine.expire_date}', 'kind': 'danger'})

        return {
            'title': 'Stock details',
            'summary_cards': [
                {'label': 'Out of stock', 'value': Medicine.objects.filter(quantity=0).count(), 'tone': 'danger'},
                {'label': 'Low stock', 'value': Medicine.objects.filter(quantity__gt=0, quantity__lt=20).count(), 'tone': 'warning'},
                {'label': 'Expired', 'value': Medicine.objects.filter(expire_date__lt=today).count(), 'tone': 'danger'},
            ],
            'items': items[:10],
        }

    def _build_sales_context(self):
        today = timezone.now().date()
        month_start = today.replace(day=1)
        top_sales = (
            SaleItem.objects.values('medicine__name')
            .annotate(total_sold=Sum('quantity'), revenue=Sum('sub_total'))
            .order_by('-total_sold')[:6]
        )
        recent_sales = Sale.objects.order_by('-sale_date')[:6]
        items = [
            {
                'title': row['medicine__name'],
                'meta': f"Sold {row['total_sold']} | Rs. {float(row['revenue'] or 0):.2f}",
                'kind': 'success',
            }
            for row in top_sales
        ]
        items.extend(
            {
                'title': sale.invoice_number,
                'meta': f"{sale.sale_date:%d %b %Y %I:%M %p} | Rs. {sale.sub_total}",
                'kind': 'info',
            }
            for sale in recent_sales
        )
        return {
            'title': 'Sales details',
            'summary_cards': [
                {'label': 'Today sales', 'value': f"Rs. {float(Sale.objects.filter(sale_date__date=today).aggregate(total=Sum('sub_total'))['total'] or 0):.2f}", 'tone': 'success'},
                {'label': 'Month sales', 'value': f"Rs. {float(Sale.objects.filter(sale_date__date__gte=month_start).aggregate(total=Sum('sub_total'))['total'] or 0):.2f}", 'tone': 'success'},
                {'label': 'Invoices', 'value': Sale.objects.count(), 'tone': 'info'},
            ],
            'items': items[:10],
        }

    def _build_supplier_context(self):
        suppliers = Supplier.objects.annotate(medicine_count=Count('medicine')).order_by('company_name')[:8]
        return {
            'title': 'Supplier details',
            'summary_cards': [
                {'label': 'Suppliers', 'value': Supplier.objects.count(), 'tone': 'info'},
            ],
            'items': [
                {
                    'title': supplier.company_name,
                    'meta': f"{supplier.contact_person or 'No contact'} | {supplier.medicine_count} medicines",
                    'kind': 'info',
                }
                for supplier in suppliers
            ],
        }

    def _build_search_context(self, message):
        terms = [part for part in message.replace('?', ' ').split() if len(part) > 2]
        query = ' '.join(terms[-4:]).strip()
        medicines = Medicine.objects.select_related('generic_name', 'presentation').filter(
            Q(name__icontains=query) | Q(generic_name__name__icontains=query)
        )[:8] if query else Medicine.objects.none()
        recommender = MedicineRecommender()
        recommendations = recommender.recommend(query, n=5) if query else []
        items = [
            {
                'title': medicine.name,
                'meta': f"Rs. {medicine.selling_price} | Qty {medicine.quantity}",
                'kind': 'info',
            }
            for medicine in medicines
        ]
        items.extend(
            {
                'title': result['name'],
                'meta': f"Similarity {result['similarity']}% | Qty {result['quantity']}",
                'kind': 'success',
            }
            for result in recommendations
        )
        return {
            'title': 'Related results',
            'summary_cards': [
                {'label': 'Matches', 'value': len(medicines), 'tone': 'info'},
                {'label': 'Recommendations', 'value': len(recommendations), 'tone': 'success'},
            ],
            'items': items[:10],
        }

    def _build_context_payload(self, message):
        lowered = message.lower()
        if self._has_keyword(lowered, self.WORKFLOW_KEYWORDS):
            return self._build_workflow_context()
        if self._has_keyword(lowered, self.OVERVIEW_KEYWORDS):
            return self._build_overview_context()
        if self._has_keyword(lowered, self.STOCK_KEYWORDS):
            return self._build_stock_context()
        if self._has_keyword(lowered, self.SALES_KEYWORDS):
            return self._build_sales_context()
        if self._has_keyword(lowered, self.SUPPLIER_KEYWORDS):
            return self._build_supplier_context()
        if self._has_keyword(lowered, self.ORDER_KEYWORDS):
            return self._build_online_order_context()
        if self._has_keyword(lowered, self.RECOMMEND_KEYWORDS):
            return self._build_search_context(message)
        return self._build_search_context(message)

    def get(self, request):
        history = list(ChatMessage.objects.filter(user=request.user).order_by('-created_at')[:30])
        history.reverse()
        return Response({
            'history': ChatMessageSerializer(history, many=True).data,
            'welcome_message': (
                "Hi! I can guide your full website workflow: dashboard, medicines, inventory, "
                "excel import/export, billing, reports, online orders, OCR and recommendations. "
                "Type 'website workflow guide' or ask for 'system overview'."
            ),
            'suggestions': self._build_suggestions(),
        })

    def post(self, request):
        message = request.data.get('message', '').strip()
        if not message:
            return Response({'error': 'Empty message'}, status=400)

        # Save user message
        ChatMessage.objects.create(user=request.user, role='user', message=message)

        # Get AI response
        lowered = message.lower()
        if self._has_keyword(lowered, self.WORKFLOW_KEYWORDS):
            response_text = self._build_workflow_guide_response()
        else:
            ai = PharmacyAI(request.user)
            response_text = ai.respond(message)
        context_payload = self._build_context_payload(message)

        # Save assistant message
        ChatMessage.objects.create(user=request.user, role='assistant', message=response_text)

        return Response({
            'response': response_text,
            'message': message,
            'context': context_payload,
            'suggestions': self._build_suggestions(message),
        })

    def delete(self, request):
        ChatMessage.objects.filter(user=request.user).delete()
        return Response({'success': True})


# ─────────────────────────────────────────────
# ML RECOMMENDATION API
# ─────────────────────────────────────────────

class RecommendationAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('q', '')
        try:
            n = max(1, min(int(request.query_params.get('n', 8)), 25))
        except (TypeError, ValueError):
            return Response({'error': 'n must be an integer between 1 and 25'}, status=400)
        if not query:
            return Response([])
        recommender = MedicineRecommender()
        results = recommender.recommend(query, n=n)
        return Response(results)


# ─────────────────────────────────────────────
# OCR API
# ─────────────────────────────────────────────

class OCRPrescriptionAPI(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        qs = OCRPrescription.objects.filter(uploaded_by=request.user)
        return Response(OCRPrescriptionSerializer(qs, many=True).data)

    def post(self, request):
        image = request.FILES.get('image')
        manual_text = request.data.get('text', '')

        extracted_text = manual_text
        if image:
            extracted_text = extract_prescription_text(image) or manual_text

        # ML-based medicine extraction from text
        recommender = MedicineRecommender()
        extracted_medicines, recommendations = recommender.extract_from_prescription(extracted_text)

        prescription = OCRPrescription.objects.create(
            image=image,
            prescription_text=extracted_text,
            extracted_medicines=extracted_medicines,
            recommendations=recommendations,
            uploaded_by=request.user
        )
        return Response({
            'id': prescription.id,
            'extracted_text': extracted_text,
            'extracted_medicines': extracted_medicines,
            'recommendations': recommendations
        })
