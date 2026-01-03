"""
Reference Matching Module
Machine Learning pipeline for matching BibTeX entries to arXiv IDs
"""
import re
import json
import numpy as np
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from collections import defaultdict


class ReferenceFeatureExtractor:
    """Extract features for reference matching"""
    
    def __init__(self):
        """Initialize feature extractor"""
        self.stop_words = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'])
    
    def normalize_string(self, text: str) -> str:
        """Normalize string for comparison"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def tokenize(self, text: str) -> List[str]:
        """Tokenize text into words"""
        normalized = self.normalize_string(text)
        tokens = normalized.split()
        
        # Remove stop words
        tokens = [t for t in tokens if t not in self.stop_words]
        
        return tokens
    
    def jaccard_similarity(self, set1: set, set2: set) -> float:
        """Compute Jaccard similarity between two sets"""
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def token_overlap_ratio(self, tokens1: List[str], tokens2: List[str]) -> float:
        """Compute token overlap ratio"""
        set1 = set(tokens1)
        set2 = set(tokens2)
        
        return self.jaccard_similarity(set1, set2)
    
    def levenshtein_distance(self, s1: str, s2: str) -> int:
        """Compute Levenshtein distance between two strings"""
        if len(s1) < len(s2):
            return self.levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def normalized_levenshtein(self, s1: str, s2: str) -> float:
        """Normalized Levenshtein similarity (0 to 1)"""
        distance = self.levenshtein_distance(s1, s2)
        max_len = max(len(s1), len(s2))
        
        return 1.0 - (distance / max_len) if max_len > 0 else 1.0
    
    def author_similarity(self, authors1: List[str], authors2: List[str]) -> float:
        """
        Compute similarity between author lists
        
        Args:
            authors1: List of author names
            authors2: List of author names
            
        Returns:
            Similarity score (0 to 1)
        """
        if not authors1 or not authors2:
            return 0.0
        
        # Normalize author names
        norm_authors1 = [self.normalize_string(a) for a in authors1]
        norm_authors2 = [self.normalize_string(a) for a in authors2]
        
        # Check for exact matches
        set1 = set(norm_authors1)
        set2 = set(norm_authors2)
        
        exact_matches = len(set1 & set2)
        total_authors = max(len(set1), len(set2))
        
        exact_score = exact_matches / total_authors if total_authors > 0 else 0.0
        
        # Check for partial matches (last names)
        def get_last_name(name: str) -> str:
            parts = name.split()
            return parts[-1] if parts else ""
        
        last_names1 = set([get_last_name(a) for a in norm_authors1])
        last_names2 = set([get_last_name(a) for a in norm_authors2])
        
        partial_matches = len(last_names1 & last_names2)
        partial_score = partial_matches / total_authors if total_authors > 0 else 0.0
        
        # Weighted combination
        return 0.7 * exact_score + 0.3 * partial_score
    
    def year_similarity(self, year1: Optional[str], year2: Optional[str]) -> float:
        """
        Compute similarity between years
        
        Args:
            year1: Year string
            year2: Year string
            
        Returns:
            1.0 if same year, 0.5 if within 1 year, 0.0 otherwise
        """
        if not year1 or not year2:
            return 0.0
        
        try:
            y1 = int(re.search(r'\d{4}', year1).group())
            y2 = int(re.search(r'\d{4}', year2).group())
            
            diff = abs(y1 - y2)
            if diff == 0:
                return 1.0
            elif diff == 1:
                return 0.5
            else:
                return 0.0
        except:
            return 0.0
    
    def extract_features(self, bib_entry: Dict, ref_entry: Dict) -> np.ndarray:
        """
        Extract feature vector for a (bib_entry, ref_entry) pair
        
        Args:
            bib_entry: BibTeX entry dictionary
            ref_entry: Reference entry from references.json
            
        Returns:
            Feature vector
        """
        features = []
        
        # Title similarity features
        bib_title = bib_entry.get('title', '')
        ref_title = ref_entry.get('title', '')
        
        if bib_title and ref_title:
            # Token overlap
            bib_tokens = self.tokenize(bib_title)
            ref_tokens = self.tokenize(ref_title)
            token_overlap = self.token_overlap_ratio(bib_tokens, ref_tokens)
            features.append(token_overlap)
            
            # Normalized Levenshtein
            norm_bib_title = self.normalize_string(bib_title)
            norm_ref_title = self.normalize_string(ref_title)
            lev_sim = self.normalized_levenshtein(norm_bib_title, norm_ref_title)
            features.append(lev_sim)
            
            # Title length ratio
            len_ratio = min(len(bib_title), len(ref_title)) / max(len(bib_title), len(ref_title))
            features.append(len_ratio)
        else:
            features.extend([0.0, 0.0, 0.0])
        
        # Author similarity
        bib_authors = bib_entry.get('authors', [])
        ref_authors = ref_entry.get('authors', [])
        
        if isinstance(bib_authors, str):
            bib_authors = [a.strip() for a in bib_authors.split(' and ')]
        if isinstance(ref_authors, str):
            ref_authors = [a.strip() for a in ref_authors.split(',')]
        
        author_sim = self.author_similarity(bib_authors, ref_authors)
        features.append(author_sim)
        
        # Author count difference
        author_count_diff = abs(len(bib_authors) - len(ref_authors))
        features.append(min(author_count_diff, 10) / 10.0)  # Normalize to 0-1
        
        # Year similarity
        bib_year = bib_entry.get('year', '') or bib_entry.get('submitted_date', '')
        ref_year = ref_entry.get('submitted_date', '')
        year_sim = self.year_similarity(bib_year, ref_year)
        features.append(year_sim)
        
        # arXiv ID in BibTeX (strong indicator)
        bib_text = str(bib_entry)
        ref_arxiv_id = ref_entry.get('arxiv_id', '')
        has_arxiv_id = 1.0 if ref_arxiv_id and ref_arxiv_id in bib_text else 0.0
        features.append(has_arxiv_id)
        
        return np.array(features)


class ReferenceMatchingModel:
    """Simple ML model for reference matching"""
    
    def __init__(self):
        """Initialize model"""
        self.feature_extractor = ReferenceFeatureExtractor()
        self.model = None
        self.feature_names = [
            'title_token_overlap',
            'title_levenshtein',
            'title_length_ratio',
            'author_similarity',
            'author_count_diff',
            'year_similarity',
            'has_arxiv_id'
        ]
    
    def create_training_data(self, labeled_data: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create training data from labeled examples
        
        Args:
            labeled_data: List of {'bib_entry': {}, 'ref_entry': {}, 'label': 0/1}
            
        Returns:
            (X, y) feature matrix and labels
        """
        X = []
        y = []
        
        for example in labeled_data:
            features = self.feature_extractor.extract_features(
                example['bib_entry'],
                example['ref_entry']
            )
            X.append(features)
            y.append(example['label'])
        
        return np.array(X), np.array(y)
    
    def train(self, X: np.ndarray, y: np.ndarray):
        """
        Train the model
        
        Args:
            X: Feature matrix
            y: Labels
        """
        from sklearn.ensemble import RandomForestClassifier
        
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.model.fit(X, y)
    
    def predict_proba(self, bib_entry: Dict, ref_entries: List[Dict]) -> np.ndarray:
        """
        Predict probability for each reference
        
        Args:
            bib_entry: BibTeX entry
            ref_entries: List of reference entries
            
        Returns:
            Array of probabilities
        """
        X = []
        for ref_entry in ref_entries:
            features = self.feature_extractor.extract_features(bib_entry, ref_entry)
            X.append(features)
        
        X = np.array(X)
        
        if self.model is None:
            # If no model trained, use simple heuristic
            # Return sum of features as score
            return X.sum(axis=1) / len(self.feature_names)
        
        # Return probability of positive class
        return self.model.predict_proba(X)[:, 1]
    
    def rank_candidates(self, bib_entry: Dict, ref_entries_dict: Dict, 
                       top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Rank candidate references for a BibTeX entry
        
        Args:
            bib_entry: BibTeX entry
            ref_entries_dict: Dictionary of arxiv_id -> reference entry
            top_k: Number of top candidates to return
            
        Returns:
            List of (arxiv_id, score) tuples
        """
        arxiv_ids = list(ref_entries_dict.keys())
        ref_entries = [ref_entries_dict[aid] for aid in arxiv_ids]
        
        # Add arxiv_id to each entry for feature extraction
        for aid, entry in zip(arxiv_ids, ref_entries):
            entry['arxiv_id'] = aid
        
        scores = self.predict_proba(bib_entry, ref_entries)
        
        # Sort by score descending
        ranked_indices = np.argsort(scores)[::-1]
        
        top_candidates = []
        for idx in ranked_indices[:top_k]:
            top_candidates.append((arxiv_ids[idx], float(scores[idx])))
        
        return top_candidates


def compute_mrr(predictions: Dict[str, List[str]], ground_truth: Dict[str, str]) -> float:
    """
    Compute Mean Reciprocal Rank
    
    Args:
        predictions: Dict of bib_key -> list of top-5 arxiv_ids
        ground_truth: Dict of bib_key -> correct arxiv_id
        
    Returns:
        MRR score
    """
    reciprocal_ranks = []
    
    for bib_key, correct_id in ground_truth.items():
        if bib_key not in predictions:
            reciprocal_ranks.append(0.0)
            continue
        
        pred_list = predictions[bib_key]
        
        if correct_id in pred_list:
            rank = pred_list.index(correct_id) + 1  # 1-indexed
            reciprocal_ranks.append(1.0 / rank)
        else:
            reciprocal_ranks.append(0.0)
    
    return np.mean(reciprocal_ranks) if reciprocal_ranks else 0.0
