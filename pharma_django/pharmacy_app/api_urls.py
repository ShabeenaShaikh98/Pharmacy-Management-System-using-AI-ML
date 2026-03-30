from django.urls import path
from .api_views import (
    GenericNameListCreateAPI, GenericNameDetailAPI,
    PresentationListCreateAPI, PresentationDetailAPI,
    SupplierListCreateAPI, SupplierDetailAPI,
    MedicineListCreateAPI, MedicineDetailAPI,
    PurchaseListCreateAPI, PurchaseDetailAPI,
    SaleListCreateAPI, SaleDetailAPI,
    DashboardStatsAPI, SalesSummaryAPI,
    MedicinePerformanceAPI, StockAlertAPI,
    InventoryReportAPI, ChatAPI,
    RecommendationAPI, OCRPrescriptionAPI,
)
from .online_api_views import (
    OnlineAssignDeliveryAPI,
    OnlineCartAPI,
    OnlineCartItemDetailAPI,
    OnlineCartItemsAPI,
    OnlineCheckoutAPI,
    OnlineDashboardAPI,
    OnlineInvoicePDFAPI,
    OnlineMedicineCatalogAPI,
    OnlineOrderDetailAPI,
    OnlineOrderStatusAPI,
    OnlineOrdersAPI,
    OnlinePaymentRefundAPI,
    OnlinePaymentsAPI,
    OnlinePaymentStatusAPI,
    OnlinePrescriptionAPI,
    OnlinePrescriptionReviewAPI,
)

urlpatterns = [
    # Generic Names
    path('generics/', GenericNameListCreateAPI.as_view(), name='api-generics'),
    path('generics/<int:pk>/', GenericNameDetailAPI.as_view(), name='api-generic-detail'),

    # Presentations
    path('presentations/', PresentationListCreateAPI.as_view(), name='api-presentations'),
    path('presentations/<int:pk>/', PresentationDetailAPI.as_view(), name='api-presentation-detail'),

    # Suppliers
    path('suppliers/', SupplierListCreateAPI.as_view(), name='api-suppliers'),
    path('suppliers/<int:pk>/', SupplierDetailAPI.as_view(), name='api-supplier-detail'),

    # Medicines
    path('medicines/', MedicineListCreateAPI.as_view(), name='api-medicines'),
    path('medicines/<int:pk>/', MedicineDetailAPI.as_view(), name='api-medicine-detail'),

    # Purchases
    path('purchases/', PurchaseListCreateAPI.as_view(), name='api-purchases'),
    path('purchases/<int:pk>/', PurchaseDetailAPI.as_view(), name='api-purchase-detail'),

    # Sales
    path('sales/', SaleListCreateAPI.as_view(), name='api-sales'),
    path('sales/<int:pk>/', SaleDetailAPI.as_view(), name='api-sale-detail'),

    # Analytics
    path('stats/', DashboardStatsAPI.as_view(), name='api-stats'),
    path('reports/sales-summary/', SalesSummaryAPI.as_view(), name='api-sales-summary'),
    path('reports/medicine-performance/', MedicinePerformanceAPI.as_view(), name='api-med-perf'),
    path('reports/stock-alerts/', StockAlertAPI.as_view(), name='api-stock-alerts'),
    path('reports/inventory/', InventoryReportAPI.as_view(), name='api-inventory'),

    # AI Chat
    path('chat/', ChatAPI.as_view(), name='api-chat'),

    # ML Recommendation
    path('recommend/', RecommendationAPI.as_view(), name='api-recommend'),

    # OCR
    path('ocr/', OCRPrescriptionAPI.as_view(), name='api-ocr'),

    # Online Purchase APIs
    path('online/dashboard/', OnlineDashboardAPI.as_view(), name='api-online-dashboard'),
    path('online/medicines/', OnlineMedicineCatalogAPI.as_view(), name='api-online-medicines'),
    path('online/cart/', OnlineCartAPI.as_view(), name='api-online-cart'),
    path('online/cart/items/', OnlineCartItemsAPI.as_view(), name='api-online-cart-items'),
    path('online/cart/items/<int:item_id>/', OnlineCartItemDetailAPI.as_view(), name='api-online-cart-item-detail'),
    path('online/prescriptions/', OnlinePrescriptionAPI.as_view(), name='api-online-prescriptions'),
    path('online/prescriptions/<int:prescription_id>/review/', OnlinePrescriptionReviewAPI.as_view(), name='api-online-prescription-review'),
    path('online/checkout/', OnlineCheckoutAPI.as_view(), name='api-online-checkout'),
    path('online/orders/', OnlineOrdersAPI.as_view(), name='api-online-orders'),
    path('online/orders/<int:order_id>/', OnlineOrderDetailAPI.as_view(), name='api-online-order-detail'),
    path('online/orders/<int:order_id>/status/', OnlineOrderStatusAPI.as_view(), name='api-online-order-status'),
    path('online/orders/<int:order_id>/assign-delivery/', OnlineAssignDeliveryAPI.as_view(), name='api-online-order-assign-delivery'),
    path('online/orders/<int:order_id>/invoice-pdf/', OnlineInvoicePDFAPI.as_view(), name='api-online-order-invoice-pdf'),
    path('online/payments/', OnlinePaymentsAPI.as_view(), name='api-online-payments'),
    path('online/payments/<int:order_id>/status/', OnlinePaymentStatusAPI.as_view(), name='api-online-payment-status'),
    path('online/payments/<int:order_id>/refund/', OnlinePaymentRefundAPI.as_view(), name='api-online-payment-refund'),
]

try:
    from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
    urlpatterns += [
        path('auth/token/', TokenObtainPairView.as_view(), name='api-token-obtain'),
        path('auth/token/refresh/', TokenRefreshView.as_view(), name='api-token-refresh'),
    ]
except ImportError:
    pass
