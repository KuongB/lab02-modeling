"""
Automatic Labeling Module
Generate labels automatically using heuristics for reference matching
"""
import re
import json
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from reference_matching import ReferenceFeatureExtractor


class AutoLabeler:
    """Generate automatic labels using heuristics"""
    
    def __init__(self, threshold_title: float = 0.9, threshold_author: float = 0.5):
        """
        Initialize auto-labeler
        
        Args:
            threshold_title: Title similarity threshold for automatic match
            threshold_author: Author similarity threshold for automatic match
        """
        self.feature_extractor = ReferenceFeatureExtractor()
        self.threshold_title = threshold_title
        self.threshold_author = threshold_author
    
    def extract_arxiv_id_from_bibtex(self, bib_entry: Dict) -> Optional[str]:
        """
        Extract arXiv ID from BibTeX entry using regex
        
        Args:
            bib_entry: BibTeX entry dictionary
            
        Returns:
            arXiv ID if found, None otherwise
        """
        # Check all fields for arXiv ID pattern
        arxiv_patterns = [
            r'arXiv:(\d{4}\.\d{4,5})',  # arXiv:YYMM.NNNNN
            r'arxiv\.org/abs/(\d{4}\.\d{4,5})',  # Full URL
            r'eprint["\']?\s*[=:]\s*["\']?(\d{4}\.\d{4,5})',  # eprint field with various formats
            r'(\d{4}\.\d{4,5})',  # Bare format YYMM.NNNNN
        ]
        
        # Combine all text from entry fields
        entry_text = json.dumps(bib_entry.fields) if hasattr(bib_entry, 'fields') else json.dumps(bib_entry)
        
        for pattern in arxiv_patterns:
            match = re.search(pattern, entry_text, re.IGNORECASE)
            if match:
                arxiv_id = match.group(1)
                # Validate format (should be YYMM.NNNNN where YY >= 07 for arXiv)
                if re.match(r'[0-9]{4}\.[0-9]{4,5}$', arxiv_id):
                    return arxiv_id
        
        return None
    
    def find_best_match(self, bib_entry, ref_entries_dict: Dict[str, Dict]) -> Optional[Tuple[str, float, str]]:
        """
        Find best matching reference for a BibTeX entry
        
        Args:
            bib_entry: BibTeX entry (BibEntry object or dict)
            ref_entries_dict: Dictionary of arxiv_id -> reference entry
            
        Returns:
            (arxiv_id, confidence_score, method) if match found, None otherwise
            method can be: 'arxiv_id_regex', 'high_similarity', 'moderate_similarity'
        """
        # Method 1: Direct arXiv ID match using regex
        arxiv_id_from_bib = self.extract_arxiv_id_from_bibtex(bib_entry)
        if arxiv_id_from_bib and arxiv_id_from_bib in ref_entries_dict:
            return (arxiv_id_from_bib, 1.0, 'arxiv_id_regex')
        
        # Method 2: Similarity-based matching
        best_match = None
        best_score = 0.0
        best_method = None
        
        bib_title = bib_entry.fields.get('title', '')
        bib_authors = bib_entry.fields.get('author', '')
        
        if isinstance(bib_authors, str):
            bib_authors = [a.strip() for a in bib_authors.split(' and ')]
        
        for arxiv_id, ref_entry in ref_entries_dict.items():
            ref_title = ref_entry.get('title', '')
            ref_authors = ref_entry.get('authors', [])
            
            if isinstance(ref_authors, str):
                ref_authors = [a.strip() for a in ref_authors.split(',')]
            
            # Compute title similarity
            if bib_title and ref_title:
                bib_tokens = self.feature_extractor.tokenize(bib_title)
                ref_tokens = self.feature_extractor.tokenize(ref_title)
                title_sim = self.feature_extractor.token_overlap_ratio(bib_tokens, ref_tokens)
                
                # Also check Levenshtein
                norm_bib_title = self.feature_extractor.normalize_string(bib_title)
                norm_ref_title = self.feature_extractor.normalize_string(ref_title)
                lev_sim = self.feature_extractor.normalized_levenshtein(norm_bib_title, norm_ref_title)
                
                # Take max of two similarity measures
                title_score = max(title_sim, lev_sim)
            else:
                title_score = 0.0
            
            # Compute author similarity
            author_score = self.feature_extractor.author_similarity(bib_authors, ref_authors)
            
            # Combined score (weighted)
            combined_score = 0.7 * title_score + 0.3 * author_score
            
            if combined_score > best_score:
                best_score = combined_score
                best_match = arxiv_id
                
                # Determine confidence method
                if title_score >= self.threshold_title and author_score >= self.threshold_author:
                    best_method = 'high_similarity'
                elif combined_score >= 0.7:
                    best_method = 'moderate_similarity'
        
        # Return match only if confidence is high enough
        if best_method in ['high_similarity', 'moderate_similarity']:
            return (best_match, best_score, best_method)
        
        return None
    
    def generate_labels_for_publication(self, pub_id: str, bib_entries: List[Dict], 
                                       ref_entries_dict: Dict[str, Dict]) -> Dict:
        """
        Generate automatic labels for one publication
        
        Args:
            pub_id: Publication ID
            bib_entries: List of BibTeX entries
            ref_entries_dict: Dictionary of arxiv_id -> reference entry
            
        Returns:
            Labels dictionary with groundtruth and metadata
        """
        labels = {
            'pub_id': pub_id,
            'groundtruth': {},
            'metadata': {
                'total_bibtex_entries': len(bib_entries),
                'total_references': len(ref_entries_dict),
                'matched_count': 0,
                'confidence_distribution': {
                    'arxiv_id_regex': 0,
                    'high_similarity': 0,
                    'moderate_similarity': 0
                }
            }
        }
        
        for bib_entry in bib_entries:
            bib_key = bib_entry.cite_key
            if not bib_key:
                continue
            
            match_result = self.find_best_match(bib_entry, ref_entries_dict)
            
            if match_result:
                arxiv_id, confidence, method = match_result
                labels['groundtruth'][bib_key] = arxiv_id
                labels['metadata']['matched_count'] += 1
                labels['metadata']['confidence_distribution'][method] += 1
        
        return labels
    
    def auto_label_publications(self, pub_dirs: List[Path], output_dir: Path) -> List[str]:
        """
        Generate automatic labels for multiple publications
        
        Args:
            pub_dirs: List of publication directories
            output_dir: Directory to save labels
            
        Returns:
            List of successfully labeled publication IDs
        """
        from bibtex_processor import BibTeXParser
        from utils import load_json_safe, save_json_safe
        
        output_dir.mkdir(exist_ok=True, parents=True)
        
        # Check for existing manual labels to avoid conflicts
        manual_labels_dir = output_dir.parent / 'manual'
        manual_labeled_pubs = set()
        if manual_labels_dir.exists():
            for label_file in manual_labels_dir.glob('*_labels.json'):
                # Extract pub_id from filename (format: {pub_id}_labels.json)
                pub_id = label_file.stem.replace('_labels', '').replace('_auto_labels', '')
                manual_labeled_pubs.add(pub_id)
        
        if manual_labeled_pubs:
            print(f"\nFound {len(manual_labeled_pubs)} publications with manual labels - will skip those")
        
        parser = BibTeXParser()
        labeled_pubs = []
        
        print(f"\nAuto-labeling {len(pub_dirs)} publications...")
        
        for pub_dir in pub_dirs:
            pub_id = pub_dir.name
            
            # Skip if manual labels exist
            if pub_id in manual_labeled_pubs:
                print(f"  Skipped {pub_id}: Manual labels already exist")
                continue
            
            # Load BibTeX entries
            refs_bib = pub_dir / 'refs.bib'
            if not refs_bib.exists():
                print(f"  Skipping {pub_id}: No refs.bib found")
                continue
            
            bib_entries = parser.parse_bib_file(refs_bib)
            if not bib_entries:
                print(f"  Skipping {pub_id}: No BibTeX entries parsed")
                continue
            
            # Load references.json
            refs_json = pub_dir / 'references.json'
            if not refs_json.exists():
                print(f"  Skipping {pub_id}: No references.json found")
                continue
            
            refs_data = load_json_safe(refs_json)
            if not refs_data:
                print(f"  Skipping {pub_id}: Invalid references.json")
                continue
            
            # references.json is already a dict of arxiv_id -> entry
            ref_entries_dict = refs_data
            
            if not ref_entries_dict:
                print(f"  Skipping {pub_id}: No arxiv_id references found")
                continue
            
            # Generate labels
            labels = self.generate_labels_for_publication(pub_id, bib_entries, ref_entries_dict)
            
            matched = labels['metadata']['matched_count']
            total = labels['metadata']['total_bibtex_entries']
            
            if matched > 0:
                # Save labels
                output_file = output_dir / f"{pub_id}_auto_labels.json"
                save_json_safe(labels, output_file)
                labeled_pubs.append(pub_id)
                
                print(f"  [OK] {pub_id}: Matched {matched}/{total} entries")
                
                # Show confidence distribution
                dist = labels['metadata']['confidence_distribution']
                print(f"    - Regex: {dist['arxiv_id_regex']}, High: {dist['high_similarity']}, Moderate: {dist['moderate_similarity']}")
            else:
                print(f"  [!] {pub_id}: No matches found")
        
        print(f"\nAuto-labeling complete: {len(labeled_pubs)} publications labeled")
        
        return labeled_pubs


if __name__ == '__main__':
    """Test auto-labeling on sample publications"""
    from pathlib import Path
    
    # Test parameters
    output_base = Path('../output')
    labels_output = Path('../labels/auto')
    
    # Get all publication directories
    pub_dirs = [d for d in output_base.iterdir() if d.is_dir()]
    
    # Auto-label first 10% of publications (or at least 3)
    num_to_label = max(3, int(len(pub_dirs) * 0.1))
    pubs_to_label = pub_dirs[:num_to_label]
    
    # Run auto-labeling
    labeler = AutoLabeler(threshold_title=0.9, threshold_author=0.5)
    labeled_pubs = labeler.auto_label_publications(pubs_to_label, labels_output)
    
    print(f"\n{'='*70}")
    print(f"Successfully labeled {len(labeled_pubs)} publications:")
    for pub_id in labeled_pubs:
        print(f"  - {pub_id}")
