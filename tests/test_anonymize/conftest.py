"""Anonymization-specific test fixtures."""

from __future__ import annotations

import pytest

from junoscfg.anonymize.config import AnonymizeConfig

# Minimal IR with IP addresses for unit testing
SAMPLE_IR_WITH_IPS = {
    "configuration": {
        "system": {"host-name": "router1"},
        "interfaces": {
            "interface": [
                {
                    "name": "ge-0/0/0",
                    "unit": [
                        {
                            "name": "0",
                            "family": {
                                "inet": {
                                    "address": [{"name": "10.1.2.3/24"}],
                                },
                            },
                        },
                    ],
                },
            ],
        },
    },
}

# IR with multiple IP fields across different sections
SAMPLE_IR_MULTI_IP = {
    "configuration": {
        "system": {
            "host-name": "router1",
            "name-server": [{"name": "8.8.8.8"}, {"name": "8.8.4.4"}],
        },
        "interfaces": {
            "interface": [
                {
                    "name": "ge-0/0/0",
                    "unit": [
                        {
                            "name": "0",
                            "family": {
                                "inet": {
                                    "address": [{"name": "10.1.2.3/24"}],
                                },
                            },
                        },
                    ],
                },
                {
                    "name": "lo0",
                    "unit": [
                        {
                            "name": "0",
                            "family": {
                                "inet": {
                                    "address": [{"name": "192.168.1.1/32"}],
                                },
                            },
                        },
                    ],
                },
            ],
        },
    },
}


@pytest.fixture
def ip_config() -> AnonymizeConfig:
    """Config with only IP anonymization enabled and a fixed salt."""
    return AnonymizeConfig(ips=True, salt="test-salt-42")


@pytest.fixture
def sample_ir_ips() -> dict:
    """IR with IP addresses."""
    import copy

    return copy.deepcopy(SAMPLE_IR_WITH_IPS)


@pytest.fixture
def sample_ir_multi_ip() -> dict:
    """IR with multiple IP addresses."""
    import copy

    return copy.deepcopy(SAMPLE_IR_MULTI_IP)
