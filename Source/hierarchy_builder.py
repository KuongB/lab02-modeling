"""
Hierarchy Builder Module
Converts LaTeX content into hierarchical tree structure
"""
import re
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from utils import compute_content_hash, generate_element_id, normalize_text
from config import (
    LATEX_SECTION_COMMANDS, EXCLUDE_SECTIONS, INCLUDE_UNNUMBERED_SECTIONS,
    MATH_BLOCK_ENVS, FIGURE_ENVS, LIST_ENVS
)


class HierarchyNode:
    """Represents a node in the document hierarchy"""
    
    def __init__(self, node_id: str, node_type: str, content: str, 
                 title: str = "", level: int = 0, parent_id: Optional[str] = None):
        self.id = node_id
        self.type = node_type  # document, section, subsection, paragraph, sentence, equation, figure, list, item
        self.content = content
        self.title = title
        self.level = level
        self.parent_id = parent_id
        self.children = []
        self.content_hash = compute_content_hash(content) if content else None
    
    def add_child(self, child: 'HierarchyNode'):
        """Add a child node"""
        self.children.append(child)
        child.parent_id = self.id
    
    def to_dict(self) -> Dict:
        """Convert node to dictionary"""
        return {
            'id': self.id,
            'type': self.type,
            'content': self.content,
            'title': self.title,
            'level': self.level,
            'parent_id': self.parent_id,
            'content_hash': self.content_hash,
            'children': [child.to_dict() for child in self.children]
        }


class HierarchyBuilder:
    """Build hierarchical structure from LaTeX content"""
    
    def __init__(self, pub_id: str, version: str):
        """
        Initialize builder
        
        Args:
            pub_id: Publication ID (e.g., '2310-15395')
            version: Version string (e.g., 'v1')
        """
        self.pub_id = pub_id
        self.version = version
        self.node_counter = defaultdict(int)
        self.all_nodes = {}  # id -> node mapping
        
    def _get_next_id(self, element_type: str, parent_id: Optional[str] = None) -> str:
        """Generate next ID for element type"""
        self.node_counter[element_type] += 1
        index = self.node_counter[element_type]
        return generate_element_id(self.pub_id, self.version, element_type, index, parent_id)
    
    def extract_sections(self, content: str) -> List[Dict]:
        """
        Extract sections and their hierarchy from content
        
        Args:
            content: LaTeX body content
            
        Returns:
            List of section dictionaries with positions and levels
        """
        sections = []
        
        # Define section levels
        section_levels = {
            r'\chapter': 0,
            r'\section': 1,
            r'\subsection': 2,
            r'\subsubsection': 3,
            r'\paragraph': 4,
            r'\subparagraph': 5
        }
        
        # Pattern to match section commands
        # Matches: \section{title} or \section*{title}
        pattern = r'\\(chapter|section|subsection|subsubsection|paragraph|subparagraph)(\*?)\{([^}]+)\}'
        
        for match in re.finditer(pattern, content):
            cmd = '\\' + match.group(1)
            is_unnumbered = match.group(2) == '*'
            title = match.group(3)
            position = match.start()
            
            # Check if this section should be excluded
            title_lower = title.lower().strip()
            
            # Check if this is References/Bibliography section
            is_references = any(excl in title_lower for excl in EXCLUDE_SECTIONS)
            
            # Include acknowledgements and appendices even if unnumbered
            include_unnumbered = any(incl in title_lower for incl in INCLUDE_UNNUMBERED_SECTIONS)
            
            # Skip numbered references section OR unnumbered sections that are not in include list
            if is_references:
                # Don't add to sections list, but we'll handle stopping at this point later
                sections.append({
                    'command': cmd,
                    'title': title,
                    'level': section_levels.get(cmd, 1),
                    'position': position,
                    'end': match.end(),
                    'is_unnumbered': is_unnumbered,
                    'include_unnumbered': include_unnumbered,
                    'is_references': True
                })
            elif is_unnumbered and not include_unnumbered:
                # Skip unnumbered sections that are not in include list
                continue
            else:
                # Include this section
                sections.append({
                    'command': cmd,
                    'title': title,
                    'level': section_levels.get(cmd, 1),
                    'position': position,
                    'end': match.end(),
                    'is_unnumbered': is_unnumbered,
                    'include_unnumbered': include_unnumbered,
                    'is_references': False
                })
        
        return sections
    
    def extract_environments(self, content: str) -> List[Dict]:
        """
        Extract LaTeX environments (equations, figures, lists)
        
        Args:
            content: LaTeX content
            
        Returns:
            List of environment dictionaries
        """
        envs = []
        
        # Pattern: \begin{envname}...\end{envname}
        pattern = r'\\begin\{([a-zA-Z*]+)\}(.*?)\\end\{\1\}'
        
        for match in re.finditer(pattern, content, re.DOTALL):
            env_name = match.group(1)
            env_content = match.group(2)
            position = match.start()
            
            # Determine environment type
            env_type = 'environment'
            if env_name in MATH_BLOCK_ENVS or env_name.replace('*', '') in MATH_BLOCK_ENVS:
                env_type = 'equation'
            elif env_name in FIGURE_ENVS or env_name.replace('*', '') in FIGURE_ENVS:
                env_type = 'figure'
            elif env_name in LIST_ENVS:
                env_type = 'list'
            
            envs.append({
                'env_name': env_name,
                'env_type': env_type,
                'content': env_content,
                'full_content': match.group(0),
                'position': position,
                'end': match.end()
            })
        
        return envs
    
    def extract_list_items(self, list_content: str) -> List[str]:
        """
        Extract items from itemize/enumerate environment
        
        Args:
            list_content: Content of list environment
            
        Returns:
            List of item contents
        """
        items = []
        
        # Split by \item
        parts = re.split(r'\\item\s*', list_content)
        
        # First part before any \item is not an item
        for part in parts[1:]:
            # Clean up the item content
            item_content = part.strip()
            if item_content:
                items.append(item_content)
        
        return items
    
    def split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences (by periods)
        
        Args:
            text: Plain text
            
        Returns:
            List of sentences
        """
        # Simple sentence splitting by period
        # This is a simplified version - a more sophisticated approach would handle
        # abbreviations, decimals, etc.
        
        # Split by period followed by space and capital letter
        sentences = re.split(r'\.\s+(?=[A-Z])', text)
        
        # Also split by period at end of text
        final_sentences = []
        for sent in sentences:
            if sent.strip():
                # Add back the period if not present
                if not sent.strip().endswith('.'):
                    sent = sent.strip() + '.'
                final_sentences.append(sent.strip())
        
        return final_sentences
    
    def build_hierarchy(self, body_content: str) -> HierarchyNode:
        """
        Build complete hierarchy from LaTeX body
        
        Args:
            body_content: Cleaned LaTeX body content
            
        Returns:
            Root node of hierarchy
        """
        # Create root document node
        root_id = f"{self.pub_id}-{self.version}-document"
        root = HierarchyNode(
            node_id=root_id,
            node_type='document',
            content='',
            title=f'{self.pub_id} {self.version}',
            level=0
        )
        self.all_nodes[root_id] = root
        
        # Extract sections
        sections = self.extract_sections(body_content)
        
        # Find where References section starts (to stop processing there)
        # Check both section commands and bibliography commands
        references_start_pos = None
        filtered_sections = []
        
        for i, section in enumerate(sections):
            if section.get('is_references', False):
                references_start_pos = section['position']
                # Don't include References and everything after
                break
            else:
                filtered_sections.append(section)
        
        # Also check for \bibliography{} or \bibliographystyle{} commands
        # which might appear without a References section heading
        biblio_match = re.search(r'\\(bibliography|bibliographystyle|begin\{thebibliography\})', 
                                body_content)
        if biblio_match:
            biblio_pos = biblio_match.start()
            # Use the earlier position between section-based and command-based detection
            if references_start_pos is None or biblio_pos < references_start_pos:
                references_start_pos = biblio_pos
        
        sections = filtered_sections
        
        if not sections:
            # No sections found - treat entire body as one section
            # But stop at References if found
            end_pos = references_start_pos if references_start_pos else len(body_content)
            self._process_content_block(body_content[:end_pos], root, 0, end_pos)
            return root
        
        # Build section hierarchy
        section_stack = [root]  # Stack of (node, level)
        
        for i, section in enumerate(sections):
            # Create section node
            section_id = self._get_next_id('section')
            section_node = HierarchyNode(
                node_id=section_id,
                node_type='section',
                content='',
                title=section['title'],
                level=section['level']
            )
            self.all_nodes[section_id] = section_node
            
            # Find appropriate parent based on level
            while len(section_stack) > 1 and section_stack[-1].level >= section['level']:
                section_stack.pop()
            
            parent = section_stack[-1]
            parent.add_child(section_node)
            section_stack.append(section_node)
            
            # Extract content for this section (from section end to next section start or References)
            start_pos = section['end']
            if i + 1 < len(sections):
                end_pos = sections[i + 1]['position']
            else:
                # Last section - stop at References or end of content
                end_pos = references_start_pos if references_start_pos else len(body_content)
            
            section_content = body_content[start_pos:end_pos]
            
            # Process content within this section
            self._process_content_block(section_content, section_node, start_pos, end_pos)
        
        return root
    
    def _process_content_block(self, content: str, parent_node: HierarchyNode, 
                               start_pos: int, end_pos: int):
        """
        Process a block of content and create child nodes
        
        Args:
            content: Content to process
            parent_node: Parent node to attach children to
            start_pos: Starting position in original content
            end_pos: Ending position in original content
        """
        # Extract environments first (equations, figures, lists)
        envs = self.extract_environments(content)
        
        # Sort environments by position
        envs.sort(key=lambda e: e['position'])
        
        # Track which parts of content are covered by environments
        covered_ranges = [(e['position'], e['end']) for e in envs]
        
        # Process environments
        for env in envs:
            if env['env_type'] == 'equation':
                # Create equation node
                eq_id = self._get_next_id('equation', parent_node.id)
                eq_node = HierarchyNode(
                    node_id=eq_id,
                    node_type='equation',
                    content=env['full_content'],
                    title='',
                    level=parent_node.level + 1,
                    parent_id=parent_node.id
                )
                self.all_nodes[eq_id] = eq_node
                parent_node.add_child(eq_node)
                
            elif env['env_type'] == 'figure':
                # Create figure node
                fig_id = self._get_next_id('figure', parent_node.id)
                
                # Try to extract caption
                caption_match = re.search(r'\\caption\{([^}]+)\}', env['content'])
                caption = caption_match.group(1) if caption_match else ''
                
                fig_node = HierarchyNode(
                    node_id=fig_id,
                    node_type='figure',
                    content=env['full_content'],
                    title=caption,
                    level=parent_node.level + 1,
                    parent_id=parent_node.id
                )
                self.all_nodes[fig_id] = fig_node
                parent_node.add_child(fig_node)
                
            elif env['env_type'] == 'list':
                # Create list node with full list environment content
                list_id = self._get_next_id('list', parent_node.id)
                list_node = HierarchyNode(
                    node_id=list_id,
                    node_type='list',
                    content=env['full_content'],  # Store full list environment
                    title='',
                    level=parent_node.level + 1,
                    parent_id=parent_node.id
                )
                self.all_nodes[list_id] = list_node
                parent_node.add_child(list_node)
                
                # Extract and process items
                items = self.extract_list_items(env['content'])
                for item_content in items:
                    item_id = self._get_next_id('item', list_node.id)
                    item_node = HierarchyNode(
                        node_id=item_id,
                        node_type='item',
                        content=item_content,
                        title='',
                        level=list_node.level + 1,
                        parent_id=list_node.id
                    )
                    self.all_nodes[item_id] = item_node
                    list_node.add_child(item_node)
        
        # Extract plain text content (not in environments)
        plain_text_parts = []
        last_end = 0
        
        for env in envs:
            if env['position'] > last_end:
                plain_text_parts.append(content[last_end:env['position']])
            last_end = env['end']
        
        if last_end < len(content):
            plain_text_parts.append(content[last_end:])
        
        plain_text = ' '.join(plain_text_parts)
        
        # Split plain text into paragraphs and sentences
        if plain_text.strip():
            # Split by double newlines (paragraphs)
            paragraphs = re.split(r'\n\n+', plain_text)
            
            for para_text in paragraphs:
                para_text = para_text.strip()
                if not para_text:
                    continue
                
                # Create paragraph node with full paragraph text as content
                para_id = self._get_next_id('paragraph', parent_node.id)
                para_node = HierarchyNode(
                    node_id=para_id,
                    node_type='paragraph',
                    content=para_text,  # Store full paragraph text
                    title='',
                    level=parent_node.level + 1,
                    parent_id=parent_node.id
                )
                self.all_nodes[para_id] = para_node
                parent_node.add_child(para_node)
                
                # Split into sentences
                sentences = self.split_into_sentences(para_text)
                for sent_text in sentences:
                    if sent_text.strip():
                        sent_id = self._get_next_id('sentence', para_node.id)
                        sent_node = HierarchyNode(
                            node_id=sent_id,
                            node_type='sentence',
                            content=sent_text,
                            title='',
                            level=para_node.level + 1,
                            parent_id=para_node.id
                        )
                        self.all_nodes[sent_id] = sent_node
                        para_node.add_child(sent_node)


def build_hierarchy_from_versions(pub_id: str, versions_data: Dict[str, Dict]) -> Dict:
    """
    Build hierarchy for all versions of a publication
    
    Args:
        pub_id: Publication ID
        versions_data: Dictionary mapping version -> parsed data
        
    Returns:
        Combined hierarchy structure following format:
        {
            "elements": {
                "id": "content or title"
            },
            "hierarchy": {
                "version": {
                    "child_id": "parent_id"
                }
            }
        }
    """
    all_elements = {}
    all_hierarchies = {}
    content_hash_to_id = {}  # For deduplication: hash -> canonical_id
    id_mapping = {}  # For mapping: original_id -> canonical_id (after dedup)
    
    for version, data in versions_data.items():
        builder = HierarchyBuilder(pub_id, version)
        body_content = data.get('body', '')
        
        if not body_content:
            continue
        
        # Build hierarchy for this version
        root = builder.build_hierarchy(body_content)
        
        # Collect all nodes and handle deduplication
        version_hierarchy = {}
        id_mapping[version] = {}  # Track ID mappings for this version
        
        for node_id, node in builder.all_nodes.items():
            canonical_id = node_id  # Default to original ID
            
            # Check for duplicate content across versions (only for leaf nodes with content)
            if node.content and node.content_hash and node.type in ['sentence', 'equation', 'figure', 'item']:
                if node.content_hash in content_hash_to_id:
                    # Reuse existing ID for duplicate content
                    canonical_id = content_hash_to_id[node.content_hash]
                    id_mapping[version][node_id] = canonical_id
                else:
                    # New content - register it
                    content_hash_to_id[node.content_hash] = node_id
                    all_elements[node_id] = node.content
                    id_mapping[version][node_id] = node_id
            else:
                # Structural node (section, paragraph, etc.) or node with title
                # These are NOT deduplicated - each version has its own structure
                if node.type in ['sentence', 'equation', 'figure', 'item']:
                    # Leaf node with content
                    all_elements[node_id] = node.content if node.content else node.title
                elif node.type in ['paragraph', 'list']:
                    # Paragraph/list nodes have content, not title
                    all_elements[node_id] = node.content if node.content else ''
                else:
                    # Higher-level component (section, document) with title
                    all_elements[node_id] = node.title if node.title else node.content
                id_mapping[version][node_id] = node_id
        
        # Build hierarchy mapping: child_id -> parent_id
        # Use canonical IDs after deduplication
        for node_id, node in builder.all_nodes.items():
            if node.parent_id:
                # Map both child and parent to their canonical IDs
                child_canonical = id_mapping[version].get(node_id, node_id)
                parent_canonical = id_mapping[version].get(node.parent_id, node.parent_id)
                version_hierarchy[child_canonical] = parent_canonical
            else:
                # This is root - no parent
                pass
        
        all_hierarchies[version] = version_hierarchy
    
    return {
        'elements': all_elements,
        'hierarchy': all_hierarchies
    }
