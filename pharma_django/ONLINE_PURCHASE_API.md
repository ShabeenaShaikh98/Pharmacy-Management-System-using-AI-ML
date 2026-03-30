# Online Medicine Purchase API (Production-Oriented)

Base prefix: `/api/online/`  
Auth: Session or JWT (when `djangorestframework-simplejwt` is installed)

## JWT Endpoints
- `POST /api/auth/token/`
- `POST /api/auth/token/refresh/`

## Customer APIs
- `GET /api/online/medicines/?q=&sort=&prescription=&near_expiry=&low_stock=`
- `GET /api/online/cart/`
- `POST /api/online/cart/items/` with `{ "medicine_id": 1, "quantity": 2 }`
- `PATCH /api/online/cart/items/{item_id}/` with `{ "quantity": 3 }`
- `DELETE /api/online/cart/items/{item_id}/`
- `GET /api/online/prescriptions/`
- `POST /api/online/prescriptions/` multipart form with `image`
- `POST /api/online/checkout/`
  ```json
  {
    "customer_name": "Amit Kumar",
    "customer_phone": "9876543210",
    "delivery_address": "Salt Lake, Kolkata",
    "payment_method": "upi",
    "notes": "",
    "prescription_id": 12
  }
  ```
- `GET /api/online/orders/?status=pending`
- `GET /api/online/orders/{order_id}/`
- `GET /api/online/orders/{order_id}/invoice-pdf/`
- `GET /api/online/payments/`

## Staff/Admin APIs
- `GET /api/online/dashboard/`
- `POST /api/online/prescriptions/{prescription_id}/review/`
  ```json
  { "action": "approved", "review_note": "Clear prescription." }
  ```
- `POST /api/online/orders/{order_id}/status/`
  ```json
  { "status": "packed", "note": "Packed and ready for dispatch." }
  ```
- `POST /api/online/orders/{order_id}/assign-delivery/`
  ```json
  { "delivery_partner_id": 4, "note": "Assigned to zone-2 runner." }
  ```
- `POST /api/online/payments/{order_id}/status/`
  ```json
  { "status": "paid", "gateway": "razorpay", "reference": "pay_123", "gateway_payment_id": "pay_123" }
  ```
- `POST /api/online/payments/{order_id}/refund/`
  ```json
  { "refunded_amount": "199.00", "reference": "rfnd_123" }
  ```

## Notes
- Order timeline is maintained automatically via `OnlineOrderStatusLog`.
- Delivery assignment is available on each order (`delivery_partner` and `delivery_assigned_at`).
- Payment records now include gateway fields and refund tracking.
- Install JWT package:
  ```bash
  pip install djangorestframework-simplejwt==5.3.1
  ```
