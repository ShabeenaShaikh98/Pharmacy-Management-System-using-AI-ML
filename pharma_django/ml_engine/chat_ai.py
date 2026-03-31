"""
╔══════════════════════════════════════════════════════════════════╗
║          Pharmacy AI Chat Assistant — PharmaBot                 ║
║  Languages: English | Hindi | Marathi | Roman Hindi | Roman Marathi ║
║  Engine   : Rule-based NLP + Django ORM + scikit-learn          ║
╚══════════════════════════════════════════════════════════════════╝

Usage:
    ai = PharmacyAI(request.user)
    response = ai.respond(user_message)   # auto-detects language

Supported input modes
─────────────────────
  en  → "show out of stock medicines"
  hi  → "स्टॉक खत्म हो गया दवाएं दिखाओ"
  mr  → "साठा नाही असलेली औषधे दाखवा"
  rhi → "stock khatam dawai dikhao"      (Roman / Hinglish)
  rmr → "satha nahi aushadhe dakahva"    (Roman Marathi)
"""

import re
import random
import datetime
from difflib import SequenceMatcher, get_close_matches
from django.db.models import Sum, Count, Q, Avg


# ══════════════════════════════════════════════════════════════════
#  MODULE-LEVEL KEYWORD POOLS  (used only for language detection)
# ══════════════════════════════════════════════════════════════════

_HINDI_DEVA = [
    'दवा', 'दवाई', 'स्टॉक', 'बिक्री', 'मदद', 'सूची', 'महीना',
    'कीमत', 'समाप्त', 'खत्म', 'नहीं', 'क्या', 'बताओ', 'दिखाओ',
    'कितना', 'सबसे', 'सप्लायर', 'सिफारिश', 'विकल्प', 'कुल',
    'नमस्ते', 'ढूंढो', 'खोजो', 'मासिक', 'राजस्व', 'एक्सपायर',
]

_MARATHI_DEVA = [
    'औषध', 'साठा', 'विक्री', 'मदत', 'यादी', 'महिना',
    'किंमत', 'संपले', 'नाही', 'आहे', 'दाखवा', 'सांगा',
    'किती', 'पुरवठादार', 'शिफारस', 'पर्याय', 'एकूण',
    'नमस्कार', 'हॅलो', 'शोधा', 'मिळवा', 'कालबाह्य',
    'महसूल', 'व्यवहार', 'मासिक', 'औषधे',
]

_ROMAN_HINDI = [
    'namaste', 'namaskar', 'kaise ho', 'kya hal',
    'stock khatam', 'stock nahi', 'stock kam', 'khatam ho gaya',
    'dawa nahi', 'uplabdh nahi', 'stock khali', 'kam stock',
    'thoda bacha', 'stock kum', 'purani dawa', 'tarikh nikal',
    'aaj ki bikri', 'aaj ki sale', 'aaj ka revenue',
    'masik bikri', 'mahine ki bikri', 'is mahine', 'monthly sale',
    'kul bikri', 'total bikri', 'sabhi sale', 'total kamai',
    'dawa', 'dawai', 'dava', 'davai',
    'sabse jyada bikne', 'top dawa', 'best seller', 'popular dawa',
    'supplier dikhao', 'aapurtikarta', 'vendor',
    'sifarish', 'sujhav', 'vikalp', 'doosri dawa', 'jaisi dawa',
    'recommend karo', 'suggest karo', 'alternative batao',
    'kimat', 'dam', 'kitna paisa', 'rate kya', 'bhav', 'mulya',
    'khojo', 'dhundho', 'dikhao', 'batao', 'search karo',
    'madad', 'help karo', 'kya kar sakte',
]

_ROMAN_MARATHI = [
    'namaskar', 'kasa ahes', 'kay hal',
    'satha nahi', 'stock sampla', 'satha sampla', 'khali satha',
    'kami satha', 'stock kami', 'thode urle',
    'kalbahya', 'expire jhale', 'mudat sampli', 'tarikh sampli',
    'aajchi vikri', 'aajchi sale', 'aajche utpanna',
    'masik vikri', 'ya mahinyat', 'mahinyachi vikri',
    'ekun vikri', 'sarva vikri', 'total vikri', 'ekun kamai',
    'aushadh', 'aushadhe', 'oushadh',
    'satha yadi', 'kiti aushadhe', 'satha saran',
    'sarvadik vikli', 'top aushadh', 'lokpriya aushadh',
    'purvthadar', 'puravthadar',
    'shifaras', 'suchava', 'paryay', 'dusre aushadh',
    'recommend kara', 'suggest kara',
    'kimat kiti', 'dar kiti', 'bhav kiti',
    'shodha', 'dakahva', 'milva', 'search kara',
    'madat', 'help kara', 'kay karu shakat',
]


# ══════════════════════════════════════════════════════════════════
#  MAIN CLASS
# ══════════════════════════════════════════════════════════════════

class PharmacyAI:
    """
    Intelligent pharmacy chat assistant with 5-language support.

    Language codes
    ──────────────
    'en'  → English
    'hi'  → Hindi (Devanagari)
    'mr'  → Marathi (Devanagari)
    'rhi' → Roman Hindi / Hinglish
    'rmr' → Roman Marathi
    """

    # ──────────────────────────────────────────────────────────────
    #  INTENT KEYWORD TABLES  (all 5 languages per intent)
    # ──────────────────────────────────────────────────────────────

    _KW_OUT_OF_STOCK = [
        # EN
        'out of stock', 'no stock', 'stock out', 'finished stock',
        'unavailable', 'zero stock', 'empty stock',
        # HI deva
        'स्टॉक नहीं', 'खत्म हो गया', 'स्टॉक खत्म', 'उपलब्ध नहीं',
        # MR deva
        'साठा नाही', 'स्टॉक संपले', 'उपलब्ध नाही', 'साठा संपला',
        # Roman Hindi
        'stock khatam', 'stock nahi', 'khatam ho gaya', 'dawa nahi',
        'stock khali', 'uplabdh nahi',
        # Roman Marathi
        'satha nahi', 'stock sampla', 'satha sampla', 'khali satha',
    ]

    _KW_LOW_STOCK = [
        # EN
        'low stock', 'running low', 'less stock', 'low quantity',
        'nearly out', 'almost empty',
        # HI deva
        'कम स्टॉक', 'कम मात्रा', 'थोड़ा बचा', 'स्टॉक कम',
        # MR deva
        'कमी साठा', 'कमी स्टॉक', 'थोडे उरले', 'साठा कमी',
        # Roman Hindi
        'kam stock', 'thoda bacha', 'stock kam', 'kam matra', 'stock kum',
        # Roman Marathi
        'kami satha', 'stock kami', 'thode urle',
    ]

    _KW_EXPIRY = [
        # EN
        'expir', 'expire', 'expiry', 'expired', 'expiration',
        'near expiry', 'about to expire',
        # HI deva
        'समाप्त', 'एक्सपायर', 'एक्सपायरी', 'दवा पुरानी', 'तारीख निकल',
        # MR deva
        'कालबाह्य', 'एक्स्पायर', 'मुदत संपले', 'तारीख संपली',
        # Roman Hindi
        'expire', 'expiry', 'purani dawa', 'tarikh nikal', 'expire ho gaya',
        # Roman Marathi
        'kalbahya', 'expire jhale', 'mudat sampli', 'tarikh sampli',
    ]

    _KW_TOP_SELLING = [
        # EN
        'best sell', 'top sell', 'popular medicine', 'most sold',
        'highest sell', 'top medicine', 'best medicine',
        # HI deva
        'सबसे ज्यादा बिकने', 'टॉप दवा', 'सबसे लोकप्रिय',
        'बेस्ट सेलर', 'ज्यादा बिकी',
        # MR deva
        'सर्वाधिक विकली', 'टॉप औषध', 'सर्वात लोकप्रिय', 'बेस्ट सेलर',
        # Roman Hindi
        'sabse jyada bikne', 'top dawa', 'best seller', 'popular dawa',
        'jyada biki', 'sabse bikne wali',
        # Roman Marathi
        'sarvadik vikli', 'top aushadh', 'lokpriya aushadh',
    ]

    _KW_INVENTORY = [
        # EN
        'inventory', 'total stock', 'how many medicine', 'stock summary',
        'overview', 'stock overview', 'medicine list',
        # HI deva
        'इन्वेंटरी', 'कुल स्टॉक', 'कितनी दवाएं', 'स्टॉक सारांश', 'दवा सूची',
        # MR deva
        'इन्व्हेंटरी', 'एकूण साठा', 'किती औषधे', 'साठा सारांश', 'औषध यादी',
        # Roman Hindi
        'stock list', 'kitni dawai', 'dawa list', 'sara stock', 'poora stock',
        'inventory dekho',
        # Roman Marathi
        'satha yadi', 'kiti aushadhe', 'inventory bagh',
    ]

    _KW_TODAY_SALES = [
        # EN
        'today sale', "today's sale", 'daily sale', 'sale today',
        'today revenue', 'todays sales',
        # HI deva
        'आज की बिक्री', 'आज की सेल', 'दैनिक बिक्री', 'आज का revenue',
        # MR deva
        'आजची विक्री', 'आजची सेल', 'दैनिक विक्री', 'आजचे उत्पन्न',
        # Roman Hindi
        'aaj ki bikri', 'aaj ki sale', 'aaj ka revenue',
        'daily bikri', 'aaj kitna hua',
        # Roman Marathi
        'aajchi vikri', 'aajchi sale', 'aajche utpanna', 'aaj kiti vikri',
    ]

    _KW_MONTHLY_SALES = [
        # EN
        'monthly sale', 'month sale', 'this month', 'monthly revenue',
        'month revenue', 'current month',
        # HI deva
        'मासिक बिक्री', 'इस महीने', 'महीने की बिक्री', 'मंथली सेल',
        # MR deva
        'मासिक विक्री', 'या महिन्यात', 'महिन्याची विक्री', 'मंथली सेल',
        # Roman Hindi
        'masik bikri', 'is mahine', 'mahine ki bikri', 'monthly bikri',
        'mahine ka revenue',
        # Roman Marathi
        'masik vikri', 'ya mahinyat', 'mahinyachi vikri', 'monthly vikri',
    ]

    _KW_TOTAL_SALES = [
        # EN
        'total sale', 'all sale', 'total revenue', 'total earning',
        'all time sale', 'overall sale',
        # HI deva
        'कुल बिक्री', 'सभी बिक्री', 'कुल कमाई', 'टोटल सेल',
        # MR deva
        'एकूण विक्री', 'सर्व विक्री', 'एकूण कमाई', 'टोटल सेल',
        # Roman Hindi
        'kul bikri', 'sabhi sale', 'kul kamai', 'total bikri', 'poori bikri',
        # Roman Marathi
        'ekun vikri', 'sarva vikri', 'ekun kamai', 'total vikri',
    ]

    _KW_OVERVIEW = [
        'overview', 'summary', 'dashboard', 'status', 'system status',
        'business summary', 'pharmacy summary', 'complete status', 'all details',
        'full detail', 'full details', 'everything',
        'सारांश', 'डैशबोर्ड', 'स्थिति', 'पूरी जानकारी', 'सब कुछ',
        'सारांश', 'डॅशबोर्ड', 'स्थिती', 'संपूर्ण माहिती', 'सगळे',
        'poora summary', 'system overview', 'dashboard status', 'sab kuch',
        'saransh', 'dashboard chi mahiti', 'sampurna mahiti',
    ]

    _KW_SUPPLIER = [
        # EN
        'supplier', 'vendor', 'company list', 'show supplier', 'supplier list',
        # HI deva
        'सप्लायर', 'आपूर्तिकर्ता', 'कंपनी', 'विक्रेता',
        # MR deva
        'पुरवठादार', 'सप्लायर', 'कंपनी', 'विक्रेता',
        # Roman Hindi
        'supplier dikhao', 'aapurtikarta', 'company dikhao', 'vendor list',
        # Roman Marathi
        'purvthadar', 'puravthadar', 'supplier dakahva',
    ]

    _KW_RECOMMEND = [
        # EN
        'recommend', 'suggest', 'alternative', 'similar', 'substitute',
        'what medicine for', 'medicine for',
        # HI deva
        'सिफारिश', 'सुझाव', 'विकल्प', 'दूसरी दवा', 'जैसी दवा',
        # MR deva
        'शिफारस', 'सुचवा', 'पर्याय', 'दुसरे औषध', 'सारखे औषध',
        # Roman Hindi
        'sifarish', 'sujhav', 'vikalp', 'doosri dawa', 'jaisi dawa',
        'recommend karo', 'suggest karo', 'substitute batao',
        'koi aur dawa', 'alternative batao',
        # Roman Marathi
        'shifaras', 'suchava', 'paryay', 'dusre aushadh',
        'recommend kara', 'suggest kara', 'similar aushadh',
    ]

    _KW_PRICE = [
        # EN
        'price', 'cost', 'how much', 'rate', 'pricing',
        # HI deva
        'कीमत', 'दाम', 'कितना', 'मूल्य', 'रेट', 'भाव',
        # MR deva
        'किंमत', 'दर', 'किती', 'मूल्य', 'रेट', 'भाव',
        # Roman Hindi
        'kimat', 'dam', 'kitna paisa', 'rate kya', 'bhav', 'mulya',
        # Roman Marathi
        'kimat kiti', 'dar kiti', 'bhav kiti',
    ]

    _KW_SEARCH = [
        # EN
        'search', 'find', 'look for', 'show me', 'get medicine',
        # HI deva
        'खोजो', 'ढूंढो', 'खोजें', 'दिखाओ', 'बताओ', 'ढूंढें',
        # MR deva
        'शोधा', 'दाखवा', 'मिळवा', 'शोधण्यासाठी',
        # Roman Hindi
        'khojo', 'dhundho', 'dikhao', 'batao', 'search karo', 'dhundo',
        # Roman Marathi
        'shodha', 'dakahva', 'milva', 'search kara',
    ]

    _KW_HELP = [
        # EN
        'help', 'what can you', 'command', 'feature', 'guide', 'how to use',
        # HI deva
        'मदद', 'सहायता', 'क्या कर सकते', 'निर्देश', 'गाइड',
        # MR deva
        'मदत', 'सहाय्य', 'काय करू शकता', 'निर्देश', 'गाइड',
        # Roman Hindi
        'madad', 'help karo', 'kya kar sakte', 'guide', 'commands',
        # Roman Marathi
        'madat', 'help kara', 'kay karu shakat',
    ]

    _KW_ORDER = [
        'order', 'orders', 'online order', 'checkout', 'cart', 'track order', 'order status',
        'delivery', 'pending', 'packed', 'out for delivery', 'delivered',
        'order karo', 'order karna', 'cart me', 'checkout karo',
        'ऑनलाइन ऑर्डर', 'ऑर्डर स्टेटस', 'डिलीवरी',
    ]

    _KW_AUTOSUGGEST = [
        'suggest medicine', 'auto suggest', 'typeahead', 'starts with', 'similar name',
        'paracitamol', 'crocine', 'doloo', 'spelling',
    ]

    _KW_SAFETY = [
        'prescription', 'rx', 'restricted', 'safe', 'dosage', 'interaction',
        'contraindication', 'side effect', 'doctor',
    ]

    _KW_BILLING = [
        'billing help', 'invoice help', 'gst help', 'bill kaise', 'invoice kaise',
    ]

    _KW_REPORTS = [
        'report', 'dashboard explain', 'insights', 'revenue trend', 'top medicines',
    ]

    _KW_GREETING = [
        # EN
        'hello', 'hi ', 'hey', 'good morning', 'good afternoon',
        'good evening', 'howdy', 'greetings',
        # HI deva
        'नमस्ते', 'नमस्कार', 'हेलो', 'हाय', 'प्रणाम', 'सुप्रभात',
        # MR deva
        'नमस्कार', 'नमस्ते', 'हॅलो', 'हाय', 'सुप्रभात',
        # Roman Hindi
        'namaste', 'namaskar', 'kaise ho', 'kya hal', 'hello yaar', 'helo',
        # Roman Marathi
        'kasa ahes', 'kay hal',
    ]

    # ──────────────────────────────────────────────────────────────
    #  CONSTRUCTOR
    # ──────────────────────────────────────────────────────────────

    def __init__(self, user):
        self.user = user
        self.lang = 'en'

    # ──────────────────────────────────────────────────────────────
    #  LANGUAGE DETECTION
    # ──────────────────────────────────────────────────────────────

    def _detect_language(self, msg: str) -> str:
        """
        Detect one of 5 language codes from the raw message.
        Priority: Devanagari script → Roman Marathi → Roman Hindi → English
        """
        # 1. Devanagari script detected
        deva_chars = [ch for ch in msg if '\u0900' <= ch <= '\u097F']
        if len(deva_chars) > 2:
            marathi_chars = ['ळ', 'ॲ', 'ऑ', 'ण']
            if any(ch in msg for ch in marathi_chars):
                return 'mr'
            for word in _MARATHI_DEVA:
                if word in msg:
                    return 'mr'
            return 'hi'

        # 2. Short Devanagari (single character or emoji combo)
        for word in _MARATHI_DEVA:
            if word in msg:
                return 'mr'
        for word in _HINDI_DEVA:
            if word in msg:
                return 'hi'

        # 3. Roman script scoring — more specific wins
        m = msg.lower()
        mr_score = sum(1 for kw in _ROMAN_MARATHI if kw in m)
        hi_score = sum(1 for kw in _ROMAN_HINDI  if kw in m)

        if mr_score > 0 and mr_score >= hi_score:
            return 'rmr'
        if hi_score > 0:
            return 'rhi'

        return 'en'

    # ──────────────────────────────────────────────────────────────
    #  TRANSLATION HELPER
    # ──────────────────────────────────────────────────────────────

    def _t(self, en: str, hi: str = None, mr: str = None,
           rhi: str = None, rmr: str = None) -> str:
        """
        Return the text in the currently active language.
        Falls back gracefully:
            rhi → hi → en
            rmr → mr → en
        """
        if self.lang == 'hi':
            return hi  or en
        if self.lang == 'mr':
            return mr  or en
        if self.lang == 'rhi':
            return rhi or hi or en
        if self.lang == 'rmr':
            return rmr or mr or en
        return en

    # ──────────────────────────────────────────────────────────────
    #  MAIN DISPATCHER
    # ──────────────────────────────────────────────────────────────

    def respond(self, message: str) -> str:
        """Route the message to the correct handler."""
        raw = message.strip()
        msg = raw.lower()
        self.lang = self._detect_language(raw)

        if   self._match(msg, self._KW_ORDER):          return self._handle_online_order_support(msg)
        elif self._match(msg, self._KW_AUTOSUGGEST):    return self._handle_autosuggest(msg)
        elif self._match(msg, self._KW_SAFETY):         return self._handle_safety_help()
        elif self._match(msg, self._KW_BILLING):        return self._handle_billing_help()
        elif self._match(msg, self._KW_REPORTS):        return self._handle_overview_summary()
        elif self._match(msg, self._KW_OUT_OF_STOCK):   return self._handle_out_of_stock()
        elif self._match(msg, self._KW_LOW_STOCK):       return self._handle_low_stock()
        elif self._match(msg, self._KW_EXPIRY):          return self._handle_expiry()
        elif self._match(msg, self._KW_TOP_SELLING):     return self._handle_top_selling()
        elif self._match(msg, self._KW_OVERVIEW):        return self._handle_overview_summary()
        elif self._match(msg, self._KW_INVENTORY):       return self._handle_inventory_summary()
        elif self._match(msg, self._KW_TODAY_SALES):     return self._handle_today_sales()
        elif self._match(msg, self._KW_MONTHLY_SALES):   return self._handle_monthly_sales()
        elif self._match(msg, self._KW_TOTAL_SALES):     return self._handle_total_sales()
        elif self._match(msg, self._KW_SUPPLIER):        return self._handle_supplier_query(msg)
        elif self._match(msg, self._KW_RECOMMEND):       return self._handle_recommendation(msg)
        elif self._match(msg, self._KW_PRICE):           return self._handle_price_query(msg)
        elif self._match(msg, self._KW_SEARCH):          return self._handle_search(msg)
        elif self._match(msg, self._KW_HELP):            return self._handle_help()
        elif self._match(msg, self._KW_GREETING):        return self._handle_greeting()
        else:                                            return self._handle_generic_search(msg)

    # ──────────────────────────────────────────────────────────────
    #  HANDLERS
    # ──────────────────────────────────────────────────────────────

    def _handle_out_of_stock(self):
        from pharma_django.pharmacy_app.models import Medicine
        qs = Medicine.objects.filter(quantity=0).select_related('generic_name', 'presentation')

        if not qs.exists():
            return self._t(
                "✅ Great news! All medicines are currently in stock. No shortages detected.",
                "✅ बहुत अच्छा! सभी दवाएं स्टॉक में हैं। कोई कमी नहीं है।",
                "✅ छान! सर्व औषधे साठ्यात आहेत. कोणतीही कमतरता नाही.",
                "✅ Bahut accha! Saari dawaiyan stock mein hain. Koi kami nahi.",
                "✅ Chan! Sarv aushadhe sathyat aahet. Konatihi kamtarta nahi.",
            )

        count = qs.count()
        header = self._t(
            f"🔴 **Out of Stock — {count} Medicines**\n",
            f"🔴 **स्टॉक नहीं — {count} दवाएं**\n",
            f"🔴 **साठा नाही — {count} औषधे**\n",
            f"🔴 **Stock Khatam — {count} Dawaiyan**\n",
            f"🔴 **Satha Nahi — {count} Aushadhe**\n",
        )
        lines = [header]
        for m in qs[:15]:
            gen  = m.generic_name.name  if m.generic_name  else "—"
            pres = m.presentation.name  if m.presentation  else "—"
            lines.append(f"• **{m.name}** ({gen}, {pres})")

        if count > 15:
            lines.append(self._t(
                f"_...and {count-15} more. Check Inventory for full list._",
                f"_...और {count-15} दवाएं। पूरी सूची के लिए Inventory देखें।_",
                f"_...आणि {count-15} जास्त. पूर्ण यादीसाठी Inventory तपासा._",
                f"_...aur {count-15} aur hain. Poori list ke liye Inventory dekho._",
                f"_...aani {count-15} jast. Poorna yadisathi Inventory tapasa._",
            ))

        lines.append(self._t(
            "\n💡 **Tip:** Go to **Inventory → Add Purchase** to restock.",
            "\n💡 **सुझाव:** रीस्टॉक के लिए **Inventory → Add Purchase** पर जाएं।",
            "\n💡 **टीप:** पुन्हा साठा भरण्यासाठी **Inventory → Add Purchase** वर जा.",
            "\n💡 **Tip:** Restock karne ke liye **Inventory → Add Purchase** par jao.",
            "\n💡 **Tip:** Puna satha bharnyasathi **Inventory → Add Purchase** var ja.",
        ))
        return "\n".join(lines)

    # ─────────────────────────────────────────

    def _handle_low_stock(self):
        from pharma_django.pharmacy_app.models import Medicine
        qs    = Medicine.objects.filter(quantity__gt=0, quantity__lt=20).order_by('quantity')
        today = datetime.date.today()

        if not qs.exists():
            return self._t(
                "✅ No medicines are running critically low right now.",
                "✅ अभी कोई भी दवा खतरनाक रूप से कम नहीं है।",
                "✅ सध्या कोणतेही औषध धोकादायकरित्या कमी नाही.",
                "✅ Abhi koi bhi dawai critically kam nahi hai.",
                "✅ Sadya konatehi aushadh kami nahi.",
            )

        count  = qs.count()
        header = self._t(
            f"🟡 **Low Stock Warning — {count} Medicines**\n",
            f"🟡 **कम स्टॉक चेतावनी — {count} दवाएं**\n",
            f"🟡 **कमी साठा सूचना — {count} औषधे**\n",
            f"🟡 **Kam Stock Warning — {count} Dawaiyan**\n",
            f"🟡 **Kami Satha Suchana — {count} Aushadhe**\n",
        )
        lines = [header]

        for m in qs[:15]:
            gen = m.generic_name.name if m.generic_name else "—"
            if m.expire_date:
                d        = (m.expire_date - today).days
                days_lbl = self._t(
                    f"{d}d to expire", f"{d} दिन बचे", f"{d} दिवस शिल्लक",
                    f"{d} din baaki", f"{d} diwas shillak",
                )
            else:
                days_lbl = self._t("N/A", "N/A", "N/A", "N/A", "N/A")

            ul = self._t("units left", "यूनिट बचे", "युनिट शिल्लक",
                         "unit bache", "unit shillak")
            lines.append(f"• **{m.name}** ({gen}) — {m.quantity} {ul} | {days_lbl}")

        lines.append(self._t(
            "\n⚠️ Consider restocking these medicines soon.",
            "\n⚠️ इन दवाओं को जल्द रीस्टॉक करें।",
            "\n⚠️ या औषधांचा साठा लवकर भरा.",
            "\n⚠️ In dawaiyon ko jaldi restock karo.",
            "\n⚠️ Ya aushadhancha satha lavkar bhara.",
        ))
        return "\n".join(lines)

    # ─────────────────────────────────────────

    def _handle_expiry(self):
        from pharma_django.pharmacy_app.models import Medicine
        today = datetime.date.today()

        expired     = Medicine.objects.filter(expire_date__lt=today)
        expiring_30 = Medicine.objects.filter(
            expire_date__gte=today,
            expire_date__lte=today + datetime.timedelta(days=30)
        )
        expiring_90 = Medicine.objects.filter(
            expire_date__gt=today + datetime.timedelta(days=30),
            expire_date__lte=today + datetime.timedelta(days=90)
        )
        lines = []

        if expired.exists():
            lines.append(self._t(
                f"🔴 **Already Expired — {expired.count()} medicines:**",
                f"🔴 **पहले से एक्सपायर — {expired.count()} दवाएं:**",
                f"🔴 **आधीच कालबाह्य — {expired.count()} औषधे:**",
                f"🔴 **Pehle se Expire — {expired.count()} Dawaiyan:**",
                f"🔴 **Aadheech Kalbahya — {expired.count()} Aushadhe:**",
            ))
            for m in expired[:8]:
                lbl = self._t("expired on", "एक्सपायर हुई", "कालबाह्य",
                              "expire hua", "expire jhale")
                lines.append(f"  • {m.name} — {lbl} {m.expire_date.strftime('%d %b %Y')}")

        if expiring_30.exists():
            lines.append(self._t(
                f"\n🟠 **Expiring in 30 days — {expiring_30.count()} medicines:**",
                f"\n🟠 **30 दिनों में एक्सपायर — {expiring_30.count()} दवाएं:**",
                f"\n🟠 **30 दिवसांत कालबाह्य — {expiring_30.count()} औषधे:**",
                f"\n🟠 **30 Din Mein Expire — {expiring_30.count()} Dawaiyan:**",
                f"\n🟠 **30 Divasanmadhe Kalbahya — {expiring_30.count()} Aushadhe:**",
            ))
            for m in expiring_30[:8]:
                d   = (m.expire_date - today).days
                dlb = self._t(f"{d} days left", f"{d} दिन बचे", f"{d} दिवस शिल्लक",
                              f"{d} din baaki", f"{d} diwas shillak")
                lines.append(f"  • {m.name} — {dlb} ({m.expire_date.strftime('%d %b %Y')})")

        if expiring_90.exists():
            lines.append(self._t(
                f"\n🟡 **Expiring in 31–90 days — {expiring_90.count()} medicines:**",
                f"\n🟡 **31–90 दिनों में एक्सपायर — {expiring_90.count()} दवाएं:**",
                f"\n🟡 **31–90 दिवसांत कालबाह्य — {expiring_90.count()} औषधे:**",
                f"\n🟡 **31–90 Din Mein Expire — {expiring_90.count()} Dawaiyan:**",
                f"\n🟡 **31–90 Divasanmadhe Kalbahya — {expiring_90.count()} Aushadhe:**",
            ))
            for m in expiring_90[:5]:
                lbl = self._t("expires", "एक्सपायर होगी", "कालबाह्य होईल",
                              "expire hogi", "expire hoil")
                lines.append(f"  • {m.name} — {lbl} {m.expire_date.strftime('%d %b %Y')}")

        if not lines:
            return self._t(
                "✅ No expired or soon-to-expire medicines. Inventory looks healthy!",
                "✅ कोई एक्सपायर या जल्द एक्सपायर होने वाली दवा नहीं। इन्वेंटरी स्वस्थ है!",
                "✅ कोणतेही कालबाह्य औषध नाही. इन्व्हेंटरी निरोगी आहे!",
                "✅ Koi expire ya jaldi expire hone wali dawai nahi. Inventory theek hai!",
                "✅ Konatehi kalbahya aushadh nahi. Inventory nirogya aahe!",
            )

        lines.append(self._t(
            "\n💡 Navigate to **Inventory** to manage expiry dates.",
            "\n💡 एक्सपायरी तारीखें प्रबंधित करने के लिए **Inventory** पर जाएं।",
            "\n💡 कालबाह्य तारखा व्यवस्थापित करण्यासाठी **Inventory** वर जा.",
            "\n💡 Expiry dates manage karne ke liye **Inventory** par jao.",
            "\n💡 Kalbahya tarkhansathi **Inventory** var ja.",
        ))
        return "\n".join(lines)

    # ─────────────────────────────────────────

    def _handle_top_selling(self):
        from pharma_django.pharmacy_app.models import SaleItem
        top = (
            SaleItem.objects
            .values('medicine__name', 'medicine__id')
            .annotate(total_sold=Sum('quantity'), revenue=Sum('sub_total'))
            .order_by('-total_sold')[:10]
        )
        if not top:
            return self._t(
                "📊 No sales data yet. Start making sales to see analytics!",
                "📊 अभी कोई बिक्री डेटा नहीं। Analytics देखने के लिए बिक्री शुरू करें!",
                "📊 अद्याप विक्री डेटा नाही. Analytics साठी विक्री सुरू करा!",
                "📊 Abhi koi sales data nahi. Sales shuru karo analytics dekhne ke liye!",
                "📊 Adyap vikri data nahi. Analytics sathi vikri suru kara!",
            )

        header = self._t(
            "📊 **Top 10 Best-Selling Medicines**\n",
            "📊 **शीर्ष 10 सबसे ज्यादा बिकने वाली दवाएं**\n",
            "📊 **शीर्ष 10 सर्वाधिक विकली जाणारी औषधे**\n",
            "📊 **Top 10 Sabse Jyada Bikne Wali Dawaiyan**\n",
            "📊 **Top 10 Sarvadik Vikali Janari Aushadhe**\n",
        )
        ul = self._t("units sold", "यूनिट बिके", "युनिट विकले", "unit bike", "unit vikale")
        rl = self._t("revenue",    "राजस्व",     "महसूल",       "revenue",   "mahsul")
        lines = [header]
        for i, item in enumerate(top, 1):
            lines.append(
                f"{i}. **{item['medicine__name']}** — "
                f"{item['total_sold']} {ul} | ₹{float(item['revenue'] or 0):.0f} {rl}"
            )
        return "\n".join(lines)

    # ─────────────────────────────────────────

    def _handle_inventory_summary(self):
        from pharma_django.pharmacy_app.models import Medicine
        today = datetime.date.today()
        stats = Medicine.objects.aggregate(
            total=Count('id'),
            total_qty=Sum('quantity'),
            avg_price=Avg('selling_price')
        )
        out      = Medicine.objects.filter(quantity=0).count()
        low      = Medicine.objects.filter(quantity__gt=0, quantity__lt=20).count()
        expired  = Medicine.objects.filter(expire_date__lt=today).count()
        expiring = Medicine.objects.filter(
            expire_date__gte=today,
            expire_date__lte=today + datetime.timedelta(days=30)
        ).count()
        total = stats['total']    or 0
        qty   = int(stats['total_qty']  or 0)
        avg   = float(stats['avg_price'] or 0)

        templates = {
            'en': f"""📦 **Pharmacy Inventory Summary**

📌 **Stock Overview:**
• Total medicine types  : **{total}**
• Total units in stock  : **{qty:,}**
• Avg. selling price    : **₹{avg:.2f}**

🚦 **Stock Health:**
• 🔴 Out of stock        : **{out}** medicines
• 🟡 Low stock (<20 units): **{low}** medicines
• 🔴 Expired             : **{expired}** medicines
• 🟠 Expiring in 30 days : **{expiring}** medicines

📎 Type _'out of stock'_, _'expiry'_, or _'low stock'_ for details.""",

            'hi': f"""📦 **फार्मेसी इन्वेंटरी सारांश**

📌 **स्टॉक अवलोकन:**
• कुल दवा प्रकार       : **{total}**
• स्टॉक में कुल यूनिट  : **{qty:,}**
• औसत बिक्री मूल्य    : **₹{avg:.2f}**

🚦 **स्टॉक स्वास्थ्य:**
• 🔴 स्टॉक खत्म        : **{out}** दवाएं
• 🟡 कम स्टॉक (<20)    : **{low}** दवाएं
• 🔴 एक्सपायर          : **{expired}** दवाएं
• 🟠 30 दिनों में expire: **{expiring}** दवाएं

📎 विस्तार के लिए _'स्टॉक खत्म'_, _'एक्सपायरी'_ लिखें।""",

            'mr': f"""📦 **फार्मसी इन्व्हेंटरी सारांश**

📌 **साठा विहंगावलोकन:**
• एकूण औषध प्रकार     : **{total}**
• साठ्यातील एकूण युनिट: **{qty:,}**
• सरासरी विक्री किंमत  : **₹{avg:.2f}**

🚦 **साठा स्थिती:**
• 🔴 साठा नाही          : **{out}** औषधे
• 🟡 कमी साठा (<20)     : **{low}** औषधे
• 🔴 कालबाह्य           : **{expired}** औषधे
• 🟠 30 दिवसांत कालबाह्य : **{expiring}** औषधे

📎 तपशीलासाठी _'साठा नाही'_, _'कालबाह्य'_ टाइप करा.""",

            'rhi': f"""📦 **Pharmacy Inventory — Poora Haal**

📌 **Stock ki Sthiti:**
• Kul dawai prakar      : **{total}**
• Stock mein kul units  : **{qty:,}**
• Average selling price : **₹{avg:.2f}**

🚦 **Stock Health:**
• 🔴 Stock khatam        : **{out}** dawaiyan
• 🟡 Kam stock (<20)     : **{low}** dawaiyan
• 🔴 Expire ho gayi      : **{expired}** dawaiyan
• 🟠 30 din mein expire  : **{expiring}** dawaiyan

📎 Detail ke liye _'stock khatam'_, _'expiry'_, _'kam stock'_ likho.""",

            'rmr': f"""📦 **Pharmacy Inventory Saransh**

📌 **Satha chi Sthiti:**
• Ekun aushadh prakar   : **{total}**
• Sathyatil ekun units  : **{qty:,}**
• Sarash vikri kimat    : **₹{avg:.2f}**

🚦 **Satha Arogya:**
• 🔴 Satha nahi          : **{out}** aushadhe
• 🟡 Kami satha (<20)    : **{low}** aushadhe
• 🔴 Kalbahya            : **{expired}** aushadhe
• 🟠 30 divasanmadhe     : **{expiring}** aushadhe

📎 Tapshilasathi _'satha nahi'_, _'kalbahya'_, _'kami satha'_ tipa kara.""",
        }
        return templates.get(self.lang, templates['en'])

    def _handle_overview_summary(self):
        from pharma_django.pharmacy_app.models import Medicine, Sale, Supplier

        today = datetime.date.today()
        month_start = today.replace(day=1)
        total_medicines = Medicine.objects.count()
        total_units = int(Medicine.objects.aggregate(total_qty=Sum('quantity'))['total_qty'] or 0)
        out = Medicine.objects.filter(quantity=0).count()
        low = Medicine.objects.filter(quantity__gt=0, quantity__lt=20).count()
        expired = Medicine.objects.filter(expire_date__lt=today).count()
        expiring = Medicine.objects.filter(
            expire_date__gte=today,
            expire_date__lte=today + datetime.timedelta(days=30)
        ).count()
        today_sales = float(Sale.objects.filter(sale_date__date=today).aggregate(total=Sum('sub_total'))['total'] or 0)
        month_sales = float(Sale.objects.filter(sale_date__date__gte=month_start).aggregate(total=Sum('sub_total'))['total'] or 0)
        total_sales = float(Sale.objects.aggregate(total=Sum('sub_total'))['total'] or 0)
        suppliers = Supplier.objects.count()

        templates = {
            'en': f"""📋 **Pharmacy Overview**

📦 **Inventory**
• Medicines available : **{total_medicines}**
• Total units         : **{total_units:,}**
• Out of stock        : **{out}**
• Low stock           : **{low}**
• Expired             : **{expired}**
• Expiring in 30 days : **{expiring}**

💰 **Sales**
• Today               : **₹{today_sales:.2f}**
• This month          : **₹{month_sales:.2f}**
• All time            : **₹{total_sales:.2f}**

🏭 **Suppliers**
• Registered suppliers: **{suppliers}**

Ask me next:
• _out of stock_
• _expiry alert_
• _today's sales_
• _top selling medicines_
• _price of crocin_""",
            'rhi': f"""📋 **Pharmacy Overview**

📦 **Inventory**
• Total medicines     : **{total_medicines}**
• Kul units           : **{total_units:,}**
• Stock khatam        : **{out}**
• Kam stock           : **{low}**
• Expired             : **{expired}**
• 30 din mein expire  : **{expiring}**

💰 **Sales**
• Aaj                 : **₹{today_sales:.2f}**
• Is mahine           : **₹{month_sales:.2f}**
• Total               : **₹{total_sales:.2f}**

🏭 **Suppliers**
• Registered          : **{suppliers}**

Next poochho:
• _stock khatam_
• _expiry alert_
• _aaj ki bikri_
• _top selling medicines_
• _crocin ki kimat_""",
            'rmr': f"""📋 **Pharmacy Overview**

📦 **Inventory**
• Ekun aushadhe       : **{total_medicines}**
• Ekun units          : **{total_units:,}**
• Satha nahi          : **{out}**
• Kami satha          : **{low}**
• Kalbahya            : **{expired}**
• 30 divasat expire   : **{expiring}**

💰 **Sales**
• Aaj                 : **₹{today_sales:.2f}**
• Ya mahinyat         : **₹{month_sales:.2f}**
• Ekun                : **₹{total_sales:.2f}**

🏭 **Suppliers**
• Registered          : **{suppliers}**

Pudhe vichara:
• _satha nahi_
• _kalbahya_
• _aajchi vikri_
• _top selling medicines_
• _crocin chi kimat_""",
        }
        return templates.get(self.lang, templates['en'])

    # ─────────────────────────────────────────

    def _handle_today_sales(self):
        from pharma_django.pharmacy_app.models import Sale, SaleItem
        today   = datetime.date.today()
        agg     = Sale.objects.filter(sale_date__date=today).aggregate(
            revenue=Sum('sub_total'), count=Count('id')
        )
        revenue = float(agg['revenue'] or 0)
        count   = agg['count'] or 0
        top     = (
            SaleItem.objects.filter(sale__sale_date__date=today)
            .values('medicine__name')
            .annotate(qty=Sum('quantity'))
            .order_by('-qty')[:3]
        )
        ds = today.strftime('%d %b %Y')

        header = self._t(
            f"💵 **Today's Sales — {ds}**\n",
            f"💵 **आज की बिक्री — {ds}**\n",
            f"💵 **आजची विक्री — {ds}**\n",
            f"💵 **Aaj ki Bikri — {ds}**\n",
            f"💵 **Aajchi Vikri — {ds}**\n",
        )
        tx  = self._t("Transactions", "लेन-देन",    "व्यवहार",     "Transactions", "Vyavahar")
        rev = self._t("Total Revenue","कुल राजस्व", "एकूण महसूल", "Kul Revenue",  "Ekun Mahsul")
        th  = self._t("🔥 **Top Items Today:**",
                      "🔥 **आज के शीर्ष उत्पाद:**",
                      "🔥 **आजचे शीर्ष उत्पादने:**",
                      "🔥 **Aaj ke Top Items:**",
                      "🔥 **Aajche Top Items:**")
        ul  = self._t("units", "यूनिट", "युनिट", "unit", "unit")

        lines = [header, f"• {tx}: **{count}**", f"• {rev}: **₹{revenue:,.2f}**"]
        if top:
            lines.append(f"\n{th}")
            for t in top:
                lines.append(f"  • {t['medicine__name']} — {t['qty']} {ul}")
        return "\n".join(lines)

    # ─────────────────────────────────────────

    def _handle_monthly_sales(self):
        from pharma_django.pharmacy_app.models import Sale
        today = datetime.date.today()
        agg   = Sale.objects.filter(
            sale_date__date__gte=today.replace(day=1)
        ).aggregate(revenue=Sum('sub_total'), count=Count('id'))
        ms  = today.strftime('%B %Y')

        header = self._t(
            f"📅 **Monthly Sales — {ms}**\n",
            f"📅 **मासिक बिक्री — {ms}**\n",
            f"📅 **मासिक विक्री — {ms}**\n",
            f"📅 **Monthly Bikri — {ms}**\n",
            f"📅 **Masik Vikri — {ms}**\n",
        )
        tx  = self._t("Transactions", "लेन-देन",    "व्यवहार",     "Transactions", "Vyavahar")
        rev = self._t("Total Revenue","कुल राजस्व", "एकूण महसूल", "Kul Revenue",  "Ekun Mahsul")
        return f"{header}\n• {tx}: **{agg['count'] or 0}**\n• {rev}: **₹{float(agg['revenue'] or 0):,.2f}**"

    # ─────────────────────────────────────────

    def _handle_total_sales(self):
        from pharma_django.pharmacy_app.models import Sale
        agg = Sale.objects.aggregate(revenue=Sum('sub_total'), count=Count('id'))

        header = self._t(
            "📊 **All-Time Sales Summary**\n",
            "📊 **सर्वकालिक बिक्री सारांश**\n",
            "📊 **सर्वकालीन विक्री सारांश**\n",
            "📊 **All-Time Bikri Summary**\n",
            "📊 **Sarvakalin Vikri Saransh**\n",
        )
        tx  = self._t("Total Transactions", "कुल लेन-देन",  "एकूण व्यवहार",
                      "Kul Transactions",   "Ekun Vyavahar")
        rev = self._t("Total Revenue",      "कुल राजस्व",   "एकूण महसूल",
                      "Kul Revenue",        "Ekun Mahsul")
        return f"{header}\n• {tx}: **{agg['count'] or 0}**\n• {rev}: **₹{float(agg['revenue'] or 0):,.2f}**"

    # ─────────────────────────────────────────

    def _handle_supplier_query(self, msg):
        from pharma_django.pharmacy_app.models import Supplier
        qs = Supplier.objects.all()

        if not qs.exists():
            return self._t(
                "No suppliers found in the system.",
                "सिस्टम में कोई सप्लायर नहीं मिला।",
                "सिस्टममध्ये कोणताही पुरवठादार नाही.",
                "System mein koi supplier nahi mila.",
                "System madhe konatahi purvthadar nahi.",
            )

        header = self._t(
            f"🏭 **Registered Suppliers — {qs.count()} total**\n",
            f"🏭 **पंजीकृत सप्लायर — कुल {qs.count()}**\n",
            f"🏭 **नोंदणीकृत पुरवठादार — एकूण {qs.count()}**\n",
            f"🏭 **Registered Suppliers — kul {qs.count()}**\n",
            f"🏭 **Nondanibaddha Purvthadar — ekun {qs.count()}**\n",
        )
        lines = [header]
        for s in qs:
            lines.append(f"• **{s.company_name}** | 📞 {s.phone or 'N/A'} | ✉️ {s.email or 'N/A'}")
        return "\n".join(lines)

    # ─────────────────────────────────────────

    def _handle_recommendation(self, msg):
        strip_re = (
            r'\b(recommend|suggest|alternative|similar|substitute|for|me|a|an|the|'
            r'medicine|drug|give|what|about|'
            r'सिफारिश|सुझाव|विकल्प|दवा|दूसरी|जैसी|'
            r'शिफारस|सुचवा|पर्याय|औषध|दुसरे|सारखे|'
            r'sifarish|sujhav|vikalp|doosri|jaisi|recommend karo|suggest karo|'
            r'substitute|batao|alternative|koi aur|'
            r'shifaras|suchava|paryay|dusre|similar|recommend kara|suggest kara)\b'
        )
        clean = re.sub(strip_re, '', msg, flags=re.IGNORECASE).strip()

        if not clean:
            return self._t(
                "Please tell me the medicine name or symptom.\nExample: _'recommend fever medicine'_",
                "कृपया दवा का नाम या लक्षण बताएं।\nउदाहरण: _'बुखार की दवा सुझाएं'_",
                "कृपया औषधाचे नाव किंवा लक्षण सांगा.\nउदाहरण: _'तापाची औषध सुचवा'_",
                "Dawai ka naam ya symptom batao.\nExample: _'bukhar ki dawai recommend karo'_",
                "Aushadhache nav kiva lakshan sanga.\nExample: _'tapachi aushadh suchava'_",
            )

        from pharma_django.ml_engine.recommender import MedicineRecommender
        results = MedicineRecommender().recommend(clean, n=8)

        if not results:
            return self._t(
                f"Couldn't find recommendations for **'{clean}'**. Try a different term.",
                f"**'{clean}'** के लिए सिफारिश नहीं मिली। कोई और नाम आज़माएं।",
                f"**'{clean}'** साठी शिफारस नाही. दुसरे नाव वापरा.",
                f"**'{clean}'** ke liye koi suggestion nahi. Kuch aur try karo.",
                f"**'{clean}'** sathi shifaras nahi. Dusre nav vapara.",
            )

        header = self._t(
            f"💊 **Recommendations for '{clean}':**\n",
            f"💊 **'{clean}' के लिए सिफारिशें:**\n",
            f"💊 **'{clean}' साठी शिफारसी:**\n",
            f"💊 **'{clean}' ke liye Suggestions:**\n",
            f"💊 **'{clean}' sathi Shifarasi:**\n",
        )
        sl = self._t("Stock", "स्टॉक", "साठा",  "Stock", "Satha")
        ml = self._t("Match", "मिलान", "जुळणी", "Match", "Julni")
        lines = [header]
        for r in results:
            icon = "✅" if r['quantity'] > 20 else "🟡" if r['quantity'] > 0 else "🔴"
            lines.append(
                f"{icon} **{r['name']}** "
                f"({r.get('generic_name','')}, {r.get('presentation','')})\n"
                f"   ₹{r['selling_price']} | {sl}: {r['quantity']} | {ml}: {r['similarity']}%"
            )
        return "\n".join(lines)

    # ─────────────────────────────────────────

    def _handle_price_query(self, msg):
        from pharma_django.pharmacy_app.models import Medicine
        strip_re = (
            r'\b(price|cost|how much|rate|of|for|is|the|pricing|'
            r'कीमत|दाम|कितना|मूल्य|रेट|भाव|की|का|'
            r'किंमत|दर|किती|रेट|'
            r'kimat|dam|kitna paisa|rate kya|bhav|mulya|kya rate|'
            r'kimat kiti|dar kiti|bhav kiti)\b'
        )
        clean = re.sub(strip_re, '', msg, flags=re.IGNORECASE).strip()

        if not clean:
            return self._t(
                "Please specify a medicine name.\nExample: _'price of Crocin'_",
                "कृपया दवा का नाम बताएं।\nउदाहरण: _'Crocin की कीमत'_",
                "कृपया औषधाचे नाव सांगा.\nउदाहरण: _'Crocin ची किंमत'_",
                "Dawai ka naam batao.\nExample: _'Crocin ki kimat kya hai'_",
                "Aushadhache nav sanga.\nExample: _'Crocin chi kimat kiti'_",
            )

        qs = Medicine.objects.filter(
            Q(name__icontains=clean) | Q(generic_name__name__icontains=clean)
        ).select_related('generic_name')[:8]
        if not qs.exists():
            return self._t(
                f"No medicine found matching **'{clean}'**. Please check the name.",
                f"**'{clean}'** नाम की कोई दवा नहीं मिली। नाम जांचें।",
                f"**'{clean}'** नावाचे कोणतेही औषध नाही. नाव तपासा.",
                f"**'{clean}'** naam ki koi dawai nahi. Naam check karo.",
                f"**'{clean}'** navache konatehi aushadh nahi. Nav tapasa.",
            )

        header = self._t(
            f"💰 **Price Info — '{clean}':**\n",
            f"💰 **'{clean}' की कीमत:**\n",
            f"💰 **'{clean}' ची किंमत:**\n",
            f"💰 **'{clean}' ki Kimat:**\n",
            f"💰 **'{clean}' chi Kimat:**\n",
        )
        oos = self._t("**OUT OF STOCK**", "**स्टॉक नहीं**", "**साठा नाही**",
                      "**Stock Khatam**", "**Satha Nahi**")
        sl  = self._t("Stock", "स्टॉक", "साठा", "Stock", "Satha")
        lines = [header]
        for m in qs:
            stk = f"{m.quantity} units" if m.quantity > 0 else oos
            generic = f" ({m.generic_name.name})" if m.generic_name else ""
            lines.append(f"• **{m.name}**{generic} — ₹{m.selling_price} | {sl}: {stk}")
        return "\n".join(lines)

    # ─────────────────────────────────────────

    def _handle_search(self, msg):
        strip_re = (
            r'\b(search|find|look for|show me|get|fetch|'
            r'खोजो|ढूंढो|खोजें|दिखाओ|बताओ|ढूंढें|'
            r'शोधा|दाखवा|मिळवा|'
            r'khojo|dhundho|dikhao|batao|search karo|dhundo|la do|'
            r'shodha|dakahva|milva|search kara)\b'
        )
        clean = re.sub(strip_re, '', msg, flags=re.IGNORECASE).strip()
        return self._handle_generic_search(clean)

    # ─────────────────────────────────────────

    def _handle_generic_search(self, msg):
        from pharma_django.pharmacy_app.models import Medicine
        if len(msg) < 2:
            return self._handle_help()

        qs = Medicine.objects.filter(
            Q(name__icontains=msg) |
            Q(generic_name__name__icontains=msg) |
            Q(description__icontains=msg) |
            Q(volume__icontains=msg)
        ).select_related('generic_name', 'presentation')[:8]

        if not qs.exists():
            return self._t(
                (f"🔍 No results for **'{msg}'**.\n\n"
                 "Try:\n• A different medicine name or generic name\n"
                 "• 'out of stock' / 'expiry' / 'recommend fever medicine'\n"
                 "• Type **help** for all commands"),
                (f"🔍 **'{msg}'** के लिए कोई परिणाम नहीं।\n\n"
                 "आज़माएं:\n• दूसरा दवा या generic नाम\n"
                 "• 'स्टॉक खत्म' / 'एक्सपायरी' / 'बुखार दवा सुझाएं'\n"
                 "• सभी आदेशों के लिए **मदद** लिखें"),
                (f"🔍 **'{msg}'** साठी काहीही मिळाले नाही.\n\n"
                 "प्रयत्न करा:\n• वेगळे औषध नाव\n"
                 "• 'साठा नाही' / 'कालबाह्य' / 'ताप औषध सुचवा'\n"
                 "• सर्व आदेशांसाठी **मदत** टाइप करा"),
                (f"🔍 **'{msg}'** ke liye kuch nahi mila.\n\n"
                 "Try karo:\n• Koi doosra dawai naam\n"
                 "• 'stock khatam' / 'expiry' / 'bukhar dawai suggest karo'\n"
                 "• Sab commands ke liye **madad** likho"),
                (f"🔍 **'{msg}'** sathi kahi milale nahi.\n\n"
                 "Prayatna kara:\n• Vegale aushadh nav\n"
                 "• 'satha nahi' / 'kalbahya' / 'tap aushadh suchava'\n"
                 "• Sarv adeshanasathi **madat** tipa kara"),
            )

        header = self._t(
            f"🔍 **Search Results for '{msg}':**\n",
            f"🔍 **'{msg}' के खोज परिणाम:**\n",
            f"🔍 **'{msg}' साठी शोध निकाल:**\n",
            f"🔍 **'{msg}' ke liye Results:**\n",
            f"🔍 **'{msg}' sathi Shodh Nikal:**\n",
        )
        ul = self._t("units", "यूनिट", "युनिट", "unit", "unit")
        lines = [header]
        for m in qs:
            gen  = m.generic_name.name if m.generic_name else "—"
            pres = m.presentation.name if m.presentation else "—"
            icon = "✅" if m.quantity > 20 else "🟡" if m.quantity > 0 else "🔴"
            lines.append(
                f"{icon} **{m.name}** ({gen}, {pres}) — ₹{m.selling_price} | {m.quantity} {ul}"
            )
        return "\n".join(lines)

    # ─────────────────────────────────────────

    def _handle_greeting(self):
        pools = {
            'en': [
                "👋 Hello! I'm **PharmaBot**, your AI pharmacy assistant.\nType **help** to see all commands!",
                "🌟 Hi there! Ready to manage your pharmacy.\nAsk me about stock, expiry, sales, or recommendations!",
                "👋 Hey! Your pharmacy AI is here.\nStock alerts, medicine search, sales reports & more — type **help**!",
            ],
            'hi': [
                "👋 नमस्ते! मैं **PharmaBot** हूं — आपका AI फार्मेसी सहायक।\nसभी कमांड देखने के लिए **मदद** टाइप करें।",
                "🌟 नमस्कार! फार्मेसी प्रबंधन के लिए तैयार हूं।\nस्टॉक, एक्सपायरी, बिक्री या सिफारिश पूछें!",
                "👋 हेलो! मैं आपका फार्मेसी AI हूं।\nस्टॉक, दवा खोज, बिक्री रिपोर्ट। शुरू करें — **मदद** लिखें!",
            ],
            'mr': [
                "👋 नमस्कार! मी **PharmaBot** आहे — तुमचा AI फार्मसी सहाय्यक.\nसर्व आदेश पाहण्यासाठी **मदत** टाइप करा.",
                "🌟 नमस्ते! फार्मसी व्यवस्थापनासाठी तयार आहे.\nसाठा, कालबाह्यता, विक्री याबद्दल विचारा!",
                "👋 हॅलो! मी तुमचा फार्मसी AI आहे.\nसाठा, औषध शोध, विक्री अहवाल. **मदत** टाइप करा!",
            ],
            'rhi': [
                "👋 Namaste! Main **PharmaBot** hoon — aapka AI pharmacy assistant.\nSab commands ke liye **madad** likho!",
                "🌟 Hello yaar! Pharmacy manage karne ke liye ready hoon.\nStock, expiry, bikri ya dawai suggestion poochho!",
                "👋 Hey! Aapka pharmacy AI yahan hai.\nStock alerts, dawai search, bikri reports. **madad** likho shuru karne ke liye!",
            ],
            'rmr': [
                "👋 Namaskar! Mi **PharmaBot** aahe — tumcha AI pharmacy sahayak.\nSarv commands sathi **madat** tipa kara!",
                "🌟 Helo! Pharmacy vyavasthapanasathi tayar aahe.\nSatha, kalbahyata, vikri yaabadal vicharaa!",
                "👋 Hey! Tumcha pharmacy AI ithe aahe.\nSatha, aushadh shodh, vikri ahval. **madat** tipa kara!",
            ],
        }
        return random.choice(pools.get(self.lang, pools['en']))

    # ─────────────────────────────────────────

    def _handle_help(self):
        helps = {

'en': """🤖 **PharmaBot — AI Pharmacy Assistant**
_Supports: English | हिंदी | मराठी | Hinglish | Roman Marathi_

**📦 Stock & Inventory:**
• `out of stock`       — Medicines with zero stock
• `low stock`          — Medicines below 20 units
• `inventory summary`  — Full stock overview

**⏰ Expiry Management:**
• `expiry alert`       — Expired & soon-to-expire medicines
• `expired medicines`  — Only already-expired items

**💊 Medicine Search & Recommendations:**
• `search crocin`             — Find a specific medicine
• `price of paracetamol`      — Get pricing info
• `recommend fever medicine`  — ML-based suggestions
• `alternative for ibuprofen` — Find substitutes

**📊 Sales & Revenue:**
• `today's sales`          — Today's revenue & transactions
• `monthly sales`          — This month's performance
• `total sales`            — All-time summary
• `top selling medicines`  — Best-seller analytics

**🏭 Suppliers:**
• `show suppliers`  — List all suppliers

_Ask naturally in any of the 5 supported languages!_ 🌟""",

'hi': """🤖 **PharmaBot — AI फार्मेसी सहायक**
_भाषाएं: English | हिंदी | मराठी | Hinglish | Roman Marathi_

**📦 स्टॉक और इन्वेंटरी:**
• `स्टॉक खत्म`       — शून्य स्टॉक वाली दवाएं
• `कम स्टॉक`          — 20 से कम यूनिट वाली दवाएं
• `इन्वेंटरी सारांश`  — पूर्ण स्टॉक अवलोकन

**⏰ एक्सपायरी प्रबंधन:**
• `एक्सपायरी अलर्ट`  — एक्सपायर / जल्द एक्सपायर दवाएं
• `एक्सपायर दवाएं`   — केवल एक्सपायर स्टॉक

**💊 दवा खोज और सिफारिश:**
• `crocin खोजें`             — विशिष्ट दवा खोजें
• `paracetamol की कीमत`       — मूल्य जानकारी
• `बुखार की दवा सुझाएं`      — ML सिफारिश
• `ibuprofen का विकल्प`       — विकल्प सुझाएं

**📊 बिक्री और राजस्व:**
• `आज की बिक्री`              — आज का राजस्व
• `मासिक बिक्री`              — इस महीने की बिक्री
• `कुल बिक्री`                — सर्वकालिक सारांश
• `सबसे ज्यादा बिकने वाली दवाएं`

**🏭 सप्लायर:**
• `सप्लायर दिखाएं`  — सभी सप्लायर सूची

_स्वाभाविक हिंदी में पूछें — मैं समझता हूं!_ 🌟""",

'mr': """🤖 **PharmaBot — AI फार्मसी सहाय्यक**
_भाषा: English | हिंदी | मराठी | Hinglish | Roman Marathi_

**📦 साठा आणि इन्व्हेंटरी:**
• `साठा नाही`          — शून्य साठ्याची औषधे
• `कमी साठा`           — 20 पेक्षा कमी युनिट
• `इन्व्हेंटरी सारांश` — पूर्ण साठा विहंगावलोकन

**⏰ कालबाह्यता व्यवस्थापन:**
• `कालबाह्य सूचना`  — कालबाह्य / लवकर कालबाह्य होणारी
• `कालबाह्य औषधे`   — केवळ कालबाह्य साठा

**💊 औषध शोध आणि शिफारस:**
• `crocin शोधा`            — विशिष्ट औषध शोधा
• `paracetamol ची किंमत`   — किंमत माहिती
• `तापाची औषध सुचवा`       — ML शिफारस
• `ibuprofen चा पर्याय`    — पर्याय सुचवा

**📊 विक्री आणि महसूल:**
• `आजची विक्री`          — आजचा महसूल
• `मासिक विक्री`          — या महिन्याची विक्री
• `एकूण विक्री`           — सर्वकालीन सारांश
• `सर्वाधिक विकली औषधे`

**🏭 पुरवठादार:**
• `पुरवठादार दाखवा`  — सर्व पुरवठादार यादी

_नैसर्गिक मराठीत विचारा — मी समजतो!_ 🌟""",

'rhi': """🤖 **PharmaBot — AI Pharmacy Assistant**
_Languages: English | हिंदी | मराठी | Hinglish | Roman Marathi_

**📦 Stock aur Inventory:**
• `stock khatam`       — Zero stock wali dawaiyan
• `kam stock`          — 20 se kam unit wali dawaiyan
• `inventory dekho`    — Poora stock overview

**⏰ Expiry:**
• `expiry alert`       — Expire / jaldi expire hone wali dawaiyan
• `expire ho gayi`     — Sirf expire hua stock

**💊 Dawai Search aur Suggestion:**
• `crocin khojo`                       — Specific dawai dhundo
• `paracetamol ki kimat`               — Price info
• `bukhar ki dawai recommend karo`     — ML recommendation
• `ibuprofen ka alternative batao`     — Doosri dawai batao

**📊 Bikri aur Revenue:**
• `aaj ki bikri`           — Aaj ka revenue
• `masik bikri`            — Is mahine ki bikri
• `kul bikri`              — All-time summary
• `sabse jyada bikne wali` — Top sellers

**🏭 Supplier:**
• `supplier dikhao`  — Sab suppliers ki list

_Hinglish ya Roman mein seedha poochho — main samajhta hoon!_ 🌟""",

'rmr': """🤖 **PharmaBot — AI Pharmacy Sahayak**
_Bhasha: English | हिंदी | मराठी | Hinglish | Roman Marathi_

**📦 Satha ani Inventory:**
• `satha nahi`          — Zero sathyachi aushadhe
• `kami satha`          — 20 peksha kami unit
• `inventory bagh`      — Poorna satha overview

**⏰ Kalbahyata:**
• `kalbahya suchna`     — Kalbahya / lavkar kalbahya
• `expire jhale`        — Sirf kalbahya satha

**💊 Aushadh Shodh ani Shifaras:**
• `crocin shodha`                 — Vishisht aushadh shodha
• `paracetamol chi kimat`         — Kimat mahiti
• `tapachi aushadh suchava`       — ML shifaras
• `ibuprofen cha paryay suchava`  — Paryay suchava

**📊 Vikri ani Mahsul:**
• `aajchi vikri`         — Aajcha mahsul
• `masik vikri`          — Ya mahinyachi vikri
• `ekun vikri`           — Sarvakalin saransh
• `sarvadik vikali`      — Top sellers

**🏭 Purvthadar:**
• `purvthadar dakahva`  — Sarv purvthadar yadi

_Naisargik Marathit kiva Roman madhe vicharaa — mi samajto!_ 🌟""",
        }
        return helps.get(self.lang, helps['en'])

    def _extract_search_text(self, msg: str) -> str:
        cleaned = re.sub(r'[^a-z0-9\s\-\+\.]', ' ', msg.lower())
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        stop_words = {
            'search', 'find', 'show', 'medicine', 'medicines', 'price', 'cost',
            'recommend', 'suggest', 'alternative', 'substitute', 'for', 'of',
            'the', 'a', 'an', 'me', 'please', 'check', 'stock', 'availability',
            'order', 'status', 'online', 'cart', 'checkout', 'rx',
            'kya', 'hai', 'ki', 'ka', 'ke', 'ko', 'batao', 'dikhao', 'karo'
        }
        parts = [p for p in cleaned.split(' ') if p and p not in stop_words]
        return ' '.join(parts).strip()

    def _medicine_health_tag(self, medicine):
        today = datetime.date.today()
        if medicine.quantity <= 0:
            stock_text = "Out of stock"
            icon = "RED"
        elif medicine.quantity < 20:
            stock_text = f"Low stock ({medicine.quantity})"
            icon = "YELLOW"
        else:
            stock_text = f"In stock ({medicine.quantity})"
            icon = "GREEN"

        expiry_text = ""
        if medicine.expire_date:
            days_left = (medicine.expire_date - today).days
            if days_left < 0:
                expiry_text = f" | Expired {abs(days_left)}d ago"
            elif days_left <= 30:
                expiry_text = f" | Expiry warning: {days_left}d"
        return icon, stock_text + expiry_text

    def _fuzzy_medicine_matches(self, text: str, limit: int = 6):
        from pharma_django.pharmacy_app.models import Medicine
        query = (text or '').strip().lower()
        if not query:
            return []

        medicines = list(Medicine.objects.select_related('generic_name', 'presentation').all()[:500])
        if not medicines:
            return []

        candidates = []
        names = []
        for med in medicines:
            name = (med.name or '').lower().strip()
            generic = (med.generic_name.name.lower().strip() if med.generic_name else '')
            tokens = [name]
            if generic:
                tokens.append(generic)
            names.extend(tokens)
            score = max(SequenceMatcher(None, query, token).ratio() for token in tokens if token)
            if score >= 0.45:
                candidates.append((score, med))

        close = get_close_matches(query, names, n=limit * 2, cutoff=0.6)
        if close:
            for med in medicines:
                pool = [med.name.lower()]
                if med.generic_name:
                    pool.append(med.generic_name.name.lower())
                if any(item in pool for item in close):
                    score = max(SequenceMatcher(None, query, token).ratio() for token in pool if token)
                    if score >= 0.45:
                        candidates.append((score, med))

        ranked = []
        seen = set()
        for score, med in sorted(candidates, key=lambda item: item[0], reverse=True):
            if med.id in seen:
                continue
            seen.add(med.id)
            ranked.append((score, med))
            if len(ranked) >= limit:
                break
        return ranked

    def _substitute_suggestions(self, medicine, limit: int = 4):
        from pharma_django.pharmacy_app.models import Medicine
        if not medicine.generic_name_id:
            return []
        qs = Medicine.objects.filter(
            generic_name_id=medicine.generic_name_id
        ).exclude(id=medicine.id).order_by('selling_price', '-quantity')[:20]
        in_stock = [m for m in qs if m.quantity > 0]
        if in_stock:
            qs = in_stock
        return list(qs[:limit])

    def _handle_autosuggest(self, msg):
        from pharma_django.pharmacy_app.models import Medicine
        query = self._extract_search_text(msg)
        if not query:
            return self._t(
                "Type 1-2 letters and I will suggest medicines instantly.\nExample: `pa` or `cro`.",
                "1-2 अक्षर लिखें, मैं तुरंत medicine suggest करूँगा.\nउदाहरण: `pa` या `cro`.",
                "1-2 अक्षरे टाइप करा, मी लगेच औषधे सुचवेन.\nउदाहरण: `pa` किंवा `cro`.",
                "1-2 letter type karo, main turant medicine suggest karunga.\nExample: `pa` ya `cro`.",
                "1-2 akshare type kara, mi turant aushadhe suchaven.\nExample: `pa` kiwa `cro`.",
            )

        starts = Medicine.objects.filter(
            Q(name__istartswith=query) | Q(generic_name__name__istartswith=query)
        ).select_related('generic_name')[:10]
        if not starts:
            starts = Medicine.objects.filter(
                Q(name__icontains=query) | Q(generic_name__name__icontains=query)
            ).select_related('generic_name')[:10]

        if not starts:
            fuzzy = self._fuzzy_medicine_matches(query, limit=6)
            if not fuzzy:
                return self._t(
                    f"No close medicine found for '{query}'. Try another spelling.",
                    f"'{query}' के लिए कोई close medicine नहीं मिली। दूसरा spelling try करें।",
                    f"'{query}' साठी close औषध मिळाले नाही. दुसरे spelling वापरा.",
                    f"'{query}' ke liye close medicine nahi mili. Dusra spelling try karo.",
                    f"'{query}' sathi close aushadh milale nahi. Dusre spelling vapara.",
                )
            lines = [self._t("Closest matches:", "Closest matches:", "Closest matches:", "Closest matches:", "Closest matches:")]
            for score, med in fuzzy:
                _, status_text = self._medicine_health_tag(med)
                rx = " | Rx required" if getattr(med, 'prescription_required', False) else ""
                lines.append(f"- {med.name} - Rs.{med.selling_price} - {status_text}{rx} ({int(score * 100)}%)")
            return "\n".join(lines)

        lines = [self._t("Medicine suggestions:", "Medicine suggestions:", "Medicine suggestions:", "Medicine suggestions:", "Medicine suggestions:")]
        for med in starts:
            _, status_text = self._medicine_health_tag(med)
            rx = " | Rx required" if getattr(med, 'prescription_required', False) else ""
            lines.append(f"- {med.name} - Rs.{med.selling_price} - {status_text}{rx}")
        return "\n".join(lines)

    def _handle_safety_help(self):
        return self._t(
            "Safety first:\n- Rx medicines need approved prescription.\n- I can suggest stock/substitutes, not diagnosis.\n- For severe symptoms, pregnancy, child dose, or interaction risk: consult doctor immediately.",
            "Safety first:\n- Rx medicines के लिए approved prescription ज़रूरी है।\n- मैं stock/substitute बता सकता हूँ, diagnosis नहीं।\n- Severe symptoms, pregnancy, child dose या interaction risk में तुरंत doctor से मिलें।",
            "Safety first:\n- Rx medicines साठी approved prescription आवश्यक आहे.\n- मी stock/substitute सांगू शकतो, diagnosis नाही.\n- Severe symptoms, pregnancy, child dose किंवा interaction risk साठी त्वरित doctor कडे जा.",
            "Safety first:\n- Rx medicine ke liye approved prescription zaroori hai.\n- Main stock/substitute suggest karta hoon, diagnosis nahi.\n- Severe symptoms, pregnancy, child dose, interaction risk me doctor ko turant dikhayein.",
            "Safety first:\n- Rx medicine sathi approved prescription avashyak aahe.\n- Mi stock/substitute sangto, diagnosis nahi.\n- Severe symptoms, pregnancy, child dose, interaction risk madhe doctor la turant dakhava.",
        )

    def _handle_billing_help(self):
        return self._t(
            "Billing quick steps:\n1. Open New Sale.\n2. Add medicine and quantity.\n3. Verify stock and discount.\n4. Enter payment amount.\n5. Generate GST invoice.",
            "Billing quick steps:\n1. New Sale खोलें.\n2. Medicine और quantity add करें.\n3. Stock और discount verify करें.\n4. Payment amount डालें.\n5. GST invoice generate करें।",
            "Billing quick steps:\n1. New Sale उघडा.\n2. Medicine आणि quantity add करा.\n3. Stock आणि discount verify करा.\n4. Payment amount भरा.\n5. GST invoice generate करा.",
            "Billing quick steps:\n1. New Sale kholo.\n2. Medicine aur quantity add karo.\n3. Stock aur discount verify karo.\n4. Payment amount daalo.\n5. GST invoice generate karo.",
            "Billing quick steps:\n1. New Sale ughada.\n2. Medicine ani quantity add kara.\n3. Stock ani discount verify kara.\n4. Payment amount bhara.\n5. GST invoice generate kara.",
        )

    def _handle_online_order_support(self, msg):
        from pharma_django.pharmacy_app.models import OnlineOrder, CustomerProfile
        text = msg.lower()
        status_map = {
            'pending': 'pending',
            'approved': 'approved',
            'packed': 'packed',
            'out for delivery': 'out_for_delivery',
            'out_for_delivery': 'out_for_delivery',
            'delivered': 'delivered',
        }

        selected_status = None
        for label, value in status_map.items():
            if label in text:
                selected_status = value
                break

        if selected_status:
            orders = OnlineOrder.objects.filter(status=selected_status).select_related('customer__user')[:10]
            if not orders:
                return f"No online orders found with status '{selected_status}'."
            lines = [f"Online orders ({selected_status}):"]
            for order in orders:
                lines.append(f"- {order.order_id} | {order.customer_name or order.customer.user.username} | Rs.{order.total_amount}")
            return "\n".join(lines)

        customer = None
        try:
            customer = CustomerProfile.objects.get(user=self.user)
        except CustomerProfile.DoesNotExist:
            customer = None

        if customer:
            my_orders = OnlineOrder.objects.filter(customer=customer).order_by('-created_at')[:5]
            if my_orders:
                lines = ["Your recent online orders:"]
                for order in my_orders:
                    lines.append(f"- {order.order_id}: {order.get_status_display()} | Rs.{order.total_amount}")
                lines.append("Flow: search -> add to cart -> checkout -> place order -> track status.")
                return "\n".join(lines)

        global_counts = OnlineOrder.objects.values('status').annotate(total=Count('id')).order_by('status')
        if not global_counts:
            return "No online orders yet. Start with: Online Medicines -> Add to Cart -> Checkout (COD/UPI/Card)."

        lines = ["Online order status summary:"]
        for row in global_counts:
            lines.append(f"- {row['status']}: {row['total']}")
        lines.append("Need help? Ask: 'how to place online order' or 'show pending orders'.")
        return "\n".join(lines)

    def _handle_recommendation(self, msg):
        from pharma_django.pharmacy_app.models import Medicine
        from pharma_django.ml_engine.recommender import MedicineRecommender

        cleaned = self._extract_search_text(msg)
        if not cleaned:
            return "Please share medicine name or symptom. Example: recommend fever medicine"

        results = MedicineRecommender().recommend(cleaned, n=8)
        if not results:
            fuzzy = self._fuzzy_medicine_matches(cleaned, limit=5)
            if not fuzzy:
                return f"No recommendation found for '{cleaned}'. Try another name/symptom."
            lines = [f"No direct recommendation for '{cleaned}'. Closest matches:"]
            for score, med in fuzzy:
                _, status_text = self._medicine_health_tag(med)
                lines.append(f"- {med.name} | Rs.{med.selling_price} | {status_text} ({int(score * 100)}%)")
            return "\n".join(lines)

        lines = [f"Recommendations for '{cleaned}':"]
        for result in results:
            try:
                med = Medicine.objects.select_related('generic_name').get(pk=result['id'])
            except Medicine.DoesNotExist:
                med = None

            stock_icon = "OK" if result['quantity'] > 20 else "LOW" if result['quantity'] > 0 else "OUT"
            rx_text = " | Rx required" if med and getattr(med, 'prescription_required', False) else ""
            lines.append(
                f"- {stock_icon} {result['name']} ({result.get('generic_name','')}) | "
                f"Rs.{result['selling_price']} | stock {result['quantity']} | match {result['similarity']}%{rx_text}"
            )

            if med:
                cheaper = [
                    item for item in self._substitute_suggestions(med, limit=3)
                    if float(item.selling_price) < float(med.selling_price)
                ]
                if cheaper:
                    lines.append(
                        "  cheaper substitute: " +
                        ", ".join(f"{item.name} (Rs.{item.selling_price})" for item in cheaper[:2])
                    )
        lines.append("Safety note: This is assistance only. For severe symptoms, consult doctor.")
        return "\n".join(lines)

    def _handle_price_query(self, msg):
        from pharma_django.pharmacy_app.models import Medicine

        cleaned = self._extract_search_text(msg)
        if not cleaned:
            return "Please specify medicine name. Example: price of paracetamol"

        matches = Medicine.objects.filter(
            Q(name__icontains=cleaned) | Q(generic_name__name__icontains=cleaned)
        ).select_related('generic_name')[:8]

        if not matches:
            fuzzy = self._fuzzy_medicine_matches(cleaned, limit=5)
            if not fuzzy:
                return f"No medicine found for '{cleaned}'. Check spelling."
            lines = [f"Closest medicines for '{cleaned}':"]
            for score, med in fuzzy:
                _, status_text = self._medicine_health_tag(med)
                lines.append(f"- {med.name} | Rs.{med.selling_price} | {status_text} ({int(score * 100)}%)")
            return "\n".join(lines)

        lines = [f"Price details for '{cleaned}':"]
        for medicine in matches:
            _, status_text = self._medicine_health_tag(medicine)
            rx_text = " | Rx required" if getattr(medicine, 'prescription_required', False) else ""
            lines.append(
                f"- {medicine.name} ({medicine.generic_name.name if medicine.generic_name else '-'}) | "
                f"Rs.{medicine.selling_price} | {status_text}{rx_text}"
            )
            substitutes = self._substitute_suggestions(medicine, limit=2)
            cheaper = [item for item in substitutes if float(item.selling_price) < float(medicine.selling_price)]
            if cheaper:
                lines.append("  cheaper option: " + ", ".join(f"{item.name} (Rs.{item.selling_price})" for item in cheaper))
        return "\n".join(lines)

    def _handle_generic_search(self, msg):
        from pharma_django.pharmacy_app.models import Medicine
        cleaned = self._extract_search_text(msg)
        if not cleaned:
            return self._handle_help()

        if len(cleaned) <= 2:
            starts = Medicine.objects.filter(
                Q(name__istartswith=cleaned) | Q(generic_name__name__istartswith=cleaned)
            ).select_related('generic_name', 'presentation')[:10]
            if not starts:
                return f"No quick suggestions for '{cleaned}'. Type one more letter."
            lines = [f"Quick suggestions for '{cleaned}':"]
            for medicine in starts:
                _, status_text = self._medicine_health_tag(medicine)
                lines.append(f"- {medicine.name} | Rs.{medicine.selling_price} | {status_text}")
            return "\n".join(lines)

        matches = Medicine.objects.filter(
            Q(name__icontains=cleaned) |
            Q(generic_name__name__icontains=cleaned) |
            Q(description__icontains=cleaned) |
            Q(volume__icontains=cleaned)
        ).select_related('generic_name', 'presentation')[:8]

        if not matches:
            fuzzy = self._fuzzy_medicine_matches(cleaned, limit=6)
            if not fuzzy:
                return f"No results for '{cleaned}'. Try different spelling or ask 'help'."
            lines = [f"No exact result for '{cleaned}'. Closest matches:"]
            for score, medicine in fuzzy:
                _, status_text = self._medicine_health_tag(medicine)
                lines.append(f"- {medicine.name} | Rs.{medicine.selling_price} | {status_text} ({int(score * 100)}%)")
            return "\n".join(lines)

        lines = [f"Search results for '{cleaned}':"]
        for medicine in matches:
            _, status_text = self._medicine_health_tag(medicine)
            rx_text = " | Rx required" if getattr(medicine, 'prescription_required', False) else ""
            lines.append(
                f"- {medicine.name} ({medicine.generic_name.name if medicine.generic_name else '-'}) | "
                f"Rs.{medicine.selling_price} | {status_text}{rx_text}"
            )
            if medicine.quantity <= 0:
                substitutes = self._substitute_suggestions(medicine, limit=2)
                if substitutes:
                    lines.append(
                        "  substitute: " +
                        ", ".join(f"{item.name} (Rs.{item.selling_price}, qty {item.quantity})" for item in substitutes)
                    )
        return "\n".join(lines)

    # ──────────────────────────────────────────────────────────────
    #  UTILITY
    # ──────────────────────────────────────────────────────────────

    def _match(self, text: str, keywords: list) -> bool:
        """Return True if any keyword appears in text (case-insensitive, all scripts)."""
        t = text.lower()
        return any(kw.lower() in t for kw in keywords)
