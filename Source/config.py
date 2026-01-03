"""
Configuration file for the project
"""
import os
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Data directories
SAMPLE_DIR = PROJECT_ROOT / "sample"
OUTPUT_DIR = PROJECT_ROOT / "output"  # Replace with your MSSV

# Ensure output directory exists
OUTPUT_DIR.mkdir(exist_ok=True)

# LaTeX parsing settings
LATEX_SECTION_COMMANDS = [
    r'\chapter',
    r'\section',
    r'\subsection',
    r'\subsubsection',
    r'\paragraph',
    r'\subparagraph'
]

# Keywords to identify sections to exclude/include
EXCLUDE_SECTIONS = ['references', 'bibliography']
INCLUDE_UNNUMBERED_SECTIONS = ['acknowledgements', 'acknowledgment', 'appendix', 'appendices']

# Mathematical environments
MATH_BLOCK_ENVS = [
    'equation', 'equation*', 'align', 'align*', 'gather', 'gather*',
    'multline', 'multline*', 'eqnarray', 'eqnarray*', 'displaymath'
]

# Figure/Table environments
FIGURE_ENVS = ['figure', 'figure*', 'table', 'table*']

# List environments
LIST_ENVS = ['itemize', 'enumerate', 'description']

# Machine Learning settings
ML_TRAIN_TEST_SPLIT = 0.2  # 20% for test
ML_VALIDATION_SPLIT = 0.1  # 10% for validation
ML_TOP_K_PREDICTIONS = 5  # Top 5 candidates

# Manual labeling requirements
MIN_MANUAL_PUBLICATIONS = 5
MIN_MANUAL_PAIRS = 20
AUTO_LABEL_PERCENTAGE = 0.1  # 10% of remaining data

# Feature engineering settings
FEATURE_SIMILARITY_THRESHOLD = 0.8
MAX_TITLE_LENGTH = 200
MAX_AUTHOR_COUNT = 50
