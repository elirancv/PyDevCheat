"""Basic tests for PyDevCheat."""

def test_import():
    """Test that the package can be imported."""
    import pydevcheat
    assert pydevcheat.__version__ is not None

def test_main_app():
    """Test that the main app can be imported."""
    from pydevcheat.main import app
    assert app is not None 