"""Check package installation and the offline test configuration."""

from importlib.metadata import version
import socket
import subprocess
import sys

import pytest
from pytest_socket import SocketBlockedError


def test_installed_package_imports_outside_repository(tmp_path):
    """Import the installed package without relying on the working directory."""
    result = subprocess.run(
        [sys.executable, "-I", "-c", "import tennisage; print(tennisage.__version__)"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == version("tennisage")


@pytest.mark.filterwarnings("ignore:A test tried to use socket.socket:UserWarning")
def test_network_access_is_disabled():
    """Confirm that tests cannot create a network socket."""
    with pytest.raises(SocketBlockedError):
        with socket.socket():
            pass
