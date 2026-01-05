"""
Main Pipeline - Lab 02 Data Modeling
Process publications, create labels, and train ML model

Usage:
    python main.py                # Interactive menu
    python main.py --process      # Process all publications
    python main.py --auto-label   # Run auto-labeling
    python main.py --train        # Train ML model
    python main.py --full         # Run complete pipeline
    python main.py --status       # Show pipeline status
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
            output_dir: Path to output directory
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
            
            # 2. Process all versions
            tex_dir = pub_dir / 'tex'
            if not tex_dir.exists():
                return False
            
            versions_data = {}
            for version_dir in tex_dir.iterdir():
                if not version_dir.is_dir():
                    continue
                
                version_name = version_dir.name
                version_match = re.search(r'v(\d+)', version_name)
                if version_match:
                    version = version_match.group(1)
                else:
                    continue
                
                # Parse LaTeX
                parsed_data = parse_version_directory(version_dir)
                
                if parsed_data['body']:
                    # Clean content
                    cleaned_body = clean_latex_content(parsed_data['body'])
                    parsed_data['body'] = cleaned_body
                    versions_data[version] = parsed_data
            
            # 3. Build hierarchy
            if versions_data:
                hierarchy_data = build_hierarchy_from_versions(pub_id, versions_data)
                hierarchy_path = output_pub_dir / 'hierarchy.json'
                write_json_safe(hierarchy_data, hierarchy_path)
            
            # 4. Process BibTeX references
            bib_data = process_publication_references(pub_dir)
            
            if bib_data['entries']:
                refs_bib_path = output_pub_dir / 'refs.bib'
                write_refs_bib(bib_data['entries'], refs_bib_path)
            
            return True
            
        except Exception as e:
            return False
    
    def run(self, pub_id: str = None):
        """Run the data processing pipeline"""
        if pub_id:
            print(f"\nProcessing: {pub_id}")
            success = self.process_publication(pub_id)
            print(f"{'[OK]' if success else '[FAILED]'}")
        else:
            self.process_all_publications()
    
    def process_all_publications(self):
        """Process all publications in sample directory"""
        pub_ids = self.get_publication_ids()
        
        if not pub_ids:
            print("[ERROR] No publications found!")
            return
        
        print(f"\nProcessing {len(pub_ids)} publications...")
        
        successful = 0
        failed = 0
        
        for pub_id in tqdm(pub_ids, desc="Processing"):
            if self.process_publication(pub_id):
                successful += 1
            else:
                failed += 1
        
        print(f"Complete: {successful} successful, {failed} failed\n")
    
    def run_auto_labeling(self, num_pubs: int = None):
        """Run automatic labeling on publications"""
        from auto_labeling import AutoLabeler
        
        print("\nAuto-labeling publications...")
        
        # Get publications with data
        pub_dirs = []
        for pub_dir in self.output_dir.iterdir():
            if pub_dir.is_dir():
                if (pub_dir / 'refs.bib').exists() and (pub_dir / 'references.json').exists():
                    pub_dirs.append(pub_dir)
        
        if not pub_dirs:
            print("[ERROR] No publications with refs.bib and references.json found")
            return
        
        # Determine number to label
        if num_pubs is None:
            num_pubs = max(3, int(len(pub_dirs) * 0.1))
        
        num_pubs = min(num_pubs, len(pub_dirs))
        
        # Create labels directory
        labels_dir = self.output_dir.parent / 'labels' / 'auto'
        labels_dir.mkdir(exist_ok=True, parents=True)
        
        # Run auto-labeling
        labeler = AutoLabeler(threshold_title=0.9, threshold_author=0.5)
        labeled_pubs = labeler.auto_label_publications(pub_dirs[:num_pubs], labels_dir)
        
        print(f"Complete: Labeled {len(labeled_pubs)}/{num_pubs} publications\n")
    
    def run_ml_pipeline(self):
        """Run ML training and evaluation pipeline"""
        from ml_pipeline import MLPipeline
        
        print("\nML Training & Evaluation...")
        
        labels_dir = self.output_dir.parent / 'labels'
        
        # Check labels
        if not labels_dir.exists():
            print("[ERROR] No labels found!")
            return
        
        manual_labels = list((labels_dir / 'manual').glob('*_labels.json')) if (labels_dir / 'manual').exists() else []
        auto_labels = list((labels_dir / 'auto').glob('*_auto_labels.json')) if (labels_dir / 'auto').exists() else []
        
        print(f"Labels: {len(manual_labels)} manual, {len(auto_labels)} auto")
        
        if len(manual_labels) < 3 or len(auto_labels) < 2:
            print(f"[WARNING] Insufficient labels (recommended: >=3 manual, >=2 auto)")
        
        # Run pipeline
        pipeline = MLPipeline(self.output_dir, labels_dir)
        pipeline.run_full_pipeline()
    
    def run_full_pipeline(self):
        """Run complete pipeline from start to finish"""
        print("\nFull Pipeline: Process > Label > Train\n")
        
        # Step 1: Process
        print("Step 1/3: Processing publications...")
        self.process_all_publications()
        
        # Step 2: Auto-label
        print("Step 2/3: Auto-labeling...")
        self.run_auto_labeling()
        
        # Step 3: Train with available labels
        print("Step 3/3: ML training...")
        labels_dir = self.output_dir.parent / 'labels'
        manual_labels = list((labels_dir / 'manual').glob('*_labels.json')) if (labels_dir / 'manual').exists() else []
        auto_labels = list((labels_dir / 'auto').glob('*_auto_labels.json')) if (labels_dir / 'auto').exists() else []
        
        if len(manual_labels) + len(auto_labels) == 0:
            print("[ERROR] No labels found after auto-labeling!")
        else:
            self.run_ml_pipeline()
        
        print("Full pipeline complete!\n")
    
    def show_status(self):
        """Show current pipeline status"""
        print(f"\n{'='*70}")
        print("PIPELINE STATUS")
        print(f"{'='*70}\n")
        
        # Check processed publications
        processed = []
        if self.output_dir.exists():
            for pub_dir in self.output_dir.iterdir():
                if pub_dir.is_dir() and (pub_dir / 'hierarchy.json').exists():
                    processed.append(pub_dir.name)
        
        print(f"[Data Processing]")
        print(f"   Processed: {len(processed)} publications")
        
        # Check labels
        labels_dir = self.output_dir.parent / 'labels'
        manual_count = 0
        auto_count = 0
        
        if labels_dir.exists():
            if (labels_dir / 'manual').exists():
                manual_count = len(list((labels_dir / 'manual').glob('*_labels.json')))
            if (labels_dir / 'auto').exists():
                auto_count = len(list((labels_dir / 'auto').glob('*_auto_labels.json')))
        
        print(f"\n[Labeling]")
        print(f"   Manual: {manual_count}")
        print(f"   Auto: {auto_count}")
        
        # Check predictions
        pred_files = list(self.output_dir.glob('*/pred.json')) if self.output_dir.exists() else []
        
        print(f"\n[ML Model]")
        print(f"   Predictions: {len(pred_files)}")
        
        if pred_files:
            # Show MRR
            by_partition = {'train': [], 'valid': [], 'test': []}
            for pred_file in pred_files:
                with open(pred_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                partition = data.get('partition', 'unknown')
                if partition in by_partition:
                    mrr = compute_mrr(data['prediction'], data['groundtruth'])
                    by_partition[partition].append(mrr)
            
            print(f"\n   [MRR Scores]")
            for partition in ['train', 'valid', 'test']:
                if by_partition[partition]:
                    avg = sum(by_partition[partition]) / len(by_partition[partition])
                    print(f"      {partition.capitalize()}: {avg:.4f}")
        
        # Next steps
        print(f"\n{'='*70}")
        print(f"[Next Steps]")
        if not processed:
            print(f"   -> python main.py --process")
        elif manual_count == 0:
            print(f"   -> python manual_labeling_helper.py")
        elif auto_count == 0:
            print(f"   -> python main.py --auto-label")
        elif not pred_files:
            print(f"   -> python main.py --train")
        else:
            print(f"   => Pipeline complete!")
        print(f"{'='*70}\n")
    
    def interactive_menu(self):
        """Interactive menu for pipeline operations"""
        while True:
            print("\n" + "="*70)
            print("LAB 02 - DATA MODELING PIPELINE")
            print("="*70)
            print("\n  1. Process publications")
            print("  2. Auto-labeling")
            print("  3. Manual labeling")
            print("  4. Train ML model")
            print("  5. Run full pipeline")
            print("  6. Show status")
            print("  0. Exit")
            print("="*70)
            
            try:
                choice = input("\nChoice [0-6]: ").strip()
                
                if choice == '0':
                    print("\nGoodbye!\n")
                    break
                elif choice == '1':
                    self.run()
                elif choice == '2':
                    self.run_auto_labeling()
                elif choice == '3':
                    import subprocess
                    subprocess.run(['python', 'manual_labeling_helper.py'])
                elif choice == '4':
                    self.run_ml_pipeline()
                elif choice == '5':
                    self.run_full_pipeline()
                elif choice == '6':
                    self.show_status()
                else:
                    print("[ERROR] Invalid choice")
            
            except KeyboardInterrupt:
                print("\n\nInterrupted. Goodbye!\n")
                break
            except Exception as e:
                print(f"\n[ERROR] {e}\n")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Lab 02 - Data Modeling Pipeline')
    parser.add_argument('--process', action='store_true', help='Process all publications')
    parser.add_argument('--pub-id', type=str, help='Process specific publication')
    parser.add_argument('--auto-label', action='store_true', help='Run auto-labeling')
    parser.add_argument('--num-auto', type=int, help='Number to auto-label')
    parser.add_argument('--train', action='store_true', help='Train ML model')
    parser.add_argument('--full', action='store_true', help='Full pipeline')
    parser.add_argument('--status', action='store_true', help='Show status')
    
    args = parser.parse_args()
    
    # Setup
    base_dir = Path(__file__).parent.parent
    pipeline = Pipeline(base_dir / 'sample', base_dir / 'output')
    
    # Execute
    if args.status:
        pipeline.show_status()
    elif args.process or args.pub_id:
        pipeline.run(pub_id=args.pub_id)
    elif args.auto_label:
        pipeline.run_auto_labeling(args.num_auto)
    elif args.train:
        pipeline.run_ml_pipeline()
    elif args.full:
        pipeline.run_full_pipeline()
    else:
        pipeline.interactive_menu()


if __name__ == '__main__':
    main()
