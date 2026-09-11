import os
import tempfile
from pathlib import Path

import pytest
import requests
from nanopub_testsuite_connector import NanopubTestSuite

from nanopub import NanopubConf, definitions, load_profile
from nanopub import __main__ as nanopub_cli
from nanopub.client import TEST_NANOPUB_QUERY_URL

_suite = NanopubTestSuite.get_latest()
_signing_key = _suite.get_signing_key("rsa-key1")


@pytest.fixture(scope="session")
def testsuite() -> NanopubTestSuite:
    return _suite


@pytest.fixture(autouse=True)
def nanopub_config_dir(monkeypatch, tmp_path) -> Path:
    """Point the user config dir at a temporary directory, for every test.

    Without this, the `setup` command exercised by `tests/test_cli.py` writes
    RSA keys and a profile into the developer's own `~/.nanopub`, overwriting
    the profile that is already there (see issue #269).

    `USER_CONFIG_DIR` and the paths derived from it are computed at import time,
    in `nanopub.definitions` and again in `nanopub.__main__`, so every one of
    those names has to be redirected. They are patched without `raising=False`
    on purpose: if one is ever renamed, the fixture should fail loudly rather
    than quietly stop isolating the home directory.
    """
    config_dir = tmp_path / ".nanopub"
    config_dir.mkdir()

    for module in (definitions, nanopub_cli):
        monkeypatch.setattr(module, "USER_CONFIG_DIR", config_dir)
        monkeypatch.setattr(module, "DEFAULT_PROFILE_PATH", config_dir / "profile.yml")
    monkeypatch.setattr(nanopub_cli, "DEFAULT_KEYS_PATH_PREFIX", config_dir / "id")
    monkeypatch.setattr(
        nanopub_cli, "DEFAULT_PRIVATE_KEY_PATH", config_dir / nanopub_cli.PRIVATE_KEY_FILE
    )
    monkeypatch.setattr(
        nanopub_cli, "DEFAULT_PUBLIC_KEY_PATH", config_dir / nanopub_cli.PUBLIC_KEY_FILE
    )

    return config_dir


def pytest_addoption(parser):
    parser.addoption('--no_rsa_key', action='store_true', default=False,
                     help="enable no_rsa_key decorated tests")


def pytest_configure(config):
    if not config.option.no_rsa_key:
        setattr(config.option, 'markexpr', 'not no_rsa_key')


def _is_nanopub_server_available() -> bool:
    try:
        response = requests.get(
            TEST_NANOPUB_QUERY_URL + 'RAkYh4UPJryajbtIDbLG-Bfd6A4JD2SbU9bmZdvaEdFRY/fdo-text-search?query=test',
            timeout=10)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


skip_if_nanopub_server_unavailable = (
    pytest.mark.skipif(
        not _is_nanopub_server_available(),
        reason='Nanopub server is unavailable'
    )
)

# Create a temporary profile.yml file for testing
profile_test_path = os.path.join(tempfile.mkdtemp(), "profile.yml")
profile_yaml = f"""orcid_id: https://orcid.org/0000-0000-0000-0000
name: Python Tests
public_key: {_signing_key.public_key}
private_key: {_signing_key.private_key}
introduction_nanopub_uri:
"""
with open(profile_test_path, "w") as f:
    f.write(profile_yaml)

profile_test = load_profile(profile_test_path)

default_conf = NanopubConf(
    profile=profile_test,
    use_test_server=True,
    add_prov_generated_time=False,
    add_pubinfo_generated_time=False,
    attribute_assertion_to_profile=True,
    attribute_publication_to_profile=True,
    assertion_attributed_to=None,
    publication_attributed_to=None,
    derived_from=None
)

testsuite_conf = NanopubConf(
    profile=profile_test,
    use_test_server=True,
    add_prov_generated_time=False,
    add_pubinfo_generated_time=False,
    attribute_assertion_to_profile=False,
    attribute_publication_to_profile=False,
)
