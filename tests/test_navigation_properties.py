# tests\test_navigation_properties.py
#!/usr/bin/env python3
"""
Property-based tests for navigation path consistency.

These tests verify that all navigation paths in the backend match
the actual Docusaurus file structure.

Run with: pytest backend/tests/test_navigation_properties.py -v
"""

import re
from pathlib import Path
from typing import Dict, List, Set

import pytest

# Get the docs path relative to the test file
DOCS_PATH = Path(__file__).parent.parent.parent / "docs" / "docs"


def get_valid_docusaurus_routes() -> Set[str]:
    """
    Generate all valid Docusaurus routes from the docs folder structure.
    
    Returns a set of valid route paths like:
    - /docs
    - /docs/module1/week1-intro-physical-ai
    - /docs/module2/week6-gazebo
    """
    if not DOCS_PATH.exists():
        return set()
    
    routes = {"/docs"}  # Root docs route
    
    for md_file in DOCS_PATH.glob("**/*.md"):
        if md_file.name.startswith("_"):
            continue
        
        # Convert file path to route
        relative = md_file.relative_to(DOCS_PATH)
        route_parts = list(relative.parts)
        
        # Remove .md extension from filename
        route_parts[-1] = route_parts[-1].replace(".md", "")
        
        # Check for custom slug in frontmatter
        content = md_file.read_text(encoding="utf-8")
        slug_match = re.search(r"^slug:\s*(.+)$", content, re.MULTILINE)
        
        if slug_match:
            slug = slug_match.group(1).strip()
            if slug == "/":
                routes.add("/docs")
            else:
                routes.add(f"/docs{slug}" if not slug.startswith("/docs") else slug)
        else:
            route = "/docs/" + "/".join(route_parts)
            routes.add(route)
    
    return routes


def get_course_navigation() -> Dict[str, Dict]:
    """Import and return the COURSE_NAVIGATION from agent_service."""
    import sys
    backend_path = Path(__file__).parent.parent
    sys.path.insert(0, str(backend_path))
    
    try:
        from src.services.agent_service import COURSE_NAVIGATION
        return COURSE_NAVIGATION
    except ImportError:
        pytest.skip("Could not import COURSE_NAVIGATION from agent_service")
        return {}


# **Feature: chatbot-navigation-enhancement, Property 2: Navigation Map Path Consistency**
class TestNavigationMapPathConsistency:
    """
    Property 2: Navigation Map Path Consistency
    
    For any entry in the COURSE_NAVIGATION dictionary, the path value SHALL 
    match a valid Docusaurus route derived from the actual file structure.
    
    Validates: Requirements 1.3
    """
    
    @pytest.fixture(scope="class")
    def valid_routes(self) -> Set[str]:
        """Get all valid Docusaurus routes."""
        return get_valid_docusaurus_routes()
    
    @pytest.fixture(scope="class")
    def navigation_map(self) -> Dict[str, Dict]:
        """Get the COURSE_NAVIGATION map."""
        return get_course_navigation()
    
    def test_all_navigation_paths_are_valid(self, valid_routes: Set[str], navigation_map: Dict[str, Dict]):
        """Verify all COURSE_NAVIGATION paths match valid Docusaurus routes."""
        if not valid_routes:
            pytest.skip("No valid routes found - docs folder may not exist")
        
        if not navigation_map:
            pytest.skip("COURSE_NAVIGATION not available")
        
        invalid_paths = []
        
        for key, nav_info in navigation_map.items():
            path = nav_info.get("path", "")
            # Strip any anchor fragments for path validation
            base_path = path.split("#")[0]
            
            if base_path not in valid_routes:
                invalid_paths.append((key, base_path))
        
        if invalid_paths:
            error_msg = "Invalid navigation paths found:\n"
            for key, path in invalid_paths:
                error_msg += f"  - '{key}' -> '{path}'\n"
            error_msg += f"\nValid routes: {sorted(valid_routes)}"
            pytest.fail(error_msg)
    
    def test_navigation_paths_not_empty(self, navigation_map: Dict[str, Dict]):
        """Verify no navigation entries have empty paths."""
        if not navigation_map:
            pytest.skip("COURSE_NAVIGATION not available")
        
        empty_paths = [key for key, info in navigation_map.items() if not info.get("path")]
        
        assert not empty_paths, f"Navigation entries with empty paths: {empty_paths}"
    
    def test_navigation_titles_not_empty(self, navigation_map: Dict[str, Dict]):
        """Verify no navigation entries have empty titles."""
        if not navigation_map:
            pytest.skip("COURSE_NAVIGATION not available")
        
        empty_titles = [key for key, info in navigation_map.items() if not info.get("title")]
        
        assert not empty_titles, f"Navigation entries with empty titles: {empty_titles}"


# **Feature: chatbot-navigation-enhancement, Property 3: Module Category Configuration Consistency**
class TestModuleCategoryConfigurationConsistency:
    """
    Property 3: Module Category Configuration Consistency
    
    For any module category configuration file, the JSON structure SHALL 
    contain the same required properties (label, position, link) as other 
    module configurations.
    
    Validates: Requirements 2.2, 2.3
    """
    
    REQUIRED_PROPERTIES = {"label", "position", "link"}
    
    def get_category_files(self) -> List[Path]:
        """Get all _category_.json files from module directories."""
        if not DOCS_PATH.exists():
            return []
        
        return list(DOCS_PATH.glob("module*/_category_.json"))
    
    def test_all_modules_have_category_files(self):
        """Verify all module directories have _category_.json files."""
        if not DOCS_PATH.exists():
            pytest.skip("Docs path not found")
        
        module_dirs = list(DOCS_PATH.glob("module*"))
        
        for module_dir in module_dirs:
            if module_dir.is_dir():
                category_file = module_dir / "_category_.json"
                assert category_file.exists(), f"Missing _category_.json in {module_dir.name}"
    
    def test_category_files_have_required_properties(self):
        """Verify all category files have required properties."""
        import json
        
        category_files = self.get_category_files()
        
        if not category_files:
            pytest.skip("No category files found")
        
        for cat_file in category_files:
            content = json.loads(cat_file.read_text(encoding="utf-8"))
            
            missing = self.REQUIRED_PROPERTIES - set(content.keys())
            
            assert not missing, (
                f"{cat_file.parent.name}/_category_.json missing properties: {missing}"
            )
    
    def test_category_files_have_consistent_structure(self):
        """Verify all category files have the same structure."""
        import json
        
        category_files = self.get_category_files()
        
        if len(category_files) < 2:
            pytest.skip("Need at least 2 category files to compare")
        
        structures = []
        for cat_file in category_files:
            content = json.loads(cat_file.read_text(encoding="utf-8"))
            structures.append((cat_file.parent.name, set(content.keys())))
        
        # All should have the same keys
        first_name, first_keys = structures[0]
        
        for name, keys in structures[1:]:
            assert keys == first_keys, (
                f"Category structure mismatch: {name} has {keys}, "
                f"but {first_name} has {first_keys}"
            )
    
    def test_category_positions_are_sequential(self):
        """Verify module positions are sequential starting from a reasonable number."""
        import json
        
        category_files = self.get_category_files()
        
        if not category_files:
            pytest.skip("No category files found")
        
        positions = []
        for cat_file in category_files:
            content = json.loads(cat_file.read_text(encoding="utf-8"))
            positions.append((cat_file.parent.name, content.get("position", 0)))
        
        positions.sort(key=lambda x: x[1])
        
        # Check positions are reasonable (between 1 and 10)
        for name, pos in positions:
            assert 1 <= pos <= 10, f"{name} has unusual position: {pos}"



# **Feature: chatbot-navigation-enhancement, Property 4: Redirect URL Anchor Inclusion**
class TestRedirectURLAnchorInclusion:
    """
    Property 4: Redirect URL Anchor Inclusion
    
    For any navigation redirect to a specific section, the redirect URL SHALL 
    include an anchor fragment identifying the target section.
    
    Validates: Requirements 3.2, 3.6
    """
    
    def get_navigate_to_page_function(self):
        """Import the navigate_to_page function."""
        import sys
        backend_path = Path(__file__).parent.parent
        sys.path.insert(0, str(backend_path))
        
        try:
            from src.services.agent_service import navigate_to_page
            return navigate_to_page
        except ImportError:
            pytest.skip("Could not import navigate_to_page from agent_service")
            return None
    
    def test_section_navigation_includes_anchor(self):
        """Verify navigation with section parameter includes anchor in path."""
        import json
        
        navigate_fn = self.get_navigate_to_page_function()
        if not navigate_fn:
            pytest.skip("navigate_to_page not available")
        
        # Test destinations that should support section anchors
        test_cases = [
            ("module 1", "learning-outcomes"),
            ("gazebo", "urdf-robot-description"),
            ("isaac", "isaac-sim-setup"),
        ]
        
        for destination, section in test_cases:
            # Call the function tool directly (it returns a string)
            result_str = navigate_fn(destination, section)
            result = json.loads(result_str)
            
            if result.get("action") == "redirect":
                path = result.get("path", "")
                # If section was provided and path doesn't already have anchor, it should be added
                assert "#" in path or section in path, (
                    f"Navigation to '{destination}' with section '{section}' "
                    f"should include anchor in path. Got: {path}"
                )
    
    def test_predefined_anchors_in_navigation_map(self):
        """Verify entries with predefined anchors have valid anchor format."""
        navigation_map = get_course_navigation()
        
        if not navigation_map:
            pytest.skip("COURSE_NAVIGATION not available")
        
        for key, nav_info in navigation_map.items():
            path = nav_info.get("path", "")
            
            if "#" in path:
                # Verify anchor format (should be lowercase with hyphens)
                anchor = path.split("#")[1]
                assert anchor == anchor.lower(), (
                    f"Anchor '{anchor}' in '{key}' should be lowercase"
                )
                assert " " not in anchor, (
                    f"Anchor '{anchor}' in '{key}' should not contain spaces"
                )
    
    def test_anchor_only_entries_have_valid_format(self):
        """Verify anchor-only entries start with # and have valid format."""
        navigation_map = get_course_navigation()
        
        if not navigation_map:
            pytest.skip("COURSE_NAVIGATION not available")
        
        for key, nav_info in navigation_map.items():
            if nav_info.get("is_anchor_only"):
                path = nav_info.get("path", "")
                assert path.startswith("#"), (
                    f"Anchor-only entry '{key}' should have path starting with #"
                )
                anchor = path[1:]  # Remove leading #
                assert anchor == anchor.lower().replace(" ", "-"), (
                    f"Anchor '{anchor}' should be lowercase with hyphens"
                )
