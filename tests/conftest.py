import os
import tempfile

import pytest
import requests

from nanopub import NanopubConf, load_profile
from nanopub.client import TEST_NANOPUB_QUERY_URL
from nanopub.definitions import TEST_RESOURCES_FILEPATH
from tests.java_wrapper import JavaWrapper


def pytest_addoption(parser):
    parser.addoption('--no_rsa_key', action='store_true', default=False,
                     help="enable no_rsa_key decorated tests")


def pytest_configure(config):
    if not config.option.no_rsa_key:
        setattr(config.option, 'markexpr', 'not no_rsa_key')


skip_if_nanopub_server_unavailable = (
    pytest.mark.skipif(
        requests.get(TEST_NANOPUB_QUERY_URL + 'RAkYh4UPJryajbtIDbLG-Bfd6A4JD2SbU9bmZdvaEdFRY/fdo-text-search?query=test').status_code != 200,
        reason='Nanopub server is unavailable'
    )
)


# Create a temporary profile.yml file for testing
profile_test_path = os.path.join(tempfile.mkdtemp(), "profile.yml")
profile_yaml = f"""orcid_id: https://orcid.org/0000-0000-0000-0000
name: Python Tests
public_key: {os.path.join(TEST_RESOURCES_FILEPATH, "id_rsa.pub")}
private_key: {os.path.join(TEST_RESOURCES_FILEPATH, "id_rsa")}
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

java_wrap = JavaWrapper(private_key=profile_test.private_key)
