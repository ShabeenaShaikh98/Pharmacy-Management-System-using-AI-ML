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
from difflib import SequenceMatcher


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

    DOSAGE_PATTERN = re.compile(r'\b\d+\s*(?:mg|ml|mcg|g|iu)\b', re.IGNORECASE)
    FORM_WORDS = {
        'tab', 'tablet', 'cap', 'capsule', 'syr', 'syrup', 'inj', 'injection',
        'oint', 'ointment', 'gel', 'drop', 'drops', 'cream', 'powder',
    }

    def _load_medicines(self):
        """Load medicines from database as DataFrame"""
        try:
            from pharmacy_app.models import Medicine
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

    def _normalize_prescription_text(self, text: str) -> str:
        text = (text or '').lower()
        text = self.DOSAGE_PATTERN.sub(' ', text)
        text = re.sub(r'[^a-z0-9\s\-\+]', ' ', text)
        parts = [part for part in text.split() if part not in self.FORM_WORDS]
        return ' '.join(parts).strip()

    def _load_catalog(self):
        try:
            from pharmacy_app.models import Medicine
            return list(Medicine.objects.select_related('generic_name', 'presentation').all())
        except Exception:
            return []

    def _find_best_catalog_match(self, candidate: str):
        normalized = self._normalize_prescription_text(candidate)
        if not normalized:
            return None

        best_match = None
        best_score = 0.0
        for medicine in self._load_catalog():
            medicine_name = self._normalize_prescription_text(medicine.name)
            generic_name = self._normalize_prescription_text(getattr(medicine.generic_name, 'name', ''))
            names_to_check = [('medicine', medicine_name), ('generic', generic_name)]
            names_to_check = [(kind, name) for kind, name in names_to_check if name]
            if not names_to_check:
                continue

            for kind, name in names_to_check:
                is_demo_name = medicine.name.lower().startswith('pg demo medicine')
                if normalized == name:
                    if kind == 'medicine':
                        return {
                            'id': medicine.id,
                            'name': candidate.strip(),
                            'inventory_name': medicine.name,
                            'generic_name': medicine.generic_name.name if medicine.generic_name else '',
                            'presentation': medicine.presentation.name if medicine.presentation else '',
                            'matched_text': candidate.strip(),
                            'match_type': 'exact',
                            'score': 100.0,
                        }
                    score = 95.0
                    if is_demo_name:
                        score -= 12
                    if score > best_score:
                        best_score = score
                        best_match = {
                            'id': medicine.id,
                            'name': candidate.strip(),
                            'inventory_name': medicine.name,
                            'generic_name': medicine.generic_name.name if medicine.generic_name else '',
                            'presentation': medicine.presentation.name if medicine.presentation else '',
                            'matched_text': candidate.strip(),
                            'match_type': 'generic',
                            'score': round(score, 1),
                        }
                    continue
                if normalized in name or name in normalized:
                    score = 96.0 if len(normalized) >= 4 else 88.0
                    if kind == 'generic':
                        score -= 6
                else:
                    score = SequenceMatcher(None, normalized, name).ratio() * 100
                    if kind == 'generic':
                        score -= 6
                if is_demo_name:
                    score -= 12

                if score > best_score:
                    best_score = score
                    best_match = {
                        'id': medicine.id,
                        'name': candidate.strip(),
                        'inventory_name': medicine.name,
                        'generic_name': medicine.generic_name.name if medicine.generic_name else '',
                        'presentation': medicine.presentation.name if medicine.presentation else '',
                        'matched_text': candidate.strip(),
                        'match_type': 'close',
                        'score': round(score, 1),
                    }

        if best_match and best_match['score'] >= 72:
            return best_match
        return None

    def _extract_candidates_from_lines(self, text: str):
        candidates = []
        for raw_line in (text or '').splitlines():
            line = raw_line.strip()
            if not line:
                continue
            line = re.sub(r'^\s*\d+[\)\.\-]?\s*', '', line)
            line = re.sub(r'^(?:rx|medicine|medicines)\s*[:\-]?\s*', '', line, flags=re.IGNORECASE)
            if not line:
                continue

            direct_match = re.search(
                r'(?:tab(?:let)?|cap(?:sule)?|syr(?:up)?|inj(?:ection)?|oint(?:ment)?|gel|drops?|cream)\s+([A-Za-z][A-Za-z0-9\-\+ ]{1,60})',
                line,
                flags=re.IGNORECASE,
            )
            if direct_match:
                cleaned = direct_match.group(1)
                cleaned = re.split(r'\s+\-|\s+\(|\s+\d+\-\d+\-\d+|\s+tds|\s+bd|\s+od|\s+hs', cleaned, maxsplit=1, flags=re.IGNORECASE)[0]
                candidates.append(cleaned.strip())
                continue

            dosage_match = re.search(r'([A-Za-z][A-Za-z0-9\-\+ ]{1,60})\s+\d+\s*(?:mg|ml|mcg|g|iu)', line, flags=re.IGNORECASE)
            if dosage_match:
                candidates.append(dosage_match.group(1).strip())
                continue

            prefix = re.split(r'\-|\(|,', line, maxsplit=1)[0].strip()
            if len(prefix.split()) <= 4 and any(ch.isalpha() for ch in prefix):
                candidates.append(prefix)

        return candidates

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
            return [], [], []

        exact_matches = []
        extracted_names = []
        seen_medicine_ids = set()
        seen_names = set()

        candidates = self._extract_candidates_from_lines(text)
        for candidate in candidates:
            match = self._find_best_catalog_match(candidate)
            if not match:
                continue
            if match['id'] in seen_medicine_ids:
                continue
            seen_medicine_ids.add(match['id'])
            exact_matches.append(match)
            seen_names.add(match['name'].lower())
            extracted_names.append(match['name'])

        if not exact_matches:
            fallback_names = []
            pattern3 = re.findall(r'\b([A-Z][a-z]{3,}(?:\s+[A-Z][a-z]{2,})?)\b', text)
            for word in pattern3:
                match = self._find_best_catalog_match(word)
                if not match or match['id'] in seen_medicine_ids:
                    continue
                seen_medicine_ids.add(match['id'])
                exact_matches.append(match)
                extracted_names.append(match['name'])
                fallback_names.append(match['name'])
            if fallback_names:
                seen_names.update(name.lower() for name in fallback_names)

        all_recs = []
        seen_ids = set()
        for med_name in extracted_names[:5]:
            recs = self.recommend(med_name, n=3)
            for r in recs:
                if r['id'] not in seen_ids:
                    seen_ids.add(r['id'])
                    r['for_medicine'] = med_name
                    all_recs.append(r)
        return extracted_names[:10], exact_matches[:10], all_recs[:12]

    def get_stock_based_alternatives(self, medicine_id: int, n: int = 5) -> list:
        """
        Given a medicine that may be out of stock,
        suggest in-stock alternatives with similar generic/presentation.
        """
        try:
            from pharmacy_app.models import Medicine
            source = Medicine.objects.select_related('generic_name', 'presentation').get(pk=medicine_id)
            query = f"{source.name} {source.generic_name.name if source.generic_name else ''}"
            results = self.recommend(query, n=n + 1)
            # Filter out the source medicine and out-of-stock
            return [r for r in results if r['id'] != medicine_id and r['quantity'] > 0][:n]
        except Exception:
            return []
