"""
This module holds objects and functions to load a nanopub user profile.
"""
import logging
import os
import warnings
from base64 import b64encode, decodebytes
from pathlib import Path
from typing import Optional, Union

import yatiml
from Crypto.PublicKey import RSA

from nanopub.definitions import DEFAULT_PROFILE_PATH, RSA_KEY_SIZE, USER_CONFIG_DIR
from nanopub.orcid_id import OrcidID, looks_like_orcid

logger = logging.getLogger(__name__)

PROFILE_INSTRUCTIONS_MESSAGE = '''
    Follow these instructions to correctly setup your nanopub profile:
    https://nanopublication.github.io/nanopub-py/getting-started/setup/#setup-your-profile
'''


class ProfileError(RuntimeError):
    """
    Error to be raised if profile is not setup correctly.
    """


def _validate_agent_id(agent_id: str) -> str:
    """Validate and normalize the agent id (signer) to a URI.

    The agent id identifies the signer and may be any URI — a person's ORCID, a
    different identity provider, or a bot/agent URI. It is taken at face value
    and never dereferenced. This URI is published verbatim in a nanopub and
    matched exactly in SPARQL queries, so it must be consistent.

    As a convenience a bare ORCID identifier (``0000-0000-0000-0000``) is
    expanded to its canonical ``https://orcid.org/`` URI, and any value that
    claims to be an ORCID (starts with that prefix) must be a well-formed one.
    """
    if not agent_id or not agent_id.strip():
        raise ProfileError(
            "An agent id (e.g. your ORCID iD) is required to create a nanopub profile.\n"
            f"{PROFILE_INSTRUCTIONS_MESSAGE}"
        )
    agent_id = agent_id.strip()
    try:
        return str(OrcidID(agent_id))
    except ValueError as e:
        if looks_like_orcid(agent_id):
            raise ProfileError(f'{e}\n{PROFILE_INSTRUCTIONS_MESSAGE}') from e
        return agent_id


class Profile:

    def __init__(
            self,
            agent_id: Optional[str] = None,
            name: Optional[str] = None,
            private_key: Optional[Union[Path, str]] = None,
            public_key: Optional[Union[Path, str]] = None,
            introduction_nanopub_uri: Optional[str] = None,
            *,
            orcid_id: Optional[str] = None,
    ) -> None:
        """Represents a user profile.

            Attributes:
                agent_id (str): URI identifying the signer — an ORCID iD or any other agent URI
                name (str): The user's name
                private_key (Optional[Union[Path, str]]): Path to the user's private key, or the key as string
                public_key (Optional[Union[Path, str]]): Path to the user's public key, or the key as string
                introduction_nanopub_uri (Optional[str]): URI of the user's profile nanopub
                orcid_id (str): Deprecated alias for ``agent_id``.
            """
        if orcid_id is not None:
            warnings.warn(
                "The 'orcid_id' argument is deprecated; use 'agent_id' instead.",
                DeprecationWarning, stacklevel=2,
            )
            if agent_id is None:
                agent_id = orcid_id
        self.agent_id = agent_id
        self._name = name
        self._introduction_nanopub_uri = introduction_nanopub_uri

        if not private_key:
            self.generate_keys()
        elif isinstance(private_key, Path):
            try:
                with open(private_key) as f:
                    raw_private_key = f.read()
            except FileNotFoundError:
                raise ProfileError(
                    f'Private key file {private_key} for nanopub not found.\n'
                    f'Maybe your nanopub profile was not set up yet or not set up '
                    f'correctly. \n{PROFILE_INSTRUCTIONS_MESSAGE}'
                )
            self._private_key = normalize_private_key(raw_private_key)
        else:
            self._private_key = normalize_private_key(private_key)

        if not public_key and private_key:
            logger.info(
                'The public key was not provided when loading the Nanopub profile, generating it from the provided private key')
            self._public_key = normalize_public_key(self._private_key)
        elif isinstance(public_key, Path):
            try:
                with open(public_key) as f:
                    raw_public_key = f.read()
            except FileNotFoundError:
                raise ProfileError(
                    f'Public key file {public_key} for nanopub not found.\n'
                    f'Maybe your nanopub profile was not set up yet or not set up '
                    f'correctly. \n{PROFILE_INSTRUCTIONS_MESSAGE}'
                )
            self._public_key = normalize_public_key(raw_public_key)
        elif public_key:
            self._public_key = normalize_public_key(public_key)

    def generate_keys(self) -> str:
        """Generate private/public RSA key pair at the path specified in the profile.yml, to be used to sign nanopubs"""
        key = RSA.generate(RSA_KEY_SIZE)
        public_key_str = key.publickey().export_key().decode('utf-8')

        self._private_key = _encode_private_key(key)
        self._public_key = _encode_public_key(key)
        logger.info(f"Public/private RSA key pair has been generated for {self.agent_id} ({self.name})")
        return public_key_str

    def store(self, folder: Path = USER_CONFIG_DIR) -> str:
        """Stores the nanopub user profile. By default the profile is stored in `HOME_DIR/.nanopub/profile.yaml`.

        Args:
            folder: The path to the folder to store the user's profile files.

        Returns:
            The path where the profile was stored.
        """
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        private_key_path = os.path.join(folder, "id_rsa")
        public_key_path = os.path.join(folder, "id_rsa.pub")
        profile_path = os.path.join(folder, "profile.yml")

        # Store keys
        if not os.path.exists(private_key_path):
            _write_private_key(private_key_path, self.private_key + '\n')
        if not os.path.exists(public_key_path):
            with open(public_key_path, "w") as f:
                f.write(self.public_key)

        intro_uri = ''
        if self.introduction_nanopub_uri:
            intro_uri = f" {self.introduction_nanopub_uri}"
        # Store profile.yml
        profile_yaml = f"""agent_id: {self.agent_id}
name: {self.name}
public_key: {public_key_path}
private_key: {private_key_path}
introduction_nanopub_uri:{intro_uri}
"""
        with open(profile_path, "w") as f:
            f.write(profile_yaml)

        return profile_path

    @property
    def agent_id(self):
        return self._agent_id

    @agent_id.setter
    def agent_id(self, value):
        self._agent_id = _validate_agent_id(value)

    @property
    def orcid_id(self):
        warnings.warn(
            "Profile.orcid_id is deprecated; use Profile.agent_id instead.",
            DeprecationWarning, stacklevel=2,
        )
        return self._agent_id

    @orcid_id.setter
    def orcid_id(self, value):
        warnings.warn(
            "Profile.orcid_id is deprecated; use Profile.agent_id instead.",
            DeprecationWarning, stacklevel=2,
        )
        self.agent_id = value

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def private_key(self):
        return self._private_key

    @private_key.setter
    def private_key(self, value):
        self._private_key = value

    @property
    def public_key(self):
        return self._public_key

    @public_key.setter
    def public_key(self, value):
        self._public_key = value

    @property
    def introduction_nanopub_uri(self):
        return self._introduction_nanopub_uri

    @introduction_nanopub_uri.setter
    def introduction_nanopub_uri(self, value):
        self._introduction_nanopub_uri = value

    def __repr__(self):
        return f"""\033[1mAgent ID\033[0m: {self._agent_id}
\033[1mName\033[0m: {self._name}
\033[1mPrivate key\033[0m: {self._private_key}
\033[1mPublic key\033[0m: {self._public_key}
\033[1mIntro Nanopub URI\033[0m: {self._introduction_nanopub_uri}"""


class ProfileLoader(Profile):
    """A class to load a user profile from a local YAML file, only used for YAtiML."""

    def __init__(
            self,
            name: str,
            private_key: Path,
            public_key: Optional[Path],
            agent_id: Optional[str] = None,
            orcid_id: Optional[str] = None,
            introduction_nanopub_uri: Optional[str] = None
    ) -> None:
        """Create a ProfileLoader.

        Both the ``agent_id`` key and the legacy ``orcid_id`` key are accepted
        from profile.yml; ``agent_id`` takes precedence when both are present.
        """
        super().__init__(
            agent_id=agent_id if agent_id is not None else orcid_id,
            name=name,
            private_key=private_key,
            public_key=public_key,
            introduction_nanopub_uri=introduction_nanopub_uri,
        )


_load_profile = yatiml.load_function(ProfileLoader)


def load_profile(profile_path: Union[Path, str] = DEFAULT_PROFILE_PATH) -> Profile:
    """Retrieve nanopub user profile.

    By default the profile is stored in `HOME_DIR/.nanopub/profile.yaml`.

    Returns:
        A Profile containing the data from the configuration file.

    Raises:
        yatiml.RecognitionError: If there is an
            error in the file.
    """
    try:
        return _load_profile(Path(profile_path))
    except (yatiml.RecognitionError, FileNotFoundError) as e:
        msg = (f'{e}\nYour nanopub profile has not been set up yet, or is not set up correctly.\n'
               f'{PROFILE_INSTRUCTIONS_MESSAGE}')
        raise ProfileError(msg)


def generate_keyfiles(path: Path = USER_CONFIG_DIR) -> str:
    """Generate private/public RSA key pair at the path specified in the profile.yml, to be used to sign nanopubs"""
    if not Path(path).exists():
        Path(path).mkdir()

    key = RSA.generate(RSA_KEY_SIZE)
    private_key_str = _encode_private_key(key)
    public_key_str = _encode_public_key(key)
    private_path = path / "id_rsa"
    public_path = path / "id_rsa.pub"

    # Store key pair
    _write_private_key(private_path, private_key_str)

    public_key_file = open(public_path, "w")
    public_key_file.write(public_key_str)
    public_key_file.close()
    logger.info(f"Public/private RSA key pair has been generated in {private_path} and {public_path}")
    return public_key_str


def _write_private_key(path: Union[Path, str], content: str) -> None:
    """Write a private key to `path`, readable and writable only by its owner.

    The file is created with mode 600 rather than chmod'ed after the fact, so
    the key is never briefly world-readable; the chmod that follows covers the
    case of a file that was already there with wider permissions. On Windows,
    where POSIX permissions do not apply, both are effectively no-ops.
    """
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(content)
    os.chmod(path, 0o600)


def _encode_private_key(key: RSA.RsaKey) -> str:
    """Encode an RSA key to nanopub's canonical private-key form.

    The canonical form is the base64 of the PKCS#8 DER with no PEM armor and no
    newlines, as required by nanopub-java and assumed by the signing code.
    """
    return b64encode(key.export_key(format='DER', pkcs=8)).decode('utf-8')


def _encode_public_key(key: RSA.RsaKey) -> str:
    """Encode an RSA key to nanopub's canonical public-key form.

    The canonical form is the base64 of the SubjectPublicKeyInfo DER with no PEM
    armor and no newlines.
    """
    return b64encode(key.publickey().export_key(format='DER')).decode('utf-8')


def format_key(key: str) -> str:
    """Format private and public keys to remove header/footer and all newlines, as this is required by nanopub-java.

    .. deprecated::
        ``format_key`` is deprecated and will be removed in an upcoming major
        version. It only strips PEM armor from a PKCS#8/SPKI key via string
        replacement and silently mishandles PKCS#1 and CRLF input. Use
        :func:`normalize_private_key` / :func:`normalize_public_key` instead,
        which accept any standard PEM/DER/bare key and return the same canonical
        single-line base64 form.
    """
    warnings.warn(
        "format_key() is deprecated and will be removed in an upcoming major "
        "version; use normalize_private_key() / normalize_public_key() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    if key.startswith("-----BEGIN PRIVATE KEY-----"):
        key = key.replace("-----BEGIN PRIVATE KEY-----", "").replace("-----END PRIVATE KEY-----", "")
    if key.startswith("-----BEGIN PUBLIC KEY-----"):
        key = key.replace("-----BEGIN PUBLIC KEY-----", "").replace("-----END PUBLIC KEY-----", "")
    return key.replace("\n", "").strip()


def _load_rsa_key(key_data: str) -> RSA.RsaKey:
    """Parse an RSA key from any standard serialization.

    Accepts PEM (PKCS#1 ``BEGIN RSA PRIVATE KEY`` or PKCS#8 ``BEGIN PRIVATE
    KEY``), DER, or the bare single-line base64 that nanopub itself stores (DER
    without the PEM armor), with any line endings. Raises a clear ProfileError
    instead of letting an opaque base64/parsing error surface from deep inside
    the crypto library.
    """
    key_data = key_data.strip()
    # RSA.import_key handles PEM (PKCS#1/#8), DER and OpenSSH, and tolerates
    # surrounding whitespace and CR/LF line endings.
    try:
        return RSA.import_key(key_data)
    except (ValueError, IndexError, TypeError):
        pass
    # Fall back to nanopub's own format: bare base64 of the DER, no armor.
    try:
        return RSA.import_key(decodebytes(key_data.encode()))
    except Exception as e:
        raise ProfileError(
            'Could not parse the RSA key. Provide a standard PEM or DER RSA key '
            "(e.g. the output of `openssl genrsa`), or nanopub's base64 key "
            f'string. If the key is passphrase-protected, decrypt it first.\n'
            f'Underlying error: {e}\n{PROFILE_INSTRUCTIONS_MESSAGE}'
        ) from None


def normalize_private_key(key_data: str) -> str:
    """Normalize any RSA private key to nanopub's canonical single-line base64.

    The canonical form is the base64 of the PKCS#8 DER with no PEM armor and no
    newlines, as required by nanopub-java and assumed by the signing code.
    """
    key = _load_rsa_key(key_data)
    if not key.has_private():
        raise ProfileError(
            'A public key was provided where a private key was expected.'
        )
    return _encode_private_key(key)


def normalize_public_key(key_data: str) -> str:
    """Normalize any RSA public key to nanopub's canonical single-line base64.

    The canonical form is the base64 of the SubjectPublicKeyInfo DER with no PEM
    armor and no newlines. A private key may be passed in, in which case the
    corresponding public key is derived.
    """
    key = _load_rsa_key(key_data)
    return _encode_public_key(key)
