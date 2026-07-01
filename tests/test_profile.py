from pathlib import Path

import pytest

from nanopub.profile import (
    Profile,
    ProfileError,
    format_key,
    load_profile,
    normalize_private_key,
    normalize_public_key,
)
from tests.conftest import profile_test_path, _signing_key

ORCID_ID = "https://orcid.org/0000-0000-0000-0000"


class TestProfileInstantiation:
    _private_key = _signing_key.private_key
    _public_key = _signing_key.public_key

    _private_key_str = _private_key.read_text()
    _public_key_str = _public_key.read_text()

    def test_instantiate_profile_with_empty_orcid_id(self):
        with pytest.raises(ProfileError):
            Profile(
                name='Python Tests',
                orcid_id='',
                private_key=self._private_key,
                public_key=self._public_key
            )

    def test_instantiate_profile_with_url_orcid_id(self):
        p = Profile(
            name='Python Tests',
            orcid_id=ORCID_ID,
            private_key=self._private_key,
            public_key=self._public_key
        )

        assert p.orcid_id == ORCID_ID

    def test_instantiate_profile_with_raw_orcid_id(self):
        p = Profile(
            name='Python Tests',
            orcid_id='0000-0000-0000-0000',
            private_key=self._private_key,
            public_key=self._public_key
        )

        assert p.orcid_id == ORCID_ID

    def test_instantiate_profile_path(self):
        assert isinstance(self._private_key, Path)
        assert isinstance(self._public_key, Path)

        p = Profile(
            name='Python Tests',
            orcid_id=ORCID_ID,
            private_key=self._private_key,
            public_key=self._public_key
        )

        assert p.orcid_id == ORCID_ID
        assert p.name == 'Python Tests'
        assert p.introduction_nanopub_uri is None
        assert p.private_key == self._private_key_str
        assert p.public_key == self._public_key_str

    def test_instantiate_profile_str(self):
        assert isinstance(self._private_key_str, str)
        assert isinstance(self._public_key_str, str)

        p = Profile(
            name='Python Tests',
            orcid_id=ORCID_ID,
            private_key=self._private_key_str,
            public_key=self._public_key_str
        )

        assert p.orcid_id == ORCID_ID
        assert p.name == 'Python Tests'
        assert p.introduction_nanopub_uri is None
        assert p.private_key == self._private_key_str
        assert p.public_key == self._public_key_str


class TestProfileLoader:
    _private_key = _signing_key.private_key
    _public_key = _signing_key.public_key

    _private_key_str = _private_key.read_text()
    _public_key_str = _public_key.read_text()

    def test_load_profile(self):
        p = load_profile(profile_test_path)

        assert p.orcid_id == ORCID_ID
        assert p.name == 'Python Tests'
        assert p.introduction_nanopub_uri is None
        assert p.private_key == self._private_key_str
        assert p.public_key == self._public_key_str

    def test_fail_loading_incomplete_profile(self, tmpdir):
        test_file = Path(tmpdir / 'profile.yml')
        profile_yaml = f"orcid_id: {ORCID_ID}\nname: Python Tests"
        with open(test_file, "w") as f:
            f.write(profile_yaml)

        with pytest.raises(ProfileError):
            load_profile(test_file)

    def test_profile_file_not_found(self, tmpdir):
        test_file = Path(tmpdir / 'profile.yml')
        with pytest.raises(ProfileError):
            load_profile(test_file)


def test_store_profile(tmpdir):
    test_folder = Path(tmpdir)

    p = Profile(
        name='Python Tests',
        orcid_id=ORCID_ID,
        private_key=_signing_key.private_key.read_text(),
        public_key=_signing_key.public_key.read_text()
    )
    p.store(test_folder)

    profile_path = test_folder / "profile.yml"
    pubkey_path = test_folder / "id_rsa.pub"
    privkey_path = test_folder / "id_rsa"
    with profile_path.open('r') as f:
        assert f.read() == (
            f"orcid_id: {ORCID_ID}\n"
            'name: Python Tests\n'
            f"public_key: {pubkey_path}\n"
            f"private_key: {privkey_path}\n"
            'introduction_nanopub_uri:\n')


def test_generate_keys(tmpdir):
    p = Profile(
        name='Python Tests',
        orcid_id=ORCID_ID,
    )
    assert p.private_key is not None
    assert p.public_key is not None


def test_generate_keys_store_profile(tmpdir):
    p = Profile(
        name='Python Tests',
        orcid_id=ORCID_ID,
    )
    assert p.private_key is not None
    assert p.public_key is not None

    test_folder = Path(tmpdir)
    p.store(test_folder)

    profile_path = test_folder / "profile.yml"
    pubkey_path = test_folder / "id_rsa.pub"
    privkey_path = test_folder / "id_rsa"
    with profile_path.open('r') as f:
        assert f.read() == (
            f"orcid_id: {ORCID_ID}\n"
            'name: Python Tests\n'
            f"public_key: {pubkey_path}\n"
            f"private_key: {privkey_path}\n"
            'introduction_nanopub_uri:\n')

    p2 = load_profile(profile_path)
    assert p2.private_key == p.private_key


def test_canonical_pubkey_literal_is_stable():
    """Normalizing an already-canonical key must be a byte-for-byte identity.

    The public key is published verbatim into the nanopub's pubinfo as
    ``Literal(profile.public_key)`` and matched exactly in SPARQL queries. Any
    variation in this literal silently breaks exact matching against every
    previously published nanopub, so normalization must not alter a key that is
    already in nanopub's canonical bare-base64 form.
    """
    # Identity for a public key already in canonical form.
    assert normalize_public_key(_signing_key.public_key.read_text()) == _signing_key.public_key.read_text()
    # Identity for a private key already in canonical form (signing determinism).
    assert normalize_private_key(_signing_key.private_key.read_text()) == _signing_key.private_key.read_text()
    # Public key derived from the private key yields the same canonical literal.
    assert normalize_public_key(_signing_key.private_key.read_text()) == _signing_key.public_key.read_text()


def test_format_key_is_deprecated():
    """format_key is retained as a deprecated shim; it must warn but still work."""
    pem = (
        "-----BEGIN PUBLIC KEY-----\n"
        f"{_signing_key.public_key.read_text()}\n"
        "-----END PUBLIC KEY-----\n"
    )
    with pytest.warns(DeprecationWarning, match="format_key"):
        result = format_key(pem)
    assert result == _signing_key.public_key.read_text()
