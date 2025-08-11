import os
from pathlib import Path

import pytest

from nanopub.definitions import TEST_RESOURCES_FILEPATH
from nanopub.profile import Profile, ProfileError, load_profile
from tests.conftest import profile_test_path

TEST_PRIVATE_KEY = "MIICeAIBADANBgkqhkiG9w0BAQEFAASCAmIwggJeAgEAAoGBAPdEfIdHtZYoFh6/DWorzoHpFXMjugqW+CGpe9uk4BfUq54MToi2u7fgdGGtXLg4wsJFBYETdVeS0p1uA7EPe8LhwjHPktf5c6AZbO/lYpKM59e7/Ih4mvOy4iTIe/Dv+1OgasTSK0nXAbKUm/5iJ6LOYa82JQeE/QnT5gUw2e97AgMBAAECgYBbNQnyJINYpeSy5qoeFZaQ2Ncup2kCavmQASJMvJ5ka+/51nRJfY30n3iOZxIiad19J1SGbhUEfoXtyBzYfOubF2i2GJtdF5VyjdSoU6w/gOo2/vnbH+GCHnMclrWshohOADGQU/Y8pYhIvlQqcb6xEOts9m9C9g4uwvPXqjmhoQJBAPkmSFIZwF3i2UvJlHyeXi599L0jkGTUJy/Y4IjieUx5suwvAtG47ejhgIPKK06VtW49oGPHWjWc3cJAmnV+vTMCQQD+EPTvNtLpX9QiDEJD7b8woDwmVrvH/RUosP/cXpMQd7BUVgPlpffAlFJGDlOzwwjZjy+8kc6MYevh1kWqobSZAkEAyCs+nV99ErEHnYEFoB1oU3f0oeSpxKhCF4np03AIvi1kV6bpX+9wjNJnevp5UriqvDgc3S0zx7EQ5Vkb/1vkywJBAMMw59y4tAVT+DhITsi9aTvEfzG9RPt6trzSb2Aw0K/AJJpGkyvl/JfZ2/Oyoh/jYXM0DKrFIni76mtRIajcH1ECQQCJi6aXOaRkRPmf7FYY9cRaJdR1BtZkKZbDg6ZMD1bY97cGiM9STTMeldYcCtQBtyhVCTEObI/V6/0FAvY9Zi7w"
TEST_PUBLIC_KEY = "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQD3RHyHR7WWKBYevw1qK86B6RVzI7oKlvghqXvbpOAX1KueDE6Itru34HRhrVy4OMLCRQWBE3VXktKdbgOxD3vC4cIxz5LX+XOgGWzv5WKSjOfXu/yIeJrzsuIkyHvw7/tToGrE0itJ1wGylJv+YieizmGvNiUHhP0J0+YFMNnvewIDAQAB"


def test_instantiate_profile_path():
    p = Profile(
        name="Python Tests",
        orcid_id="https://orcid.org/0000-0000-0000-0000",
        private_key=Path(os.path.join(TEST_RESOURCES_FILEPATH, "id_rsa")),
        public_key=Path(os.path.join(TEST_RESOURCES_FILEPATH, "id_rsa.pub")),
    )

    assert p.orcid_id == "https://orcid.org/0000-0000-0000-0000"
    assert p.name == "Python Tests"
    assert p.introduction_nanopub_uri is None
    assert p.private_key == TEST_PRIVATE_KEY
    assert p.public_key == TEST_PUBLIC_KEY
    assert p.private_key == TEST_PRIVATE_KEY
    assert p.public_key == TEST_PUBLIC_KEY


def test_instantiate_profile_str():
    p = Profile(
        name="Python Tests",
        orcid_id="https://orcid.org/0000-0000-0000-0000",
        private_key=TEST_PRIVATE_KEY,
        public_key=TEST_PUBLIC_KEY,
    )

    assert p.orcid_id == "https://orcid.org/0000-0000-0000-0000"
    assert p.name == "Python Tests"
    assert p.introduction_nanopub_uri is None
    assert p.private_key == TEST_PRIVATE_KEY
    assert p.public_key == TEST_PUBLIC_KEY


def test_load_profile():
    p = load_profile(profile_test_path)

    assert p.orcid_id == "https://orcid.org/0000-0000-0000-0000"
    assert p.name == "Python Tests"
    assert p.introduction_nanopub_uri is None
    assert p.private_key == TEST_PRIVATE_KEY
    assert p.public_key == TEST_PUBLIC_KEY


def test_fail_loading_incomplete_profile(tmpdir):
    test_file = Path(tmpdir / "profile.yml")
    profile_yaml = """orcid_id: https://orcid.org/0000-0000-0000-0000
name: Python Tests"""
    with open(test_file, "w") as f:
        f.write(profile_yaml)

    with pytest.raises(ProfileError):
        load_profile(test_file)


def test_profile_file_not_found(tmpdir):
    test_file = Path(tmpdir / "profile.yml")
    with pytest.raises(ProfileError):
        load_profile(test_file)


def test_store_profile(tmpdir):
    test_folder = Path(tmpdir)

    p = Profile(
        name="Python Tests",
        orcid_id="https://orcid.org/0000-0000-0000-0000",
        private_key=TEST_PRIVATE_KEY,
        public_key=TEST_PUBLIC_KEY,
    )
    p.store(test_folder)

    profile_path = test_folder / "profile.yml"
    pubkey_path = test_folder / "id_rsa.pub"
    privkey_path = test_folder / "id_rsa"
    with profile_path.open("r") as f:
        assert f.read() == (
            "orcid_id: https://orcid.org/0000-0000-0000-0000\n"
            "name: Python Tests\n"
            f"public_key: {pubkey_path}\n"
            f"private_key: {privkey_path}\n"
            "introduction_nanopub_uri:\n"
        )


def test_generate_keys(tmpdir):
    p = Profile(
        name="Python Tests",
        orcid_id="https://orcid.org/0000-0000-0000-0000",
    )
    assert p.private_key is not None
    assert p.public_key is not None


def test_generate_keys_store_profile(tmpdir):
    p = Profile(
        name="Python Tests",
        orcid_id="https://orcid.org/0000-0000-0000-0000",
    )
    assert p.private_key is not None
    assert p.public_key is not None

    test_folder = Path(tmpdir)
    p.store(test_folder)

    profile_path = test_folder / "profile.yml"
    pubkey_path = test_folder / "id_rsa.pub"
    privkey_path = test_folder / "id_rsa"
    with profile_path.open("r") as f:
        assert f.read() == (
            "orcid_id: https://orcid.org/0000-0000-0000-0000\n"
            "name: Python Tests\n"
            f"public_key: {pubkey_path}\n"
            f"private_key: {privkey_path}\n"
            "introduction_nanopub_uri:\n"
        )

    p2 = load_profile(profile_path)
    assert p2.private_key == p.private_key
