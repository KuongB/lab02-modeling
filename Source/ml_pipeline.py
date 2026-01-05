"""
ML Training Pipeline
Complete pipeline for training and evaluating reference matching model
"""
import json
import numpy as np
from typing import Dict, List, Tuple
from pathlib import Path
from collections import defaultdict
from reference_matching import ReferenceMatchingModel, compute_mrr
from utils import load_json_safe, save_json_safe


class MLPipeline:
    """Complete ML pipeline for reference matching"""
    
    def __init__(self, output_dir: Path, labels_dir: Path):
        """
        Initialize ML pipeline
        
        Args:
            output_dir: Directory containing processed publications
            labels_dir: Directory containing manual and auto labels
        """
        self.output_dir = Path(output_dir)
        self.labels_dir = Path(labels_dir)
        self.model = ReferenceMatchingModel()
        
        self.train_pubs = []
        self.valid_pubs = []
        self.test_pubs = []
    
    def load_all_labels(self) -> Dict[str, Dict]:
        """
        Load all labeled data (manual + auto)
        
        Returns:
            Dictionary mapping pub_id -> labels
        """
        all_labels = {}
        
        # Load manual labels
        manual_dir = self.labels_dir / 'manual'
        if manual_dir.exists():
            for label_file in manual_dir.glob('*_labels.json'):
                labels = load_json_safe(label_file)
                if labels and 'pub_id' in labels:
                    pub_id = labels['pub_id']
                    # Ensure source is set correctly
                    if 'source' not in labels or labels['source'] != 'manual':
                        labels['source'] = 'manual'
                    all_labels[pub_id] = labels
                    print(f"  Loaded manual: {pub_id}")
        
        # Load auto labels (but don't overwrite manual labels)
        auto_dir = self.labels_dir / 'auto'
        if auto_dir.exists():
            for label_file in auto_dir.glob('*_auto_labels.json'):
                labels = load_json_safe(label_file)
                if labels and 'pub_id' in labels:
                    pub_id = labels['pub_id']
                    # Skip if manual label already exists for this pub
                    if pub_id not in all_labels:
                        # Ensure source is set correctly
                        if 'source' not in labels or labels['source'] != 'auto':
                            labels['source'] = 'auto'
                        all_labels[pub_id] = labels
                        print(f"  Loaded auto: {pub_id}")
                    else:
                        print(f"  Skipped auto: {pub_id} (manual exists)")
        
        return all_labels
    
    def split_data(self, all_labels: Dict[str, Dict]) -> Tuple[List[str], List[str], List[str]]:
        """
        Split data into train/valid/test sets
        
        Flexible splitting based on available labels:
        - Ideal: 3+ manual + 2+ auto (1+1 test, 1+1 valid, rest train)
        - Fallback: Use all available labels, split 60/20/20
        
        Args:
            all_labels: Dictionary of pub_id -> labels
            
        Returns:
            (train_pubs, valid_pubs, test_pubs)
        """
        manual_pubs = [pid for pid, labels in all_labels.items() if labels.get('source') == 'manual']
        auto_pubs = [pid for pid, labels in all_labels.items() if labels.get('source') == 'auto']
        
        print(f"\nData split:")
        print(f"  Manual labeled: {len(manual_pubs)} publications")
        print(f"  Auto labeled: {len(auto_pubs)} publications")
        
        all_pubs = list(all_labels.keys())
        
        # Check if we have enough data for training
        if len(all_pubs) < 2:
            raise ValueError(f"Need at least 2 labeled publications. Found {len(all_pubs)}")
        
        # Ideal case: enough manual and auto labels
        if len(manual_pubs) >= 3 and len(auto_pubs) >= 2:
            # Allocate test set
            test_pubs = [manual_pubs[0], auto_pubs[0]]
            
            # Allocate valid set
            valid_pubs = [manual_pubs[1], auto_pubs[1]]
            
            # Remaining for training
            train_pubs = manual_pubs[2:] + auto_pubs[2:]
            
            print(f"  Split strategy: Balanced (manual+auto)")
        
        # Fallback: split all available labels proportionally
        else:
            print(f"  Split strategy: Proportional (insufficient manual/auto balance)")
            
            # 60% train, 20% valid, 20% test
            n = len(all_pubs)
            n_test = max(1, int(n * 0.2))
            n_valid = max(1, int(n * 0.2))
            n_train = n - n_test - n_valid
            
            # Ensure at least 1 in train if possible
            if n_train == 0 and n >= 3:
                n_test = 1
                n_valid = 1
                n_train = n - 2
            
            test_pubs = all_pubs[:n_test]
            valid_pubs = all_pubs[n_test:n_test + n_valid]
            train_pubs = all_pubs[n_test + n_valid:]
        
        print(f"\nData split:")
        print(f"  Test: {len(test_pubs)} pubs")
        print(f"  Valid: {len(valid_pubs)} pubs")
        print(f"  Train: {len(train_pubs)} pubs")
        
        return train_pubs, valid_pubs, test_pubs
        
        return train_pubs, valid_pubs, test_pubs
    
    def create_training_pairs(self, pub_ids: List[str], all_labels: Dict[str, Dict]) -> List[Dict]:
        """
        Create all (bib_entry, ref_entry, label) pairs for training
        
        Following requirements: For each publication with m BibTeX entries and n references,
        create m × n pairs with binary labels.
        
        Args:
            pub_ids: List of publication IDs
            all_labels: All labels dictionary
            
        Returns:
            List of training examples
        """
        from bibtex_processor import BibTeXParser
        
        parser = BibTeXParser()
        training_examples = []
        
        for pub_id in pub_ids:
            pub_dir = self.output_dir / pub_id
            
            # Load BibTeX entries
            refs_bib = pub_dir / 'refs.bib'
            if not refs_bib.exists():
                continue
            
            bib_entries = parser.parse_bib_file(refs_bib)
            if not bib_entries:
                continue
            
            # Load references
            refs_json = pub_dir / 'references.json'
            if not refs_json.exists():
                continue
            
            refs_data = load_json_safe(refs_json)
            if not refs_data:
                continue
            
            # references.json is already a dict of arxiv_id -> entry
            ref_entries_dict = refs_data
            
            # Get groundtruth for this publication
            groundtruth = all_labels[pub_id].get('groundtruth', {})
            
            # Create m × n pairs
            for bib_entry in bib_entries:
                bib_key = bib_entry.cite_key
                if not bib_key:
                    continue
                
                correct_arxiv_id = groundtruth.get(bib_key)
                
                for arxiv_id, ref_entry in ref_entries_dict.items():
                    # Label: 1 if this is the correct match, 0 otherwise
                    label = 1 if arxiv_id == correct_arxiv_id else 0
                    
                    training_examples.append({
                        'pub_id': pub_id,
                        'bib_key': bib_key,
                        'arxiv_id': arxiv_id,
                        'bib_entry': bib_entry,
                        'ref_entry': ref_entry,
                        'label': label
                    })
        
        return training_examples
    
    def train_model(self, train_pubs: List[str], all_labels: Dict[str, Dict]):
        """
        Train the ML model
        
        Args:
            train_pubs: List of training publication IDs
            all_labels: All labels dictionary
        """
        print(f"\nTraining Model...")
        
        # Create training pairs
        training_examples = self.create_training_pairs(train_pubs, all_labels)
        
        positive = sum(1 for ex in training_examples if ex['label'] == 1)
        negative = len(training_examples) - positive
        print(f"  Training examples: {len(training_examples)} ({positive} positive, {negative} negative)")
        
        # Extract features and labels
        X, y = self.model.create_training_data(training_examples)
        print(f"  Features: {X.shape[1]} dimensions")
        
        # Train model
        self.model.train(X, y)
        print("[OK] Model trained")
    
    def evaluate_and_generate_predictions(self, eval_pubs: List[str], all_labels: Dict[str, Dict],
                                         partition_name: str) -> Dict[str, float]:
        """
        Evaluate model on a set of publications and generate predictions
        
        Args:
            eval_pubs: List of publication IDs to evaluate
            all_labels: All labels dictionary
            partition_name: 'train', 'valid', or 'test'
            
        Returns:
            Dictionary of metrics
        """
        from bibtex_processor import BibTeXParser
        
        parser = BibTeXParser()
        
        all_predictions = {}
        all_groundtruth = {}
        
        print(f"\nEvaluating {partition_name} set...")
        
        for pub_id in eval_pubs:
            pub_dir = self.output_dir / pub_id
            
            # Load BibTeX entries
            refs_bib = pub_dir / 'refs.bib'
            if not refs_bib.exists():
                continue
            
            bib_entries = parser.parse_bib_file(refs_bib)
            if not bib_entries:
                continue
            
            # Create dictionary keyed by bib_key
            bib_dict = {}
            for entry in bib_entries:
                bib_key = entry.cite_key
                if bib_key:
                    bib_dict[bib_key] = entry
            
            # Load references
            refs_json = pub_dir / 'references.json'
            if not refs_json.exists():
                continue
            
            refs_data = load_json_safe(refs_json)
            if not refs_data:
                continue
            
            # references.json is already a dict of arxiv_id -> entry
            ref_entries_dict = refs_data
            
            # Get groundtruth
            groundtruth = all_labels[pub_id].get('groundtruth', {})
            
            # Generate predictions for each BibTeX entry
            pub_predictions = {}
            pub_groundtruth = {}
            
            for bib_key, bib_entry in bib_dict.items():
                if bib_key not in groundtruth:
                    continue  # Skip entries without groundtruth
                
                # Rank candidates
                top_candidates = self.model.rank_candidates(bib_entry, ref_entries_dict, top_k=5)
                
                # Extract just the arxiv_ids
                candidate_ids = [arxiv_id for arxiv_id, score in top_candidates]
                
                pub_predictions[bib_key] = candidate_ids
                pub_groundtruth[bib_key] = groundtruth[bib_key]
            
            # Save pred.json for this publication
            pred_data = {
                'partition': partition_name,
                'groundtruth': pub_groundtruth,
                'prediction': pub_predictions
            }
            
            pred_file = pub_dir / 'pred.json'
            save_json_safe(pred_data, pred_file)
            
            # Accumulate for overall metrics
            all_predictions.update(pub_predictions)
            all_groundtruth.update(pub_groundtruth)
            
            # Compute MRR for this publication
            pub_mrr = compute_mrr(pub_predictions, pub_groundtruth)
            print(f"  {pub_id}: MRR = {pub_mrr:.4f} ({len(pub_groundtruth)} queries)")
        
        # Compute overall MRR
        overall_mrr = compute_mrr(all_predictions, all_groundtruth)
        
        print(f"\n{partition_name.upper()} SET: MRR = {overall_mrr:.4f} ({len(all_groundtruth)} queries)")
        
        return {
            'mrr': overall_mrr,
            'num_queries': len(all_groundtruth)
        }
    
    def run_full_pipeline(self):
        """Run complete ML pipeline"""
        print(f"\nML Training Pipeline")
        
        # Load all labels
        print("\nLoading labels...")
        all_labels = self.load_all_labels()
        
        if not all_labels:
            print("[X] No labels found! Please create labels first:")
            print("   1. Manual labels: Use manual_labeling_helper.py")
            print("   2. Auto labels: Run auto_labeling.py")
            return
        
        print(f"[OK] Loaded labels for {len(all_labels)} publications")
        
        # Split data
        train_pubs, valid_pubs, test_pubs = self.split_data(all_labels)
        
        self.train_pubs = train_pubs
        self.valid_pubs = valid_pubs
        self.test_pubs = test_pubs
        
        # Train model
        self.train_model(train_pubs, all_labels)
        
        # Evaluate on validation set
        valid_metrics = self.evaluate_and_generate_predictions(valid_pubs, all_labels, 'valid')
        
        # Evaluate on test set
        test_metrics = self.evaluate_and_generate_predictions(test_pubs, all_labels, 'test')
        
        # Also generate predictions for training set (for completeness)
        train_metrics = self.evaluate_and_generate_predictions(train_pubs, all_labels, 'train')
        
        # Final summary
        print(f"\nFinal Results:")
        print(f"  Train: {train_metrics['mrr']:.4f}")
        print(f"  Valid: {valid_metrics['mrr']:.4f}")
        print(f"  Test:  {test_metrics['mrr']:.4f}")
        print(f"\n[OK] ML pipeline complete!")
        print(f"Predictions saved to: output/{{pub_id}}/pred.json\n")


if __name__ == '__main__':
    """Run ML pipeline"""
    from pathlib import Path
    
    # Paths
    output_dir = Path('../output')
    labels_dir = Path('../labels')
    
    # Create and run pipeline
    pipeline = MLPipeline(output_dir, labels_dir)
    pipeline.run_full_pipeline()
