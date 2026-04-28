#!/usr/bin/env python3
"""Simple test for Obsidian sync functionality."""

import sys
import os

# Add scripts dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import importlib.util
spec = importlib.util.spec_from_file_location("archive_manager", "scripts/archive-manager.py")
am = importlib.util.module_from_spec(spec)
spec.loader.exec_module(am)
validate_obsidian_config = am.validate_obsidian_config
sync_to_obsidian = am.sync_to_obsidian
slugify = am.slugify

def test_validate_obsidian_config():
    """Test validate_obsidian_config with non-existent path."""
    is_valid, msg = validate_obsidian_config("/nonexistent/path")
    assert is_valid == False, f"Expected False for non-existent path, got {is_valid}"
    assert "不存在" in msg, f"Expected '不存在' in message, got {msg}"
    print("✓ validate_obsidian_config() correctly rejects non-existent path")

def test_sync_to_obsidian_missing_source():
    """Test sync_to_obsidian with non-existent source file."""
    result = sync_to_obsidian("/nonexistent/file.md", "/tmp", "test/")
    assert result["status"] == "error", f"Expected error status, got {result['status']}"
    assert "源文件不存在" in result["error"], f"Expected '源文件不存在', got {result['error']}"
    print("✓ sync_to_obsidian() correctly handles missing source file")

def test_slugify():
    """Test slugify function."""
    assert slugify("Claude Code") == "claude-code"
    assert slugify("SWE-bench") == "swe-bench"
    print("✓ slugify() works correctly")

def test_sync_to_obsidian_invalid_vault():
    """Test sync_to_obsidian with invalid vault path."""
    result = sync_to_obsidian("/tmp/test.md", "/nonexistent/vault", "test/")
    assert result["status"] == "error", f"Expected error status, got {result['status']}"
    assert result["action"] == "obsidian_sync"
    print("✓ sync_to_obsidian() correctly handles invalid vault")

if __name__ == "__main__":
    test_slugify()
    test_validate_obsidian_config()
    test_sync_to_obsidian_missing_source()
    test_sync_to_obsidian_invalid_vault()
    print("\n✅ All tests passed!")
