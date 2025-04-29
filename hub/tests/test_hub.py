from hub.settings import is_testing
import hub.wsgi


def test_import_wsgi() -> None:
    """Test if the WSGI application is imported correctly."""
    assert hasattr(hub.wsgi, "application")

def test_enviroment() -> None:
    """Test if the environment variable is set correctly."""
    assert is_testing is True, "Environment variable RUNNING_TESTS should be set to 1"
