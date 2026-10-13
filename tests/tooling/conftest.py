"""Explicit seams for synthetic repositories using the installed application."""

import pytest
from agent_ready_checks import verification_runtime

from tests.support.paths import PROJECT_ROOT


@pytest.fixture
def native_driver(monkeypatch):
    """Bind the real installed driver's root, separate from a synthetic candidate.

    These wrapper integration tests execute fixture inputs through the installed
    editable application. Observe the actual project's complete driver identity;
    the native candidate manifest still binds every synthetic repository input.
    No identity bytes, command execution, output hashes or stability checks are
    replaced by a constant or suppressed.
    """
    observe = verification_runtime.driver
    monkeypatch.setattr(verification_runtime, "driver", lambda root: observe(PROJECT_ROOT))
