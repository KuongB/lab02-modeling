"""
Main Pipeline
Orchestrates the entire data processing and ML pipeline
"""
import re
import json
import shutil
from pathlib import Path
from typing import Dict, List
from tqdm import tqdm

from config import SAMPLE_DIR, OUTPUT_DIR
from utils import load_json_safe, write_json_safe
from latex_parser import parse_version_directory
from latex_cleaner import clean_latex_content
from hierarchy_builder import build_hierarchy_from_versions
from bibtex_processor import process_publication_references, write_refs_bib
from reference_matching import ReferenceMatchingModel, compute_mrr


class Pipeline:
    """Main processing pipeline"""
    
    def __init__(self, sample_dir: Path, output_dir: Path):
        """
        Initialize pipeline
        
        Args:
            sample_dir: Path to sample directory
            output_dir: Path to output directory (MSSV folder)
        """
        self.sample_dir = Path(sample_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def get_publication_ids(self) -> List[str]:
        """Get list of all publication IDs in sample directory"""
        pub_ids = []
        
        for pub_dir in self.sample_dir.iterdir():
            if pub_dir.is_dir() and re.match(r'\d{4}-\d{5}', pub_dir.name):
                pub_ids.append(pub_dir.name)
        
        return sorted(pub_ids)
    
    def process_publication(self, pub_id: str) -> bool:
        """
        Process a single publication
        
        Args:
            pub_id: Publication ID (e.g., '2310-15395')
            
        Returns:
            True if successful
        """
        print(f"\nProcessing {pub_id}...")
        
        pub_dir = self.sample_dir / pub_id
        output_pub_dir = self.output_dir / pub_id
        output_pub_dir.mkdir(exist_ok=True)
        
        try:
            # 1. Copy metadata.json and references.json
            for filename in ['metadata.json', 'references.json']:
                src = pub_dir / filename
                dst = output_pub_dir / filename
                if src.exists():
                    shutil.copy2(src, dst)
                    print(f"  ✓ Copied {filename}")
            
            # 2. Process all versions
            tex_dir = pub_dir / 'tex'
            if not tex_dir.exists():
                print(f"  ✗ No tex directory found")
                return False
            
            versions_data = {}
            for version_dir in tex_dir.iterdir():
                if not version_dir.is_dir():
                    continue
                
                version_name = version_dir.name  # e.g., '2310-15395v1'
                # Extract version number
                version_match = re.search(r'v(\d+)', version_name)
                if version_match:
                    version = version_match.group(1)
                else:
                    continue
                
                print(f"  Processing {version_name}...")
                
                # Parse LaTeX
                parsed_data = parse_version_directory(version_dir)
                
                if parsed_data['body']:
                    # Clean content
                    cleaned_body = clean_latex_content(parsed_data['body'])
                    parsed_data['body'] = cleaned_body
                    
                    versions_data[version] = parsed_data
                    print(f"    ✓ Parsed {version_name}")
            
            # 3. Build hierarchy
            if versions_data:
                hierarchy_data = build_hierarchy_from_versions(pub_id, versions_data)
                
                # Write hierarchy.json
                hierarchy_path = output_pub_dir / 'hierarchy.json'
                if write_json_safe(hierarchy_data, hierarchy_path):
                    print(f"  ✓ Created hierarchy.json")
            
            # 4. Process BibTeX references
            bib_data = process_publication_references(pub_dir)
            
            if bib_data['entries']:
                # Write refs.bib
                refs_bib_path = output_pub_dir / 'refs.bib'
                write_refs_bib(bib_data['entries'], refs_bib_path)
                print(f"  ✓ Created refs.bib with {len(bib_data['entries'])} entries")
            
            return True
            
        except Exception as e:
            print(f"  ✗ Error processing {pub_id}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def process_all_publications(self):
        """Process all publications in sample directory"""
        pub_ids = self.get_publication_ids()
        
        print(f"Found {len(pub_ids)} publications to process")
        
        successful = 0
        failed = 0
        
        for pub_id in tqdm(pub_ids, desc="Processing publications"):
            if self.process_publication(pub_id):
                successful += 1
            else:
                failed += 1
        
        print(f"\n{'='*60}")
        print(f"Processing complete!")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"{'='*60}")
    
    def prepare_ml_data(self, manual_labels_path: Path, auto_label_count: int = None):
        """
        Prepare data for ML training
        
        Args:
            manual_labels_path: Path to manual labels JSON file
            auto_label_count: Number of publications to auto-label
        """
        print("\nPreparing ML training data...")
        
        # Load manual labels
        manual_labels = load_json_safe(manual_labels_path)
        
        if not manual_labels:
            print("No manual labels found. Please create manual labels first.")
            return
        
        # TODO: Implement auto-labeling using heuristics
        # TODO: Split data into train/valid/test
        # TODO: Train model
        # TODO: Generate predictions
        
        print("ML data preparation complete!")
    
    def train_and_evaluate_ml_model(self):
        """Train ML model and evaluate on test set"""
        print("\nTraining ML model...")
        
        # Load all processed publications
        pub_ids = [p.name for p in self.output_dir.iterdir() if p.is_dir()]
        
        all_bib_entries = []
        all_references = {}
        
        for pub_id in pub_ids:
            pub_dir = self.output_dir / pub_id
            
            # Load refs.bib
            refs_bib = pub_dir / 'refs.bib'
            if refs_bib.exists():
                # Parse BibTeX entries
                from bibtex_processor import BibTeXParser
                parser = BibTeXParser()
                entries = parser.parse_bib_file(refs_bib)
                all_bib_entries.extend([(pub_id, e) for e in entries])
            
            # Load references.json
            refs_json = pub_dir / 'references.json'
            if refs_json.exists():
                refs_data = load_json_safe(refs_json)
                if refs_data:
                    all_references[pub_id] = refs_data
        
        print(f"  Total BibTeX entries: {len(all_bib_entries)}")
        print(f"  Total publications with references: {len(all_references)}")
        
        # TODO: Load ground truth labels
        # TODO: Create training data
        # TODO: Train model
        # TODO: Generate predictions for test set
        # TODO: Compute MRR
        
        print("ML training complete!")


def main():
    """Main entry point"""
    import re
    
    print("="*60)
    print("Lab 02 - Modeling Pipeline")
    print("="*60)
    
    # Initialize pipeline
    pipeline = Pipeline(SAMPLE_DIR, OUTPUT_DIR)
    
    # Process all publications
    pipeline.process_all_publications()
    
    # TODO: Train ML model after manual labeling
    # pipeline.train_and_evaluate_ml_model()


if __name__ == '__main__':
    main()
