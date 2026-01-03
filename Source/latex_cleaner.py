"""
LaTeX Content Cleaner Module
Standardizes and cleans LaTeX content
"""
import re


class LaTeXCleaner:
    """Clean and standardize LaTeX content"""
    
    # Formatting commands that don't carry semantic meaning
    FORMATTING_COMMANDS = [
        r'\\centering',
        r'\\raggedright',
        r'\\raggedleft',
        r'\\noindent',
        r'\\smallskip',
        r'\\medskip',
        r'\\bigskip',
        r'\\newpage',
        r'\\clearpage',
        r'\\pagebreak',
        r'\\linebreak',
        r'\\nolinebreak',
        r'\\nopagebreak',
        r'\\vspace\{[^}]*\}',
        r'\\hspace\{[^}]*\}',
        r'\\vfill',
        r'\\hfill',
    ]
    
    # Table formatting commands
    TABLE_COMMANDS = [
        r'\\toprule',
        r'\\midrule',
        r'\\bottomrule',
        r'\\cline\{[^}]*\}',
        r'\\hline',
        r'\[htpb\]',
        r'\[!htbp\]',
        r'\[H\]',
        r'\[h\]',
        r'\[t\]',
        r'\[b\]',
        r'\[p\]',
    ]
    
    def __init__(self):
        """Initialize cleaner"""
        pass
    
    def remove_formatting_commands(self, content: str) -> str:
        """
        Remove LaTeX formatting commands that don't carry content meaning
        
        Args:
            content: LaTeX content
            
        Returns:
            Cleaned content
        """
        cleaned = content
        
        for cmd in self.FORMATTING_COMMANDS + self.TABLE_COMMANDS:
            cleaned = re.sub(cmd, '', cleaned)
        
        return cleaned
    
    def normalize_inline_math(self, content: str) -> str:
        """
        Normalize inline math to $ ... $ format
        
        Args:
            content: LaTeX content
            
        Returns:
            Content with normalized inline math
        """
        # Convert \( ... \) to $ ... $
        content = re.sub(r'\\\(', '$', content)
        content = re.sub(r'\\\)', '$', content)
        
        return content
    
    def normalize_display_math(self, content: str) -> str:
        """
        Normalize display math to \\begin{equation} ... \\end{equation} format
        
        Args:
            content: LaTeX content
            
        Returns:
            Content with normalized display math
        """
        # Convert $$ ... $$ to \begin{equation*} ... \end{equation*}
        # Split by $$
        parts = content.split('$$')
        
        result = []
        for i, part in enumerate(parts):
            if i % 2 == 0:
                # Not in math mode
                result.append(part)
            else:
                # In math mode - convert to equation*
                result.append(r'\begin{equation*}' + part + r'\end{equation*}')
        
        return ''.join(result)
    
    def normalize_quotes(self, content: str) -> str:
        """
        Normalize LaTeX quotes to standard format
        
        Args:
            content: LaTeX content
            
        Returns:
            Content with normalized quotes
        """
        # Convert `` and '' to standard quotes (keep LaTeX style)
        # This is optional - LaTeX quotes are fine as-is
        return content
    
    def clean_whitespace(self, content: str) -> str:
        """
        Clean excessive whitespace while preserving paragraph breaks
        
        Args:
            content: LaTeX content
            
        Returns:
            Cleaned content
        """
        # Replace multiple spaces with single space
        content = re.sub(r' +', ' ', content)
        
        # Replace more than 2 newlines with 2 newlines (paragraph break)
        content = re.sub(r'\n\n+', '\n\n', content)
        
        # Remove trailing whitespace from lines
        lines = content.split('\n')
        lines = [line.rstrip() for line in lines]
        content = '\n'.join(lines)
        
        return content
    
    def remove_latex_command(self, content: str, command: str) -> str:
        """
        Remove specific LaTeX command and its arguments
        
        Args:
            content: LaTeX content
            command: Command name (without backslash)
            
        Returns:
            Content with command removed
        """
        # Pattern for \command{arg}
        pattern = r'\\' + re.escape(command) + r'\{[^}]*\}'
        content = re.sub(pattern, '', content)
        
        # Pattern for \command (no argument)
        pattern = r'\\' + re.escape(command) + r'(?![a-zA-Z])'
        content = re.sub(pattern, '', content)
        
        return content
    
    def clean_all(self, content: str) -> str:
        """
        Apply all cleaning operations
        
        Args:
            content: LaTeX content
            
        Returns:
            Fully cleaned content
        """
        content = self.remove_formatting_commands(content)
        content = self.normalize_inline_math(content)
        content = self.normalize_display_math(content)
        content = self.clean_whitespace(content)
        
        return content


def clean_latex_content(content: str) -> str:
    """
    Convenience function to clean LaTeX content
    
    Args:
        content: Raw LaTeX content
        
    Returns:
        Cleaned content
    """
    cleaner = LaTeXCleaner()
    return cleaner.clean_all(content)
