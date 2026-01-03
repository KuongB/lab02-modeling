"""
Manual Labeling Helper
Interactive tool to help with manual labeling of references
"""
import json
from pathlib import Path
from typing import Dict, List
from fuzzywuzzy import fuzz
from config import OUTPUT_DIR
from utils import load_json_safe


class ManualLabelingHelper:
    """Helper tool for manual reference labeling"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.labels = {}
        self.labels_file = Path('manual_labels.json')
        
        # Load existing labels if available
        if self.labels_file.exists():
            self.labels = load_json_safe(self.labels_file)
            if not self.labels:
                self.labels = {}
    
    def get_publication_list(self) -> List[str]:
        """Get list of processed publications"""
        pubs = []
        for pub_dir in self.output_dir.iterdir():
            if pub_dir.is_dir() and (pub_dir / 'refs.bib').exists():
                pubs.append(pub_dir.name)
        return sorted(pubs)
    
    def load_publication_data(self, pub_id: str) -> Dict:
        """Load BibTeX entries and references for a publication"""
        pub_dir = self.output_dir / pub_id
        
        # Load references.json
        refs_path = pub_dir / 'references.json'
        references = load_json_safe(refs_path) or {}
        
        # Load refs.bib
        bib_path = pub_dir / 'refs.bib'
        bib_entries = {}
        
        if bib_path.exists():
            from bibtex_processor import BibTeXParser
            parser = BibTeXParser()
            entries = parser.parse_bib_file(bib_path)
            
            for entry in entries:
                bib_entries[entry.cite_key] = {
                    'type': entry.entry_type,
                    'fields': entry.fields
                }
        
        return {
            'references': references,
            'bib_entries': bib_entries
        }
    
    def suggest_matches(self, bib_entry: Dict, references: Dict, top_n: int = 5) -> List[tuple]:
        """
        Suggest potential matches for a BibTeX entry
        
        Args:
            bib_entry: BibTeX entry dict
            references: References dict
            top_n: Number of suggestions
            
        Returns:
            List of (arxiv_id, score, reason) tuples
        """
        suggestions = []
        
        bib_title = bib_entry.get('fields', {}).get('title', '').lower()
        bib_year = bib_entry.get('fields', {}).get('year', '')
        bib_eprint = bib_entry.get('fields', {}).get('eprint', '')
        
        # Check if arXiv ID directly in entry
        if bib_eprint and bib_eprint in references:
            return [(bib_eprint, 100, 'Direct arXiv ID match')]
        
        for arxiv_id, ref_data in references.items():
            ref_title = ref_data.get('title', '').lower()
            ref_year = ref_data.get('submitted_date', '')[:4]
            
            score = 0
            reasons = []
            
            # Title similarity
            if bib_title and ref_title:
                title_sim = fuzz.ratio(bib_title, ref_title)
                score += title_sim * 0.7
                if title_sim > 80:
                    reasons.append(f'Title similarity: {title_sim}%')
            
            # Year match
            if bib_year and ref_year and bib_year == ref_year:
                score += 20
                reasons.append(f'Year match: {bib_year}')
            
            # Author match (simple check)
            bib_author = bib_entry.get('fields', {}).get('author', '').lower()
            ref_authors = ' '.join(ref_data.get('authors', [])).lower()
            
            if bib_author and ref_authors:
                # Check for last name in authors
                author_parts = bib_author.split()
                for part in author_parts:
                    if len(part) > 3 and part in ref_authors:
                        score += 10
                        reasons.append(f'Author match: {part}')
                        break
            
            if score > 30:  # Minimum threshold
                suggestions.append((arxiv_id, score, ', '.join(reasons)))
        
        # Sort by score descending
        suggestions.sort(key=lambda x: x[1], reverse=True)
        
        return suggestions[:top_n]
    
    def interactive_label(self, pub_id: str):
        """Interactive labeling for one publication"""
        print(f"\n{'='*70}")
        print(f"Labeling Publication: {pub_id}")
        print(f"{'='*70}")
        
        data = self.load_publication_data(pub_id)
        references = data['references']
        bib_entries = data['bib_entries']
        
        if pub_id not in self.labels:
            self.labels[pub_id] = {}
        
        print(f"\nFound {len(bib_entries)} BibTeX entries")
        print(f"Found {len(references)} reference candidates\n")
        
        for i, (bib_key, bib_entry) in enumerate(bib_entries.items(), 1):
            # Skip if already labeled
            if bib_key in self.labels[pub_id]:
                print(f"[{i}/{len(bib_entries)}] {bib_key} - Already labeled ✓")
                continue
            
            print(f"\n{'-'*70}")
            print(f"[{i}/{len(bib_entries)}] BibTeX Key: {bib_key}")
            print(f"Type: {bib_entry['type']}")
            
            if 'title' in bib_entry['fields']:
                print(f"Title: {bib_entry['fields']['title'][:80]}...")
            if 'author' in bib_entry['fields']:
                print(f"Author: {bib_entry['fields']['author'][:80]}...")
            if 'year' in bib_entry['fields']:
                print(f"Year: {bib_entry['fields']['year']}")
            
            # Get suggestions
            suggestions = self.suggest_matches(bib_entry, references)
            
            if suggestions:
                print(f"\n📋 Suggested matches:")
                for j, (arxiv_id, score, reason) in enumerate(suggestions, 1):
                    ref = references[arxiv_id]
                    print(f"\n  {j}. {arxiv_id} (Score: {score:.0f})")
                    print(f"     Title: {ref.get('title', 'N/A')[:70]}...")
                    print(f"     Authors: {', '.join(ref.get('authors', []))[:70]}...")
                    print(f"     Year: {ref.get('submitted_date', 'N/A')[:4]}")
                    print(f"     Reason: {reason}")
            
            print(f"\n{'='*70}")
            response = input("Enter choice (1-5 for suggestion, arXiv ID, 's' to skip, 'q' to quit): ").strip()
            
            if response.lower() == 'q':
                break
            elif response.lower() == 's':
                continue
            elif response.isdigit() and 1 <= int(response) <= len(suggestions):
                # Use suggestion
                arxiv_id = suggestions[int(response) - 1][0]
                self.labels[pub_id][bib_key] = arxiv_id
                print(f"✓ Labeled: {bib_key} → {arxiv_id}")
            elif response in references:
                # Direct arXiv ID input
                self.labels[pub_id][bib_key] = response
                print(f"✓ Labeled: {bib_key} → {response}")
            else:
                print("❌ Invalid input, skipping...")
        
        # Save after each publication
        self.save_labels()
    
    def save_labels(self):
        """Save labels to file"""
        with open(self.labels_file, 'w', encoding='utf-8') as f:
            json.dump(self.labels, f, indent=2, ensure_ascii=False)
        
        # Count total pairs
        total_pairs = sum(len(pairs) for pairs in self.labels.values())
        print(f"\n💾 Saved {len(self.labels)} publications, {total_pairs} pairs")
    
    def show_statistics(self):
        """Show labeling statistics"""
        print(f"\n{'='*70}")
        print("Labeling Statistics")
        print(f"{'='*70}")
        
        total_pubs = len(self.labels)
        total_pairs = sum(len(pairs) for pairs in self.labels.values())
        
        print(f"Publications labeled: {total_pubs}")
        print(f"Total pairs labeled: {total_pairs}")
        
        if self.labels:
            print(f"\nBreakdown by publication:")
            for pub_id, pairs in self.labels.items():
                print(f"  {pub_id}: {len(pairs)} pairs")
        
        # Check requirements
        print(f"\n{'='*70}")
        print("Requirements Check")
        print(f"{'='*70}")
        
        req_met = True
        if total_pubs < 5:
            print(f"❌ Need at least 5 publications (have {total_pubs})")
            req_met = False
        else:
            print(f"✓ Publications requirement met ({total_pubs} ≥ 5)")
        
        if total_pairs < 20:
            print(f"❌ Need at least 20 pairs (have {total_pairs})")
            req_met = False
        else:
            print(f"✓ Pairs requirement met ({total_pairs} ≥ 20)")
        
        if req_met:
            print(f"\n🎉 All requirements met! Ready for ML training.")
        else:
            print(f"\n⚠️  Continue labeling to meet requirements.")
    
    def run(self):
        """Run interactive labeling session"""
        print("\n" + "="*70)
        print("Manual Labeling Helper")
        print("="*70)
        
        pubs = self.get_publication_list()
        print(f"\nFound {len(pubs)} publications")
        
        # Show current statistics
        self.show_statistics()
        
        print(f"\n{'='*70}")
        print("Available publications:")
        for i, pub_id in enumerate(pubs[:10], 1):  # Show first 10
            status = "✓ Labeled" if pub_id in self.labels else "○ Not labeled"
            pairs = len(self.labels.get(pub_id, {}))
            print(f"  {i}. {pub_id} - {status} ({pairs} pairs)")
        
        if len(pubs) > 10:
            print(f"  ... and {len(pubs) - 10} more")
        
        while True:
            print(f"\n{'='*70}")
            print("Options:")
            print("  [number] - Label publication by number")
            print("  [pub_id] - Label publication by ID")
            print("  'stats' - Show statistics")
            print("  'quit' - Exit")
            print(f"{'='*70}")
            
            choice = input("Enter choice: ").strip()
            
            if choice.lower() == 'quit':
                break
            elif choice.lower() == 'stats':
                self.show_statistics()
            elif choice.isdigit() and 1 <= int(choice) <= len(pubs):
                pub_id = pubs[int(choice) - 1]
                self.interactive_label(pub_id)
            elif choice in pubs:
                self.interactive_label(choice)
            else:
                print("❌ Invalid choice")
        
        print("\n✅ Labeling session complete!")
        self.show_statistics()


def main():
    """Main entry point"""
    helper = ManualLabelingHelper(OUTPUT_DIR)
    helper.run()


if __name__ == '__main__':
    main()
