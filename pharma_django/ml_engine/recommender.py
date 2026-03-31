"""
Medicine Recommendation Engine
Uses TF-IDF vectorization + K-Nearest Neighbors (cosine similarity)
"""
import re
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import MinMaxScaler


class MedicineRecommender:
    """
    ML-powered medicine recommendation engine.
    - TF-IDF on medicine name + generic + presentation + description
    - KNN with cosine distance for similarity matching
    - Prescription text parsing with regex + fuzzy matching
    """

    COMMON_MEDICINE_PATTERNS = [
        r'\b([A-Z][a-z]+(?:icin|mycin|oxacin|cillin|prazole|statin|sartan|olol|dipine|formin|zepam|pam|mab|nib))\b',
        r'\b([A-Z][a-z]+)\s+(\d+\s*(?:mg|ml|mcg|g|iu))\b',
        r'(?:Tab(?:let)?|Cap(?:sule)?|Syr(?:up)?|Inj(?:ection)?)\s+([A-Z][a-zA-Z]+)',
        r'\b([A-Z][a-z]{3,})\b',
    ]

    SYMPTOM_MAP = {
        'fever': ['paracetamol', 'ibuprofen', 'aspirin', 'crocin', 'dolo'],
        'pain': ['ibuprofen', 'diclofenac', 'paracetamol', 'naproxen'],
        'cold': ['cetirizine', 'loratadine', 'chlorphenamine', 'antihistamine'],
        'cough': ['dextromethorphan', 'ambroxol', 'guaifenesin', 'bromhexine'],
        'infection': ['amoxicillin', 'azithromycin', 'ciprofloxacin', 'doxycycline'],
        'acidity': ['omeprazole', 'pantoprazole', 'ranitidine', 'antacid'],
        'diabetes': ['metformin', 'glipizide', 'insulin', 'sitagliptin'],
        'blood pressure': ['amlodipine', 'atenolol', 'losartan', 'enalapril'],
        'cholesterol': ['atorvastatin', 'rosuvastatin', 'simvastatin'],
        'allergy': ['cetirizine', 'loratadine', 'fexofenadine', 'antihistamine'],
        'asthma': ['salbutamol', 'ipratropium', 'budesonide', 'montelukast'],
        'anxiety': ['alprazolam', 'diazepam', 'clonazepam'],
        'vitamin': ['vitamin c', 'vitamin d', 'vitamin b', 'multivitamin'],
        'headache': ['paracetamol', 'ibuprofen', 'diclofenac', 'crocin'],
        'migraine': ['sumatriptan', 'naproxen', 'paracetamol'],
        'stomach pain': ['dicyclomine', 'pantoprazole', 'antacid'],
        'gas': ['pantoprazole', 'omeprazole', 'antacid', 'simethicone'],
        'vomiting': ['ondansetron', 'domperidone', 'oral rehydration'],
        'nausea': ['ondansetron', 'domperidone', 'pantoprazole'],
        'loose motion': ['loperamide', 'oral rehydration', 'probiotic'],
        'diarrhea': ['loperamide', 'oral rehydration', 'metronidazole', 'probiotic'],
        'constipation': ['lactulose', 'ispaghula', 'bisacodyl'],
        'acne': ['clindamycin', 'benzoyl peroxide', 'adapalene'],
        'skin infection': ['clotrimazole', 'mupirocin', 'fusidic acid'],
        'fungal infection': ['clotrimazole', 'fluconazole', 'terbinafine'],
        'eye irritation': ['carboxymethylcellulose', 'moxifloxacin', 'olopatadine'],
        'ear pain': ['ciprofloxacin ear drops', 'paracetamol', 'ibuprofen'],
        'sore throat': ['amoxicillin', 'azithromycin', 'cetirizine', 'paracetamol'],
        'joint pain': ['diclofenac', 'aceclofenac', 'ibuprofen', 'calcium'],
        'tooth pain': ['ibuprofen', 'diclofenac', 'paracetamol'],
        'bp': ['amlodipine', 'losartan', 'atenolol', 'telmisartan'],
        'sugar': ['metformin', 'glimepiride', 'insulin', 'sitagliptin'],
        'sleep': ['melatonin', 'clonazepam', 'alprazolam'],
    }

    def _load_medicines(self):
        """Load medicines from database as DataFrame"""
        try:
            from pharma_django.pharmacy_app.models import Medicine
            meds = Medicine.objects.select_related('generic_name', 'presentation', 'supplier').all()
            if not meds.exists():
                return pd.DataFrame()

            records = []
            for m in meds:
                records.append({
                    'id': m.id,
                    'name': m.name,
                    'generic_name': m.generic_name.name if m.generic_name else '',
                    'presentation': m.presentation.name if m.presentation else '',
                    'description': m.description or '',
                    'selling_price': float(m.selling_price),
                    'quantity': m.quantity,
                    'volume': m.volume or '',
                    'supplier': m.supplier.company_name if m.supplier else '',
                    'expire_date': str(m.expire_date) if m.expire_date else '',
                    'stock_status': m.stock_status,
                })
            return pd.DataFrame(records)
        except Exception:
            return pd.DataFrame()

    def _build_corpus(self, df: pd.DataFrame) -> list:
        """Build combined text corpus for TF-IDF"""
        corpus = []
        for _, row in df.iterrows():
            text = ' '.join([
                row['name'],
                row['name'],  # doubled for higher weight
                row['generic_name'],
                row['generic_name'],
                row['presentation'],
                row['description'],
                row['volume'],
            ]).lower()
            corpus.append(text)
        return corpus

    def recommend(self, query: str, n: int = 8) -> list:
        """
        Find top-N similar medicines to the query.
        Returns list of dicts with medicine info + similarity score.
        """
        # Check if query is a symptom
        query_lower = query.lower()
        for symptom, keywords in self.SYMPTOM_MAP.items():
            if symptom in query_lower:
                # Expand query with related keywords
                query = query + ' ' + ' '.join(keywords)
                break

        df = self._load_medicines()
        if df.empty:
            return []

        corpus = self._build_corpus(df)

        try:
            vectorizer = TfidfVectorizer(
                ngram_range=(1, 3),
                max_features=2000,
                min_df=1,
                analyzer='word',
                sublinear_tf=True,
            )
            tfidf_matrix = vectorizer.fit_transform(corpus)
            query_vec = vectorizer.transform([query.lower()])

            k = min(n, len(df))
            nn = NearestNeighbors(n_neighbors=k, metric='cosine', algorithm='brute')
            nn.fit(tfidf_matrix)
            distances, indices = nn.kneighbors(query_vec)

            results = []
            for dist, idx in zip(distances[0], indices[0]):
                similarity = round((1 - dist) * 100, 1)
                row = df.iloc[idx]
                results.append({
                    'id': int(row['id']),
                    'name': row['name'],
                    'generic_name': row['generic_name'],
                    'presentation': row['presentation'],
                    'selling_price': row['selling_price'],
                    'quantity': int(row['quantity']),
                    'volume': row['volume'],
                    'supplier': row['supplier'],
                    'stock_status': row['stock_status'],
                    'similarity': similarity,
                })

            # Sort by similarity desc, filter low similarity
            results = sorted(results, key=lambda x: x['similarity'], reverse=True)
            return [r for r in results if r['similarity'] > 5][:n]

        except Exception as e:
            return []

    def extract_from_prescription(self, text: str):
        """
        Extract medicine names from prescription text using regex patterns.
        Returns (extracted_medicines, recommendations)
        """
        if not text or not text.strip():
            return [], []

        extracted = set()

        # Pattern 1: Medicine with dosage
        pattern1 = re.findall(r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)\s+\d+\s*(?:mg|ml|mcg|g|IU)', text)
        extracted.update([p.strip() for p in pattern1 if len(p) > 3])

        # Pattern 2: Tab/Cap/Syrup prefix
        pattern2 = re.findall(r'(?:Tab|Cap|Syr|Inj|Oint|Gel|Drops?)\s*\.?\s*([A-Z][a-zA-Z\s]+?)(?:\d|\n|,|\.|$)', text)
        extracted.update([p.strip() for p in pattern2 if len(p.strip()) > 3])

        # Pattern 3: Capitalized words likely to be medicines
        pattern3 = re.findall(r'\b([A-Z][a-z]{3,}(?:\s+[A-Z][a-z]{2,})?)\b', text)
        # Filter by length and common medicine suffixes
        med_suffixes = ('cin', 'mycin', 'cillin', 'prazole', 'statin', 'sartan', 'olol',
                        'dipine', 'formin', 'zepam', 'mab', 'nib', 'fenac', 'gesic',
                        'cef', 'dryl', 'fen', 'sol', 'pen', 'dol')
        for word in pattern3:
            if any(word.lower().endswith(s) for s in med_suffixes):
                extracted.add(word.strip())

        extracted = list(extracted)[:10]

        # Get recommendations for each extracted medicine
        all_recs = []
        seen_ids = set()
        for med_name in extracted[:5]:
            recs = self.recommend(med_name, n=3)
            for r in recs:
                if r['id'] not in seen_ids:
                    seen_ids.add(r['id'])
                    r['for_medicine'] = med_name
                    all_recs.append(r)

        return extracted, all_recs[:12]

    def get_stock_based_alternatives(self, medicine_id: int, n: int = 5) -> list:
        """
        Given a medicine that may be out of stock,
        suggest in-stock alternatives with similar generic/presentation.
        """
        try:
            from pharma_django.pharmacy_app.models import Medicine
            source = Medicine.objects.select_related('generic_name', 'presentation').get(pk=medicine_id)
            query = f"{source.name} {source.generic_name.name if source.generic_name else ''}"
            results = self.recommend(query, n=n + 1)
            # Filter out the source medicine and out-of-stock
            return [r for r in results if r['id'] != medicine_id and r['quantity'] > 0][:n]
        except Exception:
            return []
