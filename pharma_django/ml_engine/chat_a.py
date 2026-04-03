"""
Pharmacy AI Chat Assistant
Rule-based NLP + scikit-learn for intent classification
"""
import re
import datetime
from django.utils import timezone
from django.db.models import Sum, Count, Q


class PharmacyAI:
    """
    Intelligent pharmacy chat assistant using:
    - Rule-based intent detection with regex
    - Django ORM for real-time data querying
    - scikit-learn for medicine recommendations
    """

    def __init__(self, user):
        self.user = user

    def respond(self, message: str) -> str:
        """Main response dispatcher"""
        msg = message.lower().strip()

        # Route to appropriate handler
        if self._match(msg, ['out of stock', 'no stock', 'stock out', 'finished stock', 'unavailable']):
            return self._handle_out_of_stock()

        elif self._match(msg, ['low stock', 'running low', 'less stock', 'low quantity']):
            return self._handle_low_stock()

        elif self._match(msg, ['expir', 'expire', 'expiry', 'expired']):
            return self._handle_expiry()

        elif self._match(msg, ['best sell', 'top sell', 'popular medicine', 'most sold', 'highest sell']):
            return self._handle_top_selling()

        elif self._match(msg, ['inventory', 'total stock', 'how many medicine', 'stock summary', 'overview']):
            return self._handle_inventory_summary()

        elif self._match(msg, ['today sale', "today's sale", 'daily sale', 'sale today']):
            return self._handle_today_sales()

        elif self._match(msg, ['monthly sale', 'month sale', 'this month', 'monthly revenue']):
            return self._handle_monthly_sales()

        elif self._match(msg, ['total sale', 'all sale', 'total revenue', 'total earning']):
            return self._handle_total_sales()

        elif self._match(msg, ['supplier', 'vendor', 'company']):
            return self._handle_supplier_query(msg)

        elif self._match(msg, ['recommend', 'suggest', 'alternative', 'similar', 'substitute']):
            return self._handle_recommendation(msg)

        elif self._match(msg, ['price', 'cost', 'how much', 'rate']):
            return self._handle_price_query(msg)

        elif self._match(msg, ['search', 'find', 'look for', 'show me']):
            return self._handle_search(msg)

        elif self._match(msg, ['help', 'what can you', 'command', 'feature', 'guide']):
            return self._handle_help()

        elif self._match(msg, ['hello', 'hi ', 'hey', 'good morning', 'good afternoon', 'howdy']):
            return self._handle_greeting()

        else:
            # Fallback: try a generic medicine search
            return self._handle_generic_search(msg)

    # ─────────────────────────────────────────
    # HANDLERS
    # ─────────────────────────────────────────

    def _handle_out_of_stock(self):
        from pharmacy_app.models import Medicine
        qs = Medicine.objects.filter(quantity=0).select_related('generic_name', 'presentation')
        if not qs.exists():
            return "✅ Great news! All medicines are currently in stock. No shortages detected."

        lines = [f"🔴 **Out of Stock — {qs.count()} Medicines**\n"]
        for m in qs[:15]:
            gen = m.generic_name.name if m.generic_name else "—"
            pres = m.presentation.name if m.presentation else "—"
            lines.append(f"• **{m.name}** ({gen}, {pres})")
        if qs.count() > 15:
            lines.append(f"_...and {qs.count()-15} more. Check Inventory for full list._")
        lines.append("\n💡 **Tip:** Go to **Inventory → Add Purchase** to restock.")
        return "\n".join(lines)

    def _handle_low_stock(self):
        from pharmacy_app.models import Medicine
        qs = Medicine.objects.filter(quantity__gt=0, quantity__lt=20).order_by('quantity')
        if not qs.exists():
            return "✅ No medicines are running critically low right now."

        lines = [f"🟡 **Low Stock Warning — {qs.count()} Medicines**\n"]
        for m in qs[:15]:
            gen = m.generic_name.name if m.generic_name else "—"
            days_left = "N/A"
            if m.expire_date:
                d = (m.expire_date - datetime.date.today()).days
                days_left = f"{d}d to expire"
            lines.append(f"• **{m.name}** ({gen}) — {m.quantity} units left | {days_left}")
        lines.append("\n⚠️ Consider restocking these medicines soon.")
        return "\n".join(lines)

    def _handle_expiry(self):
        from pharmacy_app.models import Medicine
        today = datetime.date.today()
        soon = today + datetime.timedelta(days=90)

        expired = Medicine.objects.filter(expire_date__lt=today)
        expiring_30 = Medicine.objects.filter(expire_date__gte=today, expire_date__lte=today + datetime.timedelta(days=30))
        expiring_90 = Medicine.objects.filter(expire_date__gt=today + datetime.timedelta(days=30), expire_date__lte=soon)

        lines = []
        if expired.exists():
            lines.append(f"🔴 **Already Expired — {expired.count()} medicines:**")
            for m in expired[:8]:
                lines.append(f"  • {m.name} — expired {m.expire_date.strftime('%d %b %Y')}")

        if expiring_30.exists():
            lines.append(f"\n🟠 **Expiring in 30 days — {expiring_30.count()} medicines:**")
            for m in expiring_30[:8]:
                d = (m.expire_date - today).days
                lines.append(f"  • {m.name} — {d} days left ({m.expire_date.strftime('%d %b %Y')})")

        if expiring_90.exists():
            lines.append(f"\n🟡 **Expiring in 31–90 days — {expiring_90.count()} medicines:**")
            for m in expiring_90[:5]:
                lines.append(f"  • {m.name} — expires {m.expire_date.strftime('%d %b %Y')}")

        if not lines:
            return "✅ No expired or soon-to-expire medicines found. Inventory looks healthy!"

        lines.append("\n💡 Navigate to **Inventory** to manage expiry dates.")
        return "\n".join(lines)

    def _handle_top_selling(self):
        from pharmacy_app.models import SaleItem
        from django.db.models import Sum, Count
        top = (
            SaleItem.objects
            .values('medicine__name', 'medicine__id')
            .annotate(total_sold=Sum('quantity'), revenue=Sum('sub_total'))
            .order_by('-total_sold')[:10]
        )
        if not top:
            return "📊 No sales data available yet. Start making sales to see analytics!"

        lines = ["📊 **Top 10 Best-Selling Medicines**\n"]
        for i, item in enumerate(top, 1):
            lines.append(
                f"{i}. **{item['medicine__name']}** — "
                f"{item['total_sold']} units sold | ₹{float(item['revenue'] or 0):.0f} revenue"
            )
        return "\n".join(lines)

    def _handle_inventory_summary(self):
        from pharmacy_app.models import Medicine
        from django.db.models import Sum, Avg
        today = datetime.date.today()
        stats = Medicine.objects.aggregate(
            total=Count('id'),
            total_qty=Sum('quantity'),
            avg_price=Avg('selling_price')
        )
        out = Medicine.objects.filter(quantity=0).count()
        low = Medicine.objects.filter(quantity__gt=0, quantity__lt=20).count()
        expired = Medicine.objects.filter(expire_date__lt=today).count()
        expiring = Medicine.objects.filter(
            expire_date__gte=today,
            expire_date__lte=today + datetime.timedelta(days=30)
        ).count()

        return f"""📦 **Pharmacy Inventory Summary**

📌 **Stock Overview:**
• Total medicine types: **{stats['total'] or 0}**
• Total units in stock: **{int(stats['total_qty'] or 0):,}**
• Average selling price: **₹{float(stats['avg_price'] or 0):.2f}**

🚦 **Stock Health:**
• ✅ Out of stock: **{out}** medicines
• 🟡 Low stock (<20 units): **{low}** medicines
• 🔴 Expired: **{expired}** medicines
• 🟠 Expiring in 30 days: **{expiring}** medicines

📎 Use _'out of stock'_, _'expiry alert'_, or _'low stock'_ for detailed lists."""

    def _handle_today_sales(self):
        from pharmacy_app.models import Sale, SaleItem
        today = datetime.date.today()
        sales = Sale.objects.filter(sale_date__date=today)
        agg = sales.aggregate(revenue=Sum('sub_total'), count=Count('id'))
        revenue = float(agg['revenue'] or 0)
        count = agg['count'] or 0

        top = (
            SaleItem.objects.filter(sale__sale_date__date=today)
            .values('medicine__name')
            .annotate(qty=Sum('quantity'))
            .order_by('-qty')[:3]
        )
        lines = [f"💵 **Today's Sales — {today.strftime('%d %b %Y')}**\n",
                 f"• Transactions: **{count}**",
                 f"• Total Revenue: **₹{revenue:,.2f}**"]
        if top:
            lines.append("\n🔥 **Top Items Today:**")
            for t in top:
                lines.append(f"  • {t['medicine__name']} — {t['qty']} units")
        return "\n".join(lines)

    def _handle_monthly_sales(self):
        from pharmacy_app.models import Sale
        today = datetime.date.today()
        month_start = today.replace(day=1)
        agg = Sale.objects.filter(sale_date__date__gte=month_start).aggregate(
            revenue=Sum('sub_total'), count=Count('id')
        )
        return (f"📅 **Monthly Sales — {today.strftime('%B %Y')}**\n\n"
                f"• Transactions: **{agg['count'] or 0}**\n"
                f"• Total Revenue: **₹{float(agg['revenue'] or 0):,.2f}**")

    def _handle_total_sales(self):
        from pharmacy_app.models import Sale
        agg = Sale.objects.aggregate(revenue=Sum('sub_total'), count=Count('id'))
        return (f"📊 **All-Time Sales Summary**\n\n"
                f"• Total Transactions: **{agg['count'] or 0}**\n"
                f"• Total Revenue: **₹{float(agg['revenue'] or 0):,.2f}**")

    def _handle_supplier_query(self, msg):
        from pharmacy_app.models import Supplier
        qs = Supplier.objects.all()
        if not qs.exists():
            return "No suppliers found in the system."
        lines = [f"🏭 **Registered Suppliers — {qs.count()} total**\n"]
        for s in qs:
            lines.append(f"• **{s.company_name}** | 📞 {s.phone or 'N/A'} | ✉️ {s.email or 'N/A'}")
        return "\n".join(lines)

    def _handle_recommendation(self, msg):
        # Strip intent words to get the medicine/symptom query
        clean = re.sub(
            r'\b(recommend|suggest|alternative|similar|substitute|for|me|a|an|the|medicine|drug|give)\b',
            '', msg, flags=re.IGNORECASE
        ).strip()
        if not clean:
            return "Please tell me what medicine or symptom you need a recommendation for.\nExample: _'recommend fever medicine'_ or _'alternative for paracetamol'_"

        from ml_engine.recommender import MedicineRecommender
        rec = MedicineRecommender()
        results = rec.recommend(clean, n=5)
        if not results:
            return f"I couldn't find recommendations for **'{clean}'**. Try a different medicine name or symptom."

        lines = [f"💊 **Recommendations for '{clean}':**\n"]
        for r in results:
            stock_icon = "✅" if r['quantity'] > 20 else "🟡" if r['quantity'] > 0 else "🔴"
            lines.append(
                f"{stock_icon} **{r['name']}** ({r.get('generic_name','')}, {r.get('presentation','')})\n"
                f"   ₹{r['selling_price']} | Stock: {r['quantity']} units | Match: {r['similarity']}%"
            )
        return "\n".join(lines)

    def _handle_price_query(self, msg):
        from pharmacy_app.models import Medicine
        # Extract medicine name
        clean = re.sub(r'\b(price|cost|how much|rate|of|for|is|the)\b', '', msg, flags=re.IGNORECASE).strip()
        if not clean:
            return "Please specify the medicine name.\nExample: _'price of Crocin'_"

        qs = Medicine.objects.filter(name__icontains=clean)[:8]
        if not qs.exists():
            return f"No medicine found matching **'{clean}'**. Please check the name."

        lines = [f"💰 **Price Information for '{clean}':**\n"]
        for m in qs:
            stock = f"{m.quantity} units" if m.quantity > 0 else "**OUT OF STOCK**"
            lines.append(f"• **{m.name}** — ₹{m.selling_price} | Stock: {stock}")
        return "\n".join(lines)

    def _handle_search(self, msg):
        clean = re.sub(r'\b(search|find|look for|show me|get|fetch)\b', '', msg, flags=re.IGNORECASE).strip()
        return self._handle_generic_search(clean)

    def _handle_generic_search(self, msg):
        from pharmacy_app.models import Medicine
        if len(msg) < 2:
            return self._handle_help()

        qs = Medicine.objects.filter(
            Q(name__icontains=msg) | Q(generic_name__name__icontains=msg)
        ).select_related('generic_name', 'presentation')[:8]

        if not qs.exists():
            return (f"🔍 No results found for **'{msg}'**.\n\n"
                    "Try:\n• A different medicine name or generic\n"
                    "• Commands like 'out of stock', 'expiry', 'recommend fever medicine'\n"
                    "• Type **help** for all commands")

        lines = [f"🔍 **Search Results for '{msg}':**\n"]
        for m in qs:
            gen = m.generic_name.name if m.generic_name else "—"
            pres = m.presentation.name if m.presentation else "—"
            stock_icon = "✅" if m.quantity > 20 else "🟡" if m.quantity > 0 else "🔴"
            lines.append(f"{stock_icon} **{m.name}** ({gen}, {pres}) — ₹{m.selling_price} | {m.quantity} units")
        return "\n".join(lines)

    def _handle_greeting(self):
        import random
        greetings = [
            f"👋 Hello! I'm **PharmaBot**, your AI pharmacy assistant.\nHow can I help you today? Type **help** to see what I can do.",
            f"🌟 Hi there! Ready to help you manage the pharmacy.\nAsk me about stock, expiry, sales, or recommendations!",
            f"👋 Hey! I'm your pharmacy AI assistant.\nI can help with stock alerts, medicine search, sales reports, and more. Type **help** to get started!",
        ]
        import random
        return random.choice(greetings)

    def _handle_help(self):
        return """🤖 **PharmaBot — AI Pharmacy Assistant**

**📦 Stock & Inventory:**
• `out of stock` — Show medicines with zero stock
• `low stock` — Show medicines below 20 units
• `inventory summary` — Full stock overview

**⏰ Expiry Management:**
• `expiry alert` — Show expired & soon-to-expire medicines
• `expired medicines` — Only show already expired stock

**💊 Medicine Search:**
• `search crocin` — Find a specific medicine
• `price of paracetamol` — Get pricing info
• `recommend fever medicine` — ML-based recommendations
• `alternative for ibuprofen` — Suggest substitutes

**📊 Sales & Revenue:**
• `today's sales` — Today's revenue & transactions
• `monthly sales` — This month's performance
• `total sales` — All-time sales summary
• `top selling medicines` — Best-selling analytics

**🏭 Supplier Info:**
• `show suppliers` — List all suppliers

**Other:**
• `help` — Show this guide

_Ask me anything naturally — I understand plain English!_ 🌟"""

    # ─────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────

    def _match(self, text: str, keywords: list) -> bool:
        return any(kw in text for kw in keywords)
