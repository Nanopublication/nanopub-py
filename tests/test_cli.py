import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from nanopub.__main__ import cli, validate_orcid_id
from nanopub._version import __version__
from nanopub.definitions import DEFAULT_PROFILE_PATH
from tests.conftest import TEST_RESOURCES_FILEPATH

runner = CliRunner()

PRIVATE_KEY_PATH = os.path.join(TEST_RESOURCES_FILEPATH, "id_rsa")


def test_validate_orcid_id():
    valid_ids = [
        "https://orcid.org/1234-5678-1234-5678",
        "https://orcid.org/1234-5678-1234-567X",
    ]
    for orcid_id in valid_ids:
        assert validate_orcid_id(ctx=None, param=None, orcid_id=orcid_id) == orcid_id

    invalid_ids = [
        "https://orcid.org/abcd-efgh-abcd-efgh",
        "https://orcid.org/1234-5678-1234-567",
        "https://orcid.org/1234-5678-1234-56789",
        "https://other-url.org/1234-5678-1234-5678",
        "0000-0000-0000-0000",
    ]
    for orcid_id in invalid_ids:
        with pytest.raises(ValueError):
            validate_orcid_id(ctx=None, param=None, orcid_id=orcid_id)


def test_setup():
    # np setup --orcid-id https://orcid.org/0000-0000-0000-0000 --name "Python test" --newkeys --no-publish
    result = runner.invoke(
        cli,
        [
            "setup",
            "--orcid-id",
            "https://orcid.org/0000-0000-0000-0000",
            "--name",
            "Python test",
            "--newkeys",
            "--no-publish",
        ],
    )
    assert result.exit_code == 1
    assert "Setting up nanopub profile" in result.stdout
    assert Path(DEFAULT_PROFILE_PATH).exists()


def test_profile():
    result = runner.invoke(
        cli,
        [
            "profile",
        ],
    )
    assert "User profile in" in result.stdout


def test_publish():
    test_file = "./tests/testsuite/valid/plain/simple1.trig"
    result = runner.invoke(cli, ["publish", test_file, "--test"])
    assert result.exit_code == 0
    assert "Nanopub published at" in result.stdout


def test_sign_with_key():
    test_file = "./tests/testsuite/valid/plain/simple1.trig"
    result = runner.invoke(
        cli,
        [
            "sign",
            test_file,
            "-k",
            PRIVATE_KEY_PATH,
        ],
    )
    assert result.exit_code == 0
    assert "Nanopub signed in" in result.stdout


def test_version():
    result = runner.invoke(cli, ["version"])
    assert result.exit_code == 0
    assert __version__ == result.stdout.strip()
