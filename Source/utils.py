"""
Utility functions for the project
"""
import re
import hashlib
import unicodedata
from pathlib import Path
from typing import List, Dict, Any, Optional


def normalize_text(text: str) -> str:
    """
    Normalize text by removing extra whitespace and normalizing unicode
    
    Args:
        text: Input text
        
    Returns:
        Normalized text
    """
    # Normalize unicode
    text = unicodedata.normalize('NFKC', text)
    
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def compute_content_hash(content: str) -> str:
    """
    Compute SHA256 hash of content for deduplication
    
    Args:
        content: Text content
        
    Returns:
        Hex digest of hash
    """
    # Normalize before hashing
    normalized = normalize_text(content)
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()[:16]


def clean_latex_command(text: str, command: str) -> str:
    r"""
    Remove specific LaTeX command from text
    
    Args:
        text: LaTeX text
        command: Command to remove (e.g., '\\centering')
        
    Returns:
        Text with command removed
    """
    # Escape backslash for regex
    pattern = re.escape(command)
    return re.sub(pattern, '', text)


def extract_cite_keys(text: str) -> List[str]:
    r"""
    Extract citation keys from LaTeX text
    
    Args:
        text: LaTeX text containing \\cite{} commands
        
    Returns:
        List of citation keys
    """
    # Match \cite{key1,key2,key3} or \cite{key}
    pattern = r'\\cite\*?\{([^}]+)\}'
    matches = re.findall(pattern, text)
    
    keys = []
    for match in matches:
        # Split by comma for multiple citations
        keys.extend([k.strip() for k in match.split(',')])
    
    return keys


def generate_element_id(pub_id: str, version: str, element_type: str, index: int, 
                       parent_id: Optional[str] = None) -> str:
    """
    Generate unique element ID
    
    Args:
        pub_id: Publication ID (e.g., '2310-15395')
        version: Version string (e.g., 'v1')
        element_type: Type of element (e.g., 'section', 'paragraph', 'equation')
        index: Index of element
        parent_id: Optional parent ID for nested elements
        
    Returns:
        Unique element ID
    """
    if parent_id:
        return f"{parent_id}-{element_type}-{index}"
    else:
        return f"{pub_id}-{version}-{element_type}-{index}"


def is_math_environment(env_name: str) -> bool:
    """
    Check if environment name is a mathematical environment
    
    Args:
        env_name: LaTeX environment name
        
    Returns:
        True if math environment
    """
    from config import MATH_BLOCK_ENVS
    return env_name in MATH_BLOCK_ENVS


def is_figure_environment(env_name: str) -> bool:
    """
    Check if environment name is a figure/table environment
    
    Args:
        env_name: LaTeX environment name
        
    Returns:
        True if figure/table environment
    """
    from config import FIGURE_ENVS
    return env_name in FIGURE_ENVS


def is_list_environment(env_name: str) -> bool:
    """
    Check if environment name is a list environment
    
    Args:
        env_name: LaTeX environment name
        
    Returns:
        True if list environment
    """
    from config import LIST_ENVS
    return env_name in LIST_ENVS


def read_file_safe(filepath: Path) -> Optional[str]:
    """
    Safely read a file with multiple encoding attempts
    
    Args:
        filepath: Path to file
        
    Returns:
        File content or None if failed
    """
    encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
    
    for encoding in encodings:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                return f.read()
        except (UnicodeDecodeError, FileNotFoundError):
            continue
    
    print(f"Warning: Could not read file {filepath}")
    return None


def write_json_safe(data: Any, filepath: Path) -> bool:
    """
    Safely write data to JSON file
    
    Args:
        data: Data to write
        filepath: Output file path
        
    Returns:
        True if successful
    """
    import json
    
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error writing to {filepath}: {e}")
        return False


def load_json_safe(filepath: Path) -> Optional[Dict]:
    """
    Safely load JSON file
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        Loaded data or None if failed
    """
    import json
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None
