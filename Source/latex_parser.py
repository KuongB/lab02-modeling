"""
LaTeX Parser Module
Handles multi-file gathering and parsing of LaTeX documents
"""
import re
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from utils import read_file_safe, normalize_text


class LaTeXParser:
    """Parse LaTeX documents and gather included files"""
    
    def __init__(self, tex_dir: Path):
        """
        Initialize parser with TeX directory
        
        Args:
            tex_dir: Directory containing TeX files
        """
        self.tex_dir = Path(tex_dir)
        self.main_file = None
        self.included_files = []
        self.content_cache = {}
        
    def find_main_file(self) -> Optional[Path]:
        """
        Find the main LaTeX file (containing \begin{document})
        
        Returns:
            Path to main file or None
        """
        # Look for .tex files with \begin{document}
        tex_files = list(self.tex_dir.glob("*.tex"))
        
        document_files = []
        for tex_file in tex_files:
            content = read_file_safe(tex_file)
            if content and r'\begin{document}' in content:
                document_files.append(tex_file)
        
        if len(document_files) == 0:
            print(f"Warning: No main file found in {self.tex_dir}")
            return None
        elif len(document_files) == 1:
            self.main_file = document_files[0]
            return self.main_file
        else:
            # Multiple files with \begin{document} - choose the one with more content
            # or the one named "main.tex"
            for f in document_files:
                if f.name.lower() == 'main.tex':
                    self.main_file = f
                    return self.main_file
            
            # Otherwise choose the largest file
            largest = max(document_files, key=lambda f: f.stat().st_size)
            self.main_file = largest
            print(f"Warning: Multiple main files found, chose {largest.name}")
            return self.main_file
    
    def extract_input_includes(self, content: str) -> List[str]:
        r"""
        Extract file names from \\input{} and \\include{} commands
        
        Args:
            content: LaTeX content
            
        Returns:
            List of file names
        """
        includes = []
        
        # Pattern for \input{filename} or \include{filename}
        pattern = r'\\(?:input|include)\{([^}]+)\}'
        matches = re.findall(pattern, content)
        
        for match in matches:
            # Remove any path separators and normalize
            filename = match.strip()
            # Add .tex extension if not present
            if not filename.endswith('.tex'):
                filename += '.tex'
            includes.append(filename)
        
        return includes
    
    def gather_all_files(self) -> List[Path]:
        """
        Recursively gather all files that are included in the main file
        
        Returns:
            List of file paths in order they should be processed
        """
        if self.main_file is None:
            self.find_main_file()
            if self.main_file is None:
                return []
        
        visited = set()
        ordered_files = []
        
        def process_file(filepath: Path):
            """Recursively process file and its includes"""
            if filepath in visited:
                return
            
            visited.add(filepath)
            content = read_file_safe(filepath)
            
            if content is None:
                return
            
            self.content_cache[filepath] = content
            
            # Extract includes from this file
            includes = self.extract_input_includes(content)
            
            # Process each include
            for include_name in includes:
                include_path = filepath.parent / include_name
                if include_path.exists():
                    process_file(include_path)
            
            # Add this file after its includes (post-order for correct assembly)
            ordered_files.append(filepath)
        
        process_file(self.main_file)
        self.included_files = ordered_files
        return ordered_files
    
    def assemble_full_content(self) -> str:
        """
        Assemble full content from main file and all includes
        
        Returns:
            Complete LaTeX content
        """
        if not self.included_files:
            self.gather_all_files()
        
        # Start with main file content
        if self.main_file not in self.content_cache:
            content = read_file_safe(self.main_file)
            if content:
                self.content_cache[self.main_file] = content
        
        main_content = self.content_cache.get(self.main_file, "")
        
        # Replace \input and \include commands with actual content
        def replace_includes(match):
            filename = match.group(1).strip()
            if not filename.endswith('.tex'):
                filename += '.tex'
            
            filepath = self.main_file.parent / filename
            if filepath in self.content_cache:
                return self.content_cache[filepath]
            else:
                # File not found, return original command
                return match.group(0)
        
        # Replace all \input and \include commands
        pattern = r'\\(?:input|include)\{([^}]+)\}'
        assembled = re.sub(pattern, replace_includes, main_content)
        
        return assembled
    
    def remove_comments(self, content: str) -> str:
        """
        Remove LaTeX comments (lines starting with %)
        
        Args:
            content: LaTeX content
            
        Returns:
            Content with comments removed
        """
        # Remove single-line comments (% to end of line)
        # But preserve \% (escaped percent)
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Find % not preceded by backslash
            parts = []
            i = 0
            while i < len(line):
                if line[i] == '%' and (i == 0 or line[i-1] != '\\'):
                    # This is a comment, stop here
                    break
                parts.append(line[i])
                i += 1
            cleaned_lines.append(''.join(parts))
        
        return '\n'.join(cleaned_lines)
    
    def extract_preamble_and_body(self, content: str) -> Tuple[str, str]:
        """
        Split content into preamble and document body
        
        Args:
            content: Full LaTeX content
            
        Returns:
            Tuple of (preamble, body)
        """
        # Find \begin{document}
        match = re.search(r'\\begin\{document\}', content)
        if not match:
            return "", content
        
        preamble = content[:match.start()]
        rest = content[match.end():]
        
        # Find \end{document}
        end_match = re.search(r'\\end\{document\}', rest)
        if end_match:
            body = rest[:end_match.start()]
        else:
            body = rest
        
        return preamble, body


def parse_version_directory(version_dir: Path) -> Dict[str, any]:
    """
    Parse a single version directory and extract all content
    
    Args:
        version_dir: Path to version directory (e.g., 2310-15395v1)
        
    Returns:
        Dictionary with parsed content
    """
    parser = LaTeXParser(version_dir)
    
    # Find and gather files
    main_file = parser.find_main_file()
    if main_file is None:
        return {
            'main_file': None,
            'included_files': [],
            'full_content': "",
            'body': ""
        }
    
    included_files = parser.gather_all_files()
    full_content = parser.assemble_full_content()
    
    # Remove comments
    full_content = parser.remove_comments(full_content)
    
    # Extract body
    preamble, body = parser.extract_preamble_and_body(full_content)
    
    return {
        'main_file': str(main_file.name),
        'included_files': [str(f.name) for f in included_files],
        'full_content': full_content,
        'preamble': preamble,
        'body': body
    }
