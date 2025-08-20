"""
This module holds objects and functions to load a nanopub user profile.
"""
import os
from base64 import decodebytes
from pathlib import Path
from typing import Optional, Union

import yatiml
from Crypto.PublicKey import RSA

from nanopub.definitions import DEFAULT_PROFILE_PATH, RSA_KEY_SIZE, USER_CONFIG_DIR
from nanopub.utils import log

PROFILE_INSTRUCTIONS_MESSAGE = '''
    Follow these instructions to correctly setup your nanopub profile:
    https://nanopublication.github.io/nanopub-py/getting-started/setup/#setup-your-profile
'''


class ProfileError(RuntimeError):
    """
    Error to be raised if profile is not setup correctly.
    """


class Profile:
    """Represents a user profile.

    Attributes:
        orcid_id (str): The user's ORCID
        name (str): The user's name
        private_key (Optional[Union[Path, str]]): Path to the user's private key, or the key as string
        public_key (Optional[Union[Path, str]]): Path to the user's public key, or the key as string
        introduction_nanopub_uri (Optional[str]): URI of the user's profile nanopub
    """

    def __init__(
            self,
            orcid_id: str,
            name: str,
            private_key: Optional[Union[Path, str]] = None,
            public_key: Optional[Union[Path, str]] = None,
            introduction_nanopub_uri: Optional[str] = None
    ) -> None:
        """Create a Profile."""
        self._orcid_id = orcid_id
        self._name = name
        self._introduction_nanopub_uri = introduction_nanopub_uri

        if not private_key:
            self.generate_keys()
        elif isinstance(private_key, Path):
            try:
                with open(private_key) as f:
                    self._private_key = f.read().strip()
            except FileNotFoundError:
                raise ProfileError(
                    f'Private key file {private_key} for nanopub not found.\n'
                    f'Maybe your nanopub profile was not set up yet or not set up '
                    f'correctly. \n{PROFILE_INSTRUCTIONS_MESSAGE}'
                )
        else:
            self._private_key = private_key

        if not public_key and private_key:
            log.info('The public key was not provided when loading the Nanopub profile, generating it from the provided private key')
            key = RSA.import_key(decodebytes(self._private_key.encode()))
            self._public_key = format_key(key.publickey().export_key().decode('utf-8'))
        elif isinstance(public_key, Path):
            try:
                with open(public_key) as f:
                    self._public_key = f.read().strip()
            except FileNotFoundError:
                raise ProfileError(
                    f'Private key file {public_key} for nanopub not found.\n'
                    f'Maybe your nanopub profile was not set up yet or not set up '
                    f'correctly. \n{PROFILE_INSTRUCTIONS_MESSAGE}'
                )
        elif public_key:
            self._public_key = public_key

    def generate_keys(self) -> str:
        """Generate private/public RSA key pair at the path specified in the profile.yml, to be used to sign nanopubs"""
        key = RSA.generate(RSA_KEY_SIZE)
        private_key_str = key.export_key('PEM', pkcs=8).decode('utf-8')
        public_key_str = key.publickey().export_key().decode('utf-8')

        self._private_key = format_key(private_key_str)
        self._public_key = format_key(public_key_str)
        log.info(f"Public/private RSA key pair has been generated for {self.orcid_id} ({self.name})")
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
            with open(private_key_path, "w") as f:
                f.write(self.private_key + '\n')
        if not os.path.exists(public_key_path):
            with open(public_key_path, "w") as f:
                f.write(self.public_key)

        intro_uri = ''
        if self.introduction_nanopub_uri:
            intro_uri = f" {self.introduction_nanopub_uri}"
        # Store profile.yml
        profile_yaml = f"""orcid_id: {self.orcid_id}
name: {self.name}
public_key: {public_key_path}
private_key: {private_key_path}
introduction_nanopub_uri:{intro_uri}
"""
        with open(profile_path, "w") as f:
            f.write(profile_yaml)

        return profile_path


    @property
    def orcid_id(self):
        return self._orcid_id

    @orcid_id.setter
    def orcid_id(self, value):
        self._orcid_id = value

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
        return f"""\033[1mORCID\033[0m: {self._orcid_id}
\033[1mName\033[0m: {self._name}
\033[1mPrivate key\033[0m: {self._private_key}
\033[1mPublic key\033[0m: {self._public_key}
\033[1mIntro Nanopub URI\033[0m: {self._introduction_nanopub_uri}"""


class ProfileLoader(Profile):
    """A class to load a user profile from a local YAML file, only used for YAtiML."""
    def __init__(
            self,
            orcid_id: str,
            name: str,
            private_key: Path,
            public_key: Optional[Path],
            introduction_nanopub_uri: Optional[str] = None
    ) -> None:
        """Create a ProfileLoader."""
        super().__init__(
            orcid_id=orcid_id,
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
    private_key_str = key.export_key('PEM', pkcs=8).decode('utf-8')
    public_key_str = key.publickey().export_key().decode('utf-8')

    private_key_str = format_key(private_key_str)
    public_key_str = format_key(public_key_str)
    private_path = path / "id_rsa"
    public_path = path / "id_rsa.pub"

    # Store key pair
    private_key_file = open(private_path, "w")
    private_key_file.write(private_key_str)
    private_key_file.close()

    public_key_file = open(public_path, "w")
    public_key_file.write(public_key_str)
    public_key_file.close()
    log.info(f"Public/private RSA key pair has been generated in {private_path} and {public_path}")
    return public_key_str


def format_key(key: str) -> str:
    """Format private and public keys to remove header/footer and all newlines, as this is required by nanopub-java"""
    if key.startswith("-----BEGIN PRIVATE KEY-----"):
        key = key.replace("-----BEGIN PRIVATE KEY-----", "").replace("-----END PRIVATE KEY-----", "")
    if key.startswith("-----BEGIN PUBLIC KEY-----"):
        key = key.replace("-----BEGIN PUBLIC KEY-----", "").replace("-----END PUBLIC KEY-----", "")
    return key.replace("\n", "").strip()
