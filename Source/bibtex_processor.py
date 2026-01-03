"""
BibTeX Processor Module
Handles BibTeX/BBL file parsing, conversion, and deduplication
"""
import re
from typing import List, Dict, Optional, Set
from pathlib import Path
from utils import read_file_safe, normalize_text, compute_content_hash


class BibEntry:
    """Represents a single BibTeX entry"""
    
    def __init__(self, entry_type: str, cite_key: str, fields: Dict[str, str]):
        self.entry_type = entry_type.lower()  # article, book, inproceedings, etc.
        self.cite_key = cite_key
        self.fields = fields  # title, author, year, etc.
        self.content_hash = self._compute_hash()
    
    def _compute_hash(self) -> str:
        """Compute hash based on content (for deduplication)"""
        # Use title, author, year for matching
        key_fields = ['title', 'author', 'year', 'journal', 'booktitle']
        content_parts = []
        
        for field in key_fields:
            if field in self.fields:
                # Normalize the value
                value = normalize_text(self.fields[field].lower())
                content_parts.append(f"{field}:{value}")
        
        content_str = '|'.join(content_parts)
        return compute_content_hash(content_str)
    
    def to_bibtex(self) -> str:
        """Convert back to BibTeX format"""
        lines = [f"@{self.entry_type}{{{self.cite_key},"]
        
        for field, value in self.fields.items():
            # Escape special characters in value
            lines.append(f"  {field} = {{{value}}},")
        
        lines.append("}")
        return '\n'.join(lines)
    
    def merge_with(self, other: 'BibEntry'):
        """Merge fields from another entry (union of fields)"""
        for field, value in other.fields.items():
            if field not in self.fields:
                self.fields[field] = value
            elif len(value) > len(self.fields[field]):
                # Keep the more complete version
                self.fields[field] = value


class BibTeXParser:
    """Parse BibTeX files"""
    
    def parse_bib_file(self, filepath: Path) -> List[BibEntry]:
        """
        Parse a .bib file
        
        Args:
            filepath: Path to .bib file
            
        Returns:
            List of BibEntry objects
        """
        content = read_file_safe(filepath)
        if not content:
            return []
        
        return self.parse_bib_content(content)
    
    def parse_bib_content(self, content: str) -> List[BibEntry]:
        """
        Parse BibTeX content string
        
        Args:
            content: BibTeX content
            
        Returns:
            List of BibEntry objects
        """
        entries = []
        
        # Pattern to match @type{key, ...}
        # This is a simplified parser - for production use bibtexparser library
        pattern = r'@(\w+)\s*\{\s*([^,\s]+)\s*,(.*?)\n\}'
        
        for match in re.finditer(pattern, content, re.DOTALL):
            entry_type = match.group(1)
            cite_key = match.group(2).strip()
            fields_str = match.group(3)
            
            # Parse fields
            fields = self._parse_fields(fields_str)
            
            entry = BibEntry(entry_type, cite_key, fields)
            entries.append(entry)
        
        return entries
    
    def _parse_fields(self, fields_str: str) -> Dict[str, str]:
        """Parse field string into dictionary"""
        fields = {}
        
        # Pattern: field = {value} or field = "value"
        pattern = r'(\w+)\s*=\s*[{"](.*?)["}]\s*,?'
        
        for match in re.finditer(pattern, fields_str, re.DOTALL):
            field_name = match.group(1).lower()
            field_value = match.group(2).strip()
            fields[field_name] = field_value
        
        return fields


class BBLParser:
    """Parse BBL (BibTeX output) files and convert to BibTeX"""
    
    def parse_bbl_file(self, filepath: Path) -> List[BibEntry]:
        """
        Parse a .bbl file and convert to BibTeX entries
        
        Args:
            filepath: Path to .bbl file
            
        Returns:
            List of BibEntry objects
        """
        content = read_file_safe(filepath)
        if not content:
            return []
        
        return self.parse_bbl_content(content)
    
    def parse_bbl_content(self, content: str) -> List[BibEntry]:
        """
        Parse BBL content and extract bibliography items
        
        Args:
            content: BBL file content
            
        Returns:
            List of BibEntry objects
        """
        entries = []
        
        # BBL files contain \bibitem entries
        # Pattern: \bibitem{key} author. title. journal, year.
        pattern = r'\\bibitem\{([^}]+)\}\s*(.*?)(?=\\bibitem|\\end\{thebibliography\}|$)'
        
        for match in re.finditer(pattern, content, re.DOTALL):
            cite_key = match.group(1).strip()
            item_content = match.group(2).strip()
            
            # Try to extract fields from the text
            fields = self._extract_fields_from_text(item_content)
            
            # Default to 'misc' type since BBL doesn't specify type
            entry = BibEntry('misc', cite_key, fields)
            entries.append(entry)
        
        return entries
    
    def _extract_fields_from_text(self, text: str) -> Dict[str, str]:
        """
        Extract fields from formatted bibliography text
        This is heuristic-based and may not be perfect
        
        Args:
            text: Formatted bibliography text
            
        Returns:
            Dictionary of fields
        """
        fields = {}
        
        # Remove LaTeX commands
        text = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', text)
        text = re.sub(r'\\[a-zA-Z]+', '', text)
        
        # Store full text as note if we can't parse it well
        fields['note'] = normalize_text(text)
        
        # Try to extract title (usually in quotes or italics)
        title_match = re.search(r'["\']([^"\']+)["\']', text)
        if title_match:
            fields['title'] = title_match.group(1)
        
        # Try to extract year (4 digits)
        year_match = re.search(r'\b(19|20)\d{2}\b', text)
        if year_match:
            fields['year'] = year_match.group(0)
        
        # Try to extract authors (text before first period or title)
        parts = text.split('.')
        if parts:
            potential_author = parts[0].strip()
            if len(potential_author) < 100:  # Reasonable author length
                fields['author'] = potential_author
        
        return fields


class BibDeduplicator:
    """Deduplicate BibTeX entries across versions"""
    
    def __init__(self):
        self.entries_by_hash = {}  # hash -> BibEntry
        self.key_mappings = {}  # old_key -> canonical_key
    
    def add_entries(self, entries: List[BibEntry]):
        """
        Add entries and deduplicate
        
        Args:
            entries: List of BibEntry objects
        """
        for entry in entries:
            if entry.content_hash in self.entries_by_hash:
                # Duplicate found - merge fields
                existing = self.entries_by_hash[entry.content_hash]
                existing.merge_with(entry)
                
                # Map this key to canonical key
                if entry.cite_key != existing.cite_key:
                    self.key_mappings[entry.cite_key] = existing.cite_key
            else:
                # New entry
                self.entries_by_hash[entry.content_hash] = entry
                self.key_mappings[entry.cite_key] = entry.cite_key
    
    def get_deduplicated_entries(self) -> List[BibEntry]:
        """Get list of unique entries"""
        return list(self.entries_by_hash.values())
    
    def get_canonical_key(self, key: str) -> str:
        """Get canonical key for a citation key"""
        return self.key_mappings.get(key, key)


def process_publication_references(pub_dir: Path) -> Dict:
    """
    Process all BibTeX/BBL files from all versions of a publication
    
    Args:
        pub_dir: Publication directory (e.g., sample/2310-15395)
        
    Returns:
        Dictionary with deduplicated entries and key mappings
    """
    tex_dir = pub_dir / 'tex'
    if not tex_dir.exists():
        return {'entries': [], 'key_mappings': {}}
    
    deduplicator = BibDeduplicator()
    bib_parser = BibTeXParser()
    bbl_parser = BBLParser()
    
    # Process each version
    for version_dir in tex_dir.iterdir():
        if not version_dir.is_dir():
            continue
        
        # Look for .bib files first (preferred)
        bib_files = list(version_dir.glob('*.bib'))
        if bib_files:
            for bib_file in bib_files:
                entries = bib_parser.parse_bib_file(bib_file)
                deduplicator.add_entries(entries)
        else:
            # Fall back to .bbl files
            bbl_files = list(version_dir.glob('*.bbl'))
            for bbl_file in bbl_files:
                entries = bbl_parser.parse_bbl_file(bbl_file)
                deduplicator.add_entries(entries)
    
    return {
        'entries': deduplicator.get_deduplicated_entries(),
        'key_mappings': deduplicator.key_mappings
    }


def write_refs_bib(entries: List[BibEntry], output_path: Path):
    """
    Write deduplicated entries to refs.bib file
    
    Args:
        entries: List of BibEntry objects
        output_path: Output file path
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for entry in entries:
            f.write(entry.to_bibtex())
            f.write('\n\n')
