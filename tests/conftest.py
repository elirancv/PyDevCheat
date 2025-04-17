"""Pytest configuration file."""

def pytest_configure(config):
    """Register custom pytest marks."""
    config.addinivalue_line("markers", "timeout: mark test with timeout in seconds") 