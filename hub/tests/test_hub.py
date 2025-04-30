import os
import sys

import hub.wsgi
from hub.settings import is_testing


def test_import_wsgi() -> None:
    """Test if the WSGI application is imported correctly."""
    assert hasattr(hub.wsgi, "application")


def test_enviroment() -> None:
    """Test if the environment variable is set correctly."""
    print(
        "is_testing conditions:",
        {
            "test in sys.argv": "test" in sys.argv,
            "pytest in sys.argv": "pytest" in sys.argv,
            "RUNNING_TESTS": os.getenv("RUNNING_TESTS"),
            "DJANGO_SETTINGS_MODULE": os.getenv("DJANGO_SETTINGS_MODULE"),
            "PYTEST_CURRENT_TEST": os.environ.get("PYTEST_CURRENT_TEST"),
            "ENVIRONMENT": os.getenv("ENVIRONMENT"),
        },
    )
    assert is_testing is True, (
        f"Environment variable RUNNING_TESTS should be set to 1. Current values: "
        f"RUNNING_TESTS={os.getenv('RUNNING_TESTS')}, "
        f"ENVIRONMENT={os.getenv('ENVIRONMENT')}, "
        f"DJANGO_SETTINGS_MODULE={os.getenv('DJANGO_SETTINGS_MODULE')}"
    )
