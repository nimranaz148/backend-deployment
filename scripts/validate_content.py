# scripts\validate_content.py
#!/usr/bin/env python3
"""
Content validation script for Physical AI & Humanoid Robotics textbook.

This script validates chapter structure, code blocks, and content quality
according to the 5-Step Concept Loop framework requirements.

Usage:
    python backend/scripts/validate_content.py
    python backend/scripts/validate_content.py --verbose
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple


def validate_learning_outcomes(content: str, filepath: Path) -> List[str]:
    """
    Validate that Learning Outcomes section exists near the beginning.
    
    Args:
        content: The markdown file content
        filepath: Path to the file being validated
        
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    lines = content.split("\n")
    first_50_lines = "\n".join(lines[:50])
    
    # Check for Learning Outcomes in various formats
    patterns = [
        r"##?\s*Learning\s+Outcomes?",
        r"##?\s*What\s+You['']ll\s+Learn",
        r"##?\s*Objectives",
    ]
    
    found = any(re.search(pattern, first_50_lines, re.IGNORECASE) for pattern in patterns)
    
    if not found:
        errors.append(f"{filepath.name}: Missing 'Learning Outcomes' section in first 50 lines")
    
    return errors


def validate_assessments(content: str, filepath: Path) -> List[str]:
    """
    Validate that Assessments section exists near the end.
    
    Args:
        content: The markdown file content
        filepath: Path to the file being validated
        
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    lines = content.split("\n")
    last_100_lines = "\n".join(lines[-100:])
    
    # Check for Assessments in various formats
    patterns = [
        r"##?\s*Assessments?",
        r"##?\s*Exercises?",
        r"##?\s*Questions?",
        r"##?\s*Review",
    ]
    
    found = any(re.search(pattern, last_100_lines, re.IGNORECASE) for pattern in patterns)
    
    if not found:
        errors.append(f"{filepath.name}: Missing 'Assessments' section in last 100 lines")
    
    return errors


def validate_code_blocks(content: str, filepath: Path) -> List[str]:
    """
    Validate that all code blocks have language specifiers.
    
    Args:
        content: The markdown file content
        filepath: Path to the file being validated
        
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    # Find all code block openings
    code_block_pattern = r"```(\w*)\n"
    matches = re.findall(code_block_pattern, content)
    
    for i, lang in enumerate(matches, 1):
        if not lang:
            errors.append(f"{filepath.name}: Code block #{i} missing language specifier")
    
    return errors


def validate_header_hierarchy(content: str, filepath: Path) -> List[str]:
    """
    Validate that headers follow proper hierarchy (no skipped levels).
    
    Args:
        content: The markdown file content
        filepath: Path to the file being validated
        
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    # Extract all headers with their levels
    header_pattern = r"^(#{1,6})\s+(.+)$"
    headers = re.findall(header_pattern, content, re.MULTILINE)
    
    if not headers:
        return errors
    
    prev_level = 0
    for hashes, title in headers:
        level = len(hashes)
        
        # Check for skipped levels (e.g., h1 -> h3)
        if prev_level > 0 and level > prev_level + 1:
            errors.append(
                f"{filepath.name}: Header hierarchy skip from h{prev_level} to h{level} "
                f"at '{title[:30]}...'"
            )
        
        prev_level = level
    
    return errors


def validate_mermaid_diagrams(content: str, filepath: Path) -> List[str]:
    """
    Check if technical chapters contain Mermaid diagrams.
    
    Args:
        content: The markdown file content
        filepath: Path to the file being validated
        
    Returns:
        List of warning messages (not errors, just informational)
    """
    warnings = []
    
    # Check if this is a technical chapter (contains code or architecture discussion)
    is_technical = (
        "```python" in content or 
        "```xml" in content or
        "architecture" in content.lower() or
        "system" in content.lower()
    )
    
    has_mermaid = "```mermaid" in content
    
    if is_technical and not has_mermaid and len(content) > 1000:
        warnings.append(f"{filepath.name}: Technical chapter without Mermaid diagrams (recommended)")
    
    return warnings


def validate_admonitions(content: str, filepath: Path) -> List[str]:
    """
    Check if hardware-related chapters use Docusaurus admonitions.
    
    Args:
        content: The markdown file content
        filepath: Path to the file being validated
        
    Returns:
        List of warning messages
    """
    warnings = []
    
    # Check if this discusses hardware
    hardware_keywords = ["gpu", "ram", "cpu", "nvidia", "jetson", "rtx", "vram"]
    discusses_hardware = any(kw in content.lower() for kw in hardware_keywords)
    
    # Check for admonitions
    admonition_pattern = r":::(warning|danger|tip|note|info)"
    has_admonitions = bool(re.search(admonition_pattern, content))
    
    if discusses_hardware and not has_admonitions:
        warnings.append(f"{filepath.name}: Hardware discussion without admonitions (recommended)")
    
    return warnings


def validate_chapter(filepath: Path, verbose: bool = False) -> Tuple[List[str], List[str]]:
    """
    Validate a single chapter file.
    
    Args:
        filepath: Path to the markdown file
        verbose: Whether to include warnings
        
    Returns:
        Tuple of (errors, warnings)
    """
    content = filepath.read_text(encoding="utf-8")
    
    # Skip very short files (likely placeholders)
    if len(content) < 100:
        return [f"{filepath.name}: File too short ({len(content)} chars), likely placeholder"], []
    
    errors = []
    warnings = []
    
    # Run all validations
    errors.extend(validate_learning_outcomes(content, filepath))
    errors.extend(validate_assessments(content, filepath))
    errors.extend(validate_code_blocks(content, filepath))
    errors.extend(validate_header_hierarchy(content, filepath))
    
    if verbose:
        warnings.extend(validate_mermaid_diagrams(content, filepath))
        warnings.extend(validate_admonitions(content, filepath))
    
    return errors, warnings


def main():
    """Main entry point for content validation."""
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    
    # Find docs directory
    docs_path = Path("docs/docs")
    if not docs_path.exists():
        # Try from backend directory
        docs_path = Path("../docs/docs")
    
    if not docs_path.exists():
        print("ERROR: Could not find docs/docs directory")
        sys.exit(1)
    
    print(f"Validating content in: {docs_path.absolute()}")
    print("=" * 60)
    
    all_errors = []
    all_warnings = []
    files_checked = 0
    
    # Find all markdown files
    for chapter in sorted(docs_path.glob("**/*.md")):
        # Skip category files and hidden files
        if chapter.name.startswith("_") or chapter.name.startswith("."):
            continue
        
        files_checked += 1
        errors, warnings = validate_chapter(chapter, verbose)
        all_errors.extend(errors)
        all_warnings.extend(warnings)
    
    # Print results
    print(f"\nFiles checked: {files_checked}")
    print("-" * 60)
    
    if all_errors:
        print(f"\n❌ ERRORS ({len(all_errors)}):")
        for error in all_errors:
            print(f"  • {error}")
    
    if verbose and all_warnings:
        print(f"\n⚠️  WARNINGS ({len(all_warnings)}):")
        for warning in all_warnings:
            print(f"  • {warning}")
    
    if not all_errors:
        print("\n✅ All chapters validated successfully!")
        sys.exit(0)
    else:
        print(f"\n❌ Validation failed with {len(all_errors)} error(s)")
        sys.exit(1)


if __name__ == "__main__":
    main()
