"""
Unit tests for core module
"""
import pytest


def test_module_import():
    """Test that core module can be imported"""
    # This test will fail until we create the module
    import core

    assert core.__version__ is not None
    assert core.__author__ is not None


def test_project_metadata():
    """Test project metadata"""
    from core import __version__, __author__

    assert isinstance(__version__, str)
    assert isinstance(__author__, str)
    assert __version__ == "0.1.0"
    assert __author__ == "zhengying"
