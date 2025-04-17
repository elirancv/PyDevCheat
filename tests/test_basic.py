"""Basic tests for PyDevCheat."""

import pytest
from pathlib import Path
import json
import tempfile
import time
from unittest.mock import patch, MagicMock
from pydevcheat import __version__, PyDevCheat
from pydevcheat.main import (
    app,
    wrap_text,
    load_cache,
    save_cache,
    CACHE_DIR,
    tldr_source,
    cheatsh_source,
    devhints_source
)
from typer.testing import CliRunner
import requests.exceptions
import os
from pydevcheat.utils import with_timeout
from pydevcheat.sources import TLDRSource
from pydevcheat.exceptions import SourceError, NetworkError

# Basic package tests
def test_import():
    """Test that the package can be imported."""
    assert PyDevCheat is not None

def test_main_app():
    """Test that the main app is initialized."""
    app = PyDevCheat()
    assert app is not None

# Utility function tests
def test_wrap_text():
    """Test text wrapping with long text."""
    text = "This is a very long text that should be wrapped at 20 characters"
    wrapped = wrap_text(text, width=20)
    assert all(len(line) <= 20 for line in wrapped.split('\n'))

def test_wrap_text_short():
    """Test text wrapping with short text."""
    text = "Short text"
    wrapped = wrap_text(text, width=20)
    assert wrapped == text

def test_wrap_text_empty():
    """Test wrapping empty text."""
    assert wrap_text("", 20) == ""

def test_wrap_text_single_long_word():
    """Test wrapping a single long word."""
    long_word = "supercalifragilisticexpialidocious"
    wrapped = wrap_text(long_word, 10)
    lines = wrapped.split('\n')
    assert len(lines) > 1
    assert ''.join(lines) == long_word

def test_wrap_text_special_chars():
    """Test wrapping text with special characters."""
    text = "Line 1\nLine 2\tTabbed"
    wrapped = wrap_text(text, 20)
    lines = wrapped.split('\n')
    assert len(lines) >= 2
    assert all(len(line) <= 20 for line in lines)

def test_timeout_success():
    """Test successful execution within timeout."""
    def quick_func():
        return "success"
    
    result = with_timeout(quick_func, timeout=1)
    assert result == "success"

def test_timeout_failure():
    """Test timeout exception for long-running function."""
    def slow_func():
        time.sleep(2)
        return "success"
    
    with pytest.raises(TimeoutError):
        with_timeout(slow_func, timeout=1)

# Cache management tests
@pytest.fixture
def temp_cache_dir():
    """Fixture to create a temporary cache directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_cache_operations(temp_cache_dir):
    """Test loading and saving cache."""
    app = PyDevCheat(cache_dir=temp_cache_dir)
    assert os.path.exists(temp_cache_dir)
    
    # Test cache file creation
    cache_file = os.path.join(temp_cache_dir, "tldr_cache.json")
    app.sources["tldr"].save_cache({"test": "data"})
    assert os.path.exists(cache_file)
    
    # Test cache loading
    loaded_cache = app.sources["tldr"].load_cache()
    assert loaded_cache == {"test": "data"}

def test_load_cache_nonexistent():
    """Test loading cache when file doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_cache = Path(tmpdir) / "nonexistent.json"
        with patch('pydevcheat.main.CACHE_FILE', temp_cache):
            assert load_cache() == {}

def test_cache_corruption():
    """Test handling of corrupted cache file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_cache = Path(tmpdir) / "corrupt_cache.json"
        temp_cache.write_text("invalid json content")
        
        with patch('pydevcheat.main.CACHE_FILE', temp_cache):
            assert load_cache() == {}

def test_cache_permission_error():
    """Test handling of permission errors during cache operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_cache = Path(tmpdir) / "protected_cache.json"
        
        with patch('pydevcheat.main.CACHE_FILE', temp_cache), \
             patch('pathlib.Path.open', side_effect=PermissionError):
            assert load_cache() == {}
            save_cache({"test": "data"})  # Should not raise exception

# CLI tests
@pytest.fixture
def runner():
    return CliRunner()

def test_cheat_command_basic(runner):
    """Test basic cheat command execution."""
    with patch('pydevcheat.main.tldr_source') as mock_tldr:
        mock_tldr.search.return_value = "# Test\ncommand # description"
        result = runner.invoke(app, ["cheat", "test"])
        assert result.exit_code == 0
        mock_tldr.search.assert_called_once_with("test")

def test_cheat_command_source_selection(runner):
    """Test cheat command with different sources."""
    sources = {
        "tldr": tldr_source,
        "cheatsh": cheatsh_source,
        "devhints": devhints_source
    }
    
    for source_name, source_obj in sources.items():
        with patch.object(source_obj, 'search', return_value="# Test\ncommand # description"):
            result = runner.invoke(app, ["cheat", "test", "--source", source_name])
            assert result.exit_code == 0

def test_cheat_command_copy_option(runner):
    """Test copy to clipboard option."""
    test_content = "# Test\ncommand # description"
    with patch('pydevcheat.main.tldr_source') as mock_tldr, \
         patch('pyperclip.copy') as mock_copy:
        mock_tldr.search.return_value = test_content
        result = runner.invoke(app, ["cheat", "test", "--copy"])
        assert result.exit_code == 0
        mock_copy.assert_called_once_with(test_content)

def test_cheat_command_invalid_source(runner):
    """Test cheat command with invalid source."""
    result = runner.invoke(app, ["cheat", "test", "--source", "invalid"])
    assert result.exit_code == 1
    assert "Unknown source" in result.stdout

def test_cheat_command_no_results(runner):
    """Test cheat command when no results are found."""
    with patch('pydevcheat.main.tldr_source') as mock_tldr:
        mock_tldr.search.return_value = None
        result = runner.invoke(app, ["cheat", "nonexistent"])
        assert result.exit_code == 1
        assert "No results found" in result.stdout

def test_cheat_command_network_error(runner):
    """Test handling of network errors."""
    with patch('pydevcheat.main.cheatsh_source') as mock_source:
        mock_source.search.side_effect = requests.exceptions.RequestException
        result = runner.invoke(app, ["cheat", "test", "--source", "cheatsh"])
        assert result.exit_code == 1
        assert "Network error" in result.stdout

def test_cheat_command_timeout(runner):
    """Test command timeout handling."""
    with patch('pydevcheat.main.tldr_source') as mock_source:
        def slow_search(*args):
            time.sleep(5)
            return "result"
        
        mock_source.search.side_effect = slow_search
        with patch('pydevcheat.main.SEARCH_TIMEOUT', 1):
            result = runner.invoke(app, ["cheat", "test"])
            assert result.exit_code == 1
            assert "Search timed out" in result.stdout

def test_cheat_command_argument_validation(runner):
    """Test command argument validation."""
    # Test empty query
    result = runner.invoke(app, ["cheat", ""])
    assert result.exit_code == 1
    assert "Query cannot be empty" in result.stdout
    
    # Test very long query
    long_query = "a" * 1000
    result = runner.invoke(app, ["cheat", long_query])
    assert result.exit_code == 1
    assert "Query too long" in result.stdout

# Source tests
def test_source_initialization():
    """Test source initialization."""
    app = PyDevCheat()
    assert isinstance(app.sources["tldr"], TLDRSource)

def test_cache_directory_creation():
    """Test if cache directory is created."""
    assert CACHE_DIR.exists()
    assert CACHE_DIR.is_dir()

# Source-specific tests
def test_tldr_source_cache():
    """Test TLDR source caching mechanism."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir)
        cache_file = cache_dir / "tldr_cache.json"
        tldr_source = TLDRSource(cache_dir=cache_dir)

        # Mock the httpx.get call
        test_content = "# test\n> Description\n- Example:\n`command`"
        with patch('httpx.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = test_content
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            # First search should create cache
            result = tldr_source.search("test")
            assert cache_file.exists()

            # Get the initial modification time
            mtime = cache_file.stat().st_mtime

            # Second search should use cache
            result = tldr_source.search("test")
            assert cache_file.stat().st_mtime == mtime  # Cache file should not be modified

def test_cheatsh_rate_limiting():
    """Test cheat.sh rate limiting."""
    for _ in range(3):
        cheatsh_source.search("test")
    
    start_time = time.time()
    cheatsh_source.search("test")
    elapsed = time.time() - start_time
    assert elapsed >= 1.5  # More lenient timing check

def test_devhints_formatting():
    """Test devhints response formatting."""
    test_content = "## Title\n* Item 1\n* Item 2"
    with patch('pydevcheat.sources.devhints.DevhintsSource._make_request') as mock_request:
        mock_request.return_value = test_content
        result = devhints_source.search("test")
        assert result is not None
        assert "Title" in result
        assert "Item 1" in result
        assert "Item 2" in result

# Error handling and formatting tests
def test_error_message_formatting():
    """Test error message formatting."""
    with patch('pydevcheat.main.format_error') as mock_format:
        runner = CliRunner()
        runner.invoke(app, ["cheat", "nonexistent"])
        mock_format.assert_called_once()
        args = mock_format.call_args[0][0]
        assert isinstance(args, str)
        assert len(args) > 0

# Performance tests
@pytest.mark.timeout(5)
def test_search_performance():
    """Test search performance."""
    with patch('pydevcheat.sources.tldr.TLDRSource.search') as mock_search:
        mock_search.return_value = "Test result"
        start_time = time.time()
        tldr_source.search("common_command")
        elapsed = time.time() - start_time
        assert elapsed < 2.0  # Search should complete within 2 seconds

@patch('pyperclip.copy')
def test_cheat_command_success(mock_copy):
    """Test successful cheat command execution."""
    app = PyDevCheat()
    mock_source = MagicMock()
    mock_source.search.return_value = "Test result"
    app.sources["tldr"] = mock_source
    
    result = app.cheat("test query", copy_to_clipboard=True)
    assert result == "Test result"
    mock_copy.assert_called_once_with("Test result")
    mock_source.search.assert_called_once_with("test query")

@patch('pyperclip.copy')
def test_cheat_command_no_results(mock_copy):
    """Test cheat command with no results."""
    app = PyDevCheat()
    mock_source = MagicMock()
    mock_source.search.return_value = None
    app.sources["tldr"] = mock_source
    
    with pytest.raises(SourceError) as exc_info:
        app.cheat("nonexistent query")
    assert "No results found" in str(exc_info.value)
    mock_copy.assert_not_called()

@patch('pyperclip.copy')
def test_cheat_command_network_error(mock_copy):
    """Test cheat command with network error."""
    app = PyDevCheat()
    mock_source = MagicMock()
    mock_source.search.side_effect = NetworkError("Network error")
    app.sources["tldr"] = mock_source
    
    with pytest.raises(NetworkError) as exc_info:
        app.cheat("test query")
    assert "Network error" in str(exc_info.value)
    mock_copy.assert_not_called()

def test_cache_dir_creation():
    """Test cache directory creation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = os.path.join(tmpdir, "cache")
        app = PyDevCheat(cache_dir=cache_dir)
        assert os.path.exists(cache_dir) 