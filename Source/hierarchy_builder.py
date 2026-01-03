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
            
            # Skip references section
            if any(excl in title_lower for excl in EXCLUDE_SECTIONS):
                continue
            
            # Include acknowledgements and appendices even if unnumbered
            include_unnumbered = any(incl in title_lower for incl in INCLUDE_UNNUMBERED_SECTIONS)
            
            sections.append({
                'command': cmd,
                'title': title,
                'level': section_levels.get(cmd, 1),
                'position': position,
                'end': match.end(),
                'is_unnumbered': is_unnumbered,
                'include_unnumbered': include_unnumbered
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
        
        if not sections:
            # No sections found - treat entire body as one section
            self._process_content_block(body_content, root, 0, len(body_content))
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
            
            # Extract content for this section (from section end to next section start)
            start_pos = section['end']
            if i + 1 < len(sections):
                end_pos = sections[i + 1]['position']
            else:
                end_pos = len(body_content)
            
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
                # Create list node
                list_id = self._get_next_id('list', parent_node.id)
                list_node = HierarchyNode(
                    node_id=list_id,
                    node_type='list',
                    content='',
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
                
                # Create paragraph node
                para_id = self._get_next_id('paragraph', parent_node.id)
                para_node = HierarchyNode(
                    node_id=para_id,
                    node_type='paragraph',
                    content='',
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
        Combined hierarchy structure
    """
    all_elements = {}
    all_hierarchies = {}
    content_hash_to_id = {}  # For deduplication
    
    for version, data in versions_data.items():
        builder = HierarchyBuilder(pub_id, version)
        body_content = data.get('body', '')
        
        if not body_content:
            continue
        
        # Build hierarchy for this version
        root = builder.build_hierarchy(body_content)
        
        # Collect all nodes
        version_hierarchy = {}
        
        for node_id, node in builder.all_nodes.items():
            # Check for duplicate content across versions
            if node.content and node.content_hash:
                if node.content_hash in content_hash_to_id:
                    # Reuse existing ID
                    deduplicated_id = content_hash_to_id[node.content_hash]
                    # Update hierarchy mapping but use existing element
                    if node.parent_id:
                        version_hierarchy[node.id] = node.parent_id
                else:
                    # New content
                    content_hash_to_id[node.content_hash] = node.id
                    all_elements[node.id] = node.content if node.type in ['sentence', 'equation', 'figure', 'item'] else node.title
                    if node.parent_id:
                        version_hierarchy[node.id] = node.parent_id
            else:
                # No content (structural node like section, paragraph)
                all_elements[node.id] = node.title
                if node.parent_id:
                    version_hierarchy[node.id] = node.parent_id
        
        all_hierarchies[version] = version_hierarchy
    
    return {
        'elements': all_elements,
        'hierarchy': all_hierarchies
    }
