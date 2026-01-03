"""
Test Script
Quick tests to validate the pipeline components
"""
import sys
from pathlib import Path

# Add Source to path
sys.path.insert(0, str(Path(__file__).parent))

from latex_parser import parse_version_directory
from latex_cleaner import clean_latex_content
from hierarchy_builder import build_hierarchy_from_versions
from bibtex_processor import process_publication_references
from config import SAMPLE_DIR


def test_latex_parser():
    """Test LaTeX parser on one version"""
    print("\n" + "="*60)
    print("Testing LaTeX Parser")
    print("="*60)
    
    # Test on first publication
    test_pub = SAMPLE_DIR / "2310-15395"
    test_version = test_pub / "tex" / "2310-15395v1"
    
    if not test_version.exists():
        print("❌ Test version not found")
        return False
    
    result = parse_version_directory(test_version)
    
    print(f"✓ Main file: {result['main_file']}")
    print(f"✓ Included files: {len(result['included_files'])}")
    print(f"✓ Body length: {len(result['body'])} characters")
    print(f"✓ Preamble length: {len(result['preamble'])} characters")
    
    if result['body']:
        print("✅ LaTeX Parser working!")
        return True
    else:
        print("❌ LaTeX Parser failed - no body extracted")
        return False


def test_latex_cleaner():
    """Test LaTeX cleaner"""
    print("\n" + "="*60)
    print("Testing LaTeX Cleaner")
    print("="*60)
    
    test_content = r"""
    \centering
    \begin{table}[htpb]
    \midrule
    Some content here with $inline$ math.
    And $$display math$$ too.
    \end{table}
    """
    
    cleaned = clean_latex_content(test_content)
    
    print(f"Original length: {len(test_content)}")
    print(f"Cleaned length: {len(cleaned)}")
    
    # Check if formatting commands removed
    if r'\centering' not in cleaned and r'\midrule' not in cleaned:
        print("✅ LaTeX Cleaner working!")
        return True
    else:
        print("❌ LaTeX Cleaner failed - formatting commands still present")
        return False


def test_hierarchy_builder():
    """Test hierarchy builder"""
    print("\n" + "="*60)
    print("Testing Hierarchy Builder")
    print("="*60)
    
    # Test on first publication
    test_pub = SAMPLE_DIR / "2310-15395"
    test_version = test_pub / "tex" / "2310-15395v1"
    
    if not test_version.exists():
        print("❌ Test version not found")
        return False
    
    # Parse
    result = parse_version_directory(test_version)
    cleaned_body = clean_latex_content(result['body'])
    
    # Build hierarchy
    versions_data = {'v1': {'body': cleaned_body}}
    hierarchy = build_hierarchy_from_versions('2310-15395', versions_data)
    
    print(f"✓ Elements: {len(hierarchy['elements'])}")
    print(f"✓ Hierarchy versions: {len(hierarchy['hierarchy'])}")
    
    if hierarchy['elements']:
        # Print some sample elements
        print("\nSample elements:")
        for i, (elem_id, content) in enumerate(list(hierarchy['elements'].items())[:5]):
            print(f"  {i+1}. {elem_id}: {content[:80]}...")
        
        print("✅ Hierarchy Builder working!")
        return True
    else:
        print("❌ Hierarchy Builder failed - no elements created")
        return False


def test_bibtex_processor():
    """Test BibTeX processor"""
    print("\n" + "="*60)
    print("Testing BibTeX Processor")
    print("="*60)
    
    # Test on first publication
    test_pub = SAMPLE_DIR / "2310-15395"
    
    if not test_pub.exists():
        print("❌ Test publication not found")
        return False
    
    result = process_publication_references(test_pub)
    
    print(f"✓ Entries found: {len(result['entries'])}")
    print(f"✓ Key mappings: {len(result['key_mappings'])}")
    
    if result['entries']:
        # Print some sample entries
        print("\nSample entries:")
        for i, entry in enumerate(result['entries'][:3]):
            print(f"  {i+1}. {entry.cite_key} ({entry.entry_type})")
            if 'title' in entry.fields:
                print(f"      Title: {entry.fields['title'][:60]}...")
        
        print("✅ BibTeX Processor working!")
        return True
    else:
        print("❌ BibTeX Processor failed - no entries found")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("Running All Component Tests")
    print("="*60)
    
    tests = [
        ("LaTeX Parser", test_latex_parser),
        ("LaTeX Cleaner", test_latex_cleaner),
        ("Hierarchy Builder", test_hierarchy_builder),
        ("BibTeX Processor", test_bibtex_processor),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n❌ {test_name} crashed with error: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Pipeline is ready to use.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please fix before running full pipeline.")


if __name__ == '__main__':
    run_all_tests()
