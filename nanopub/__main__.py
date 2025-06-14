#! /usr/bin/env python3
import os
import re
import shutil
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Optional, Tuple

import rdflib
import typer
from typer import Argument, Option

from nanopub import Nanopub, NanopubClaim, NanopubConf, load_profile
from nanopub._version import __version__
from nanopub.definitions import DEFAULT_PROFILE_PATH, USER_CONFIG_DIR
from nanopub.profile import Profile, ProfileError, generate_keyfiles
from nanopub.templates.nanopub_introduction import NanopubIntroduction
from nanopub.utils import MalformedNanopubError

cli = typer.Typer(help="Nanopub Command Line Interface", no_args_is_help=True)

PRIVATE_KEY_FILE = 'id_rsa'
PUBLIC_KEY_FILE = 'id_rsa.pub'
DEFAULT_KEYS_PATH_PREFIX = USER_CONFIG_DIR / 'id'
DEFAULT_PRIVATE_KEY_PATH = USER_CONFIG_DIR / PRIVATE_KEY_FILE
DEFAULT_PUBLIC_KEY_PATH = USER_CONFIG_DIR / PUBLIC_KEY_FILE
RSA = 'RSA'
ORCID_ID_REGEX = r'^https://orcid.org/(\d{4}-){3}\d{3}(\d|X)$'


def validate_orcid_id(ctx, param, orcid_id: str):
    """Check if valid ORCID iD, should be https://orcid.org/ + 16 digit in form:
    https://orcid.org/0000-0000-0000-0000. ctx and param are necessary `click` callback args
    """
    if re.match(ORCID_ID_REGEX, orcid_id):
        return orcid_id
    else:
        raise ValueError('Your ORCID iD is not valid, please provide a valid ORCID iD that '
                         'looks like: https://orcid.org/0000-0000-0000-0000')


@cli.command(help='Get nanopub library version')
def version():
    print(__version__)


@cli.command(help='Get the current user profile info')
def profile():
    try:
        p = load_profile()
        print(f' 👤 User profile in \033[1m{DEFAULT_PROFILE_PATH}\033[0m')
        print(str(p))
    except ProfileError as e:
        print(e)
        print(f" ⚠️  No profile could be loaded from {DEFAULT_PROFILE_PATH}")
        print(" ℹ️  Use \033[1mnp setup\033[0m to setup your nanopub profile locally with the interactive CLI")



@cli.command(help='Sign a Nanopublication')
def sign(
    filepath: Path,
    private_key: Optional[Path] = typer.Option(
        None, "--private-key", "-k",
        help="Path to the RSA private key with which the nanopub will be signed."
    ),
):
    if private_key:
        config = NanopubConf(
            profile=Profile(
                # TODO: better handle Profile without name or orcid_id
                name='', orcid_id='',
                private_key=private_key
            ),
        )
    else:
        config = NanopubConf(profile=load_profile())

    folder_path = filepath.parent
    filename = f'{filepath.stem}.trig'
    np = Nanopub(
        conf=config,
        rdf=filepath
    )
    np.sign()
    signed_filepath = f"{str(folder_path)}/signed.{str(filename)}"
    np.rdf.serialize(signed_filepath, format='trig')
    print(f" ✒️  Nanopub signed in \033[1m{signed_filepath}\033[0m with the trusty URI \033[1m{np.source_uri}\033[0m")
    print(f" 📬️ To publish it run \033[1mnp publish {signed_filepath}\033[0m")


@cli.command(help='Publish a Nanopublication')
def publish(
    filepath: Path,
    test: bool = typer.Option(False, help="Publish to the test server"),
):
    if test:
        print(" 🧪 Publishing to the test server")
    config = NanopubConf(
        profile=load_profile(),
        use_test_server=test,
    )
    np = Nanopub(conf=config, rdf=filepath)
    np.publish()
    print(f" 📬️ Nanopub published at \033[1m{np.source_uri}\033[0m")



@cli.command(help='Check if a signed Nanopublication is valid')
def check(filepath: Path):
    config = NanopubConf(profile=load_profile())
    np = Nanopub(conf=config, rdf=filepath)
    try:
        np.is_valid
        print(f"\033[1m✅ Valid nanopub\033[0m {np.source_uri}")
    except MalformedNanopubError as e:
        print(f"\033[1m❌ Invalid nanopub\033[0m: {e}")


@cli.command(help='Interactive CLI to create a nanopub user profile. '
                  'A local version of the profile will be stored in the user config dir '
                  '(by default $HOME/.nanopub/). '
                  'The profile will also be published to the nanopub servers.')
def setup(
    orcid_id: str = typer.Option(
        None,
        help="Your ORCID iD (i.e. https://orcid.org/0000-0000-0000-0000)",
        prompt='What is your ORCID iD (i.e. https://orcid.org/0000-0000-0000-0000)?',
        callback=validate_orcid_id
    ),
    name: str = typer.Option(
        None,
        help='Your full name',
        prompt='What is your full name?',
    ),
    newkeys: bool = typer.Option(
        False,
        help="Generate new RSA public and private keys with which your nanopubs will be signed",
    ),
    keypair: Optional[Tuple[Path, Path]] = typer.Option(
        (None, None),
        help="Your RSA public and private keys with which your nanopubs will be signed",
    ),
    publish: Optional[bool] = typer.Option(
        None, "--publish/--no-publish",
        help="If true, nanopub will be published to nanopub servers",
    ),
):
    """
    Interactive CLI to create a user profile.

    Args:
        orcid_id: the users ORCID iD or other form of universal identifier. Example:
            `https://orcid.org/0000-0000-0000-0000`
        publish: if True, profile will be published to nanopub servers
        name: the name of the user
        keypair: a tuple containing the paths to the public and private RSA key to be used to sign
            nanopubs. If empty, new keys will be generated or the ones in the .nanopub folder
            will be used.
    """
    print('⚙️ Setting up nanopub profile...')
    if keypair == (None, None):
        keypair = None
    if not USER_CONFIG_DIR.exists():
        USER_CONFIG_DIR.mkdir()

    if publish is None:
        prompt = ('📬️ Would you like to publish your profile to the nanopub servers? '
                  'This links your ORCID iD to your RSA key, thereby making all your '
                  'publications linkable to you')
        publish_resp = typer.prompt(prompt, type=str, default="")
        if publish_resp and publish_resp.lower().startswith("y"):
            publish = True
        else:
            publish = False

    if not keypair and not newkeys:
        prompt = '🔓️ Provide the path to your public RSA key: ' \
            'Leave empty for using the one in: '
        public_key = typer.prompt(prompt, type=Path,
                                  default=DEFAULT_PUBLIC_KEY_PATH)
        if not public_key:
            keypair = None
        else:
            prompt = '🔑 Provide the path to your private RSA key: '
            private_key = typer.prompt(prompt, type=Path,
                                       default=DEFAULT_PRIVATE_KEY_PATH)
            keypair = public_key, private_key

    if not keypair:
        if _rsa_keys_exist():
            print(f'🛑 RSA keys already exist and are stored in {USER_CONFIG_DIR}. '
                  f'If you want to create new ones then you must manually '
                  f'delete these keys.')
            raise typer.Exit(code=1)
        else:
            # JavaWrapper().make_keys(path_name=DEFAULT_KEYS_PATH_PREFIX)
            generate_keyfiles(USER_CONFIG_DIR)
            print(f'🔑 Created RSA keys. Your RSA keys are stored in {USER_CONFIG_DIR}')
    else:
        public_key_path, private_key = keypair

        # Copy the keypair to the default location
        if not os.path.exists(DEFAULT_PUBLIC_KEY_PATH):
            shutil.copy(public_key_path, USER_CONFIG_DIR / PUBLIC_KEY_FILE)
        if not os.path.exists(DEFAULT_PRIVATE_KEY_PATH):
            shutil.copy(private_key, USER_CONFIG_DIR / PRIVATE_KEY_FILE)

        print(f'🚚 Your RSA keys have been copied to {USER_CONFIG_DIR}')

    # Public key can always be found at DEFAULT_PUBLIC_KEY_PATH.
    # Either new keys have been generated there or
    # existing keys have been copy to that location.
    public_key = DEFAULT_PUBLIC_KEY_PATH.read_text()

    profile = Profile(orcid_id, name, DEFAULT_PRIVATE_KEY_PATH, DEFAULT_PUBLIC_KEY_PATH)
    profile.store(USER_CONFIG_DIR)

    # Declare the user to nanopub
    np_conf = NanopubConf(profile=profile)

    np = NanopubIntroduction(conf=np_conf)
    np.sign()
    if publish:
        np.publish()

        profile.introduction_nanopub_uri = np.concept_uri
        print(f"Introduction Nanopub published: {np.source_uri}")
    else:
        print("Introduction Nanopub signed but not published:")
        print(np)

    # Store profile nanopub uri
    profile_path = profile.store(USER_CONFIG_DIR)

    print(f"👤 Profile stored in \033[1m{profile_path}\033[0m")


def _rsa_keys_exist():
    return DEFAULT_PRIVATE_KEY_PATH.exists() or DEFAULT_PUBLIC_KEY_PATH.exists()


create = typer.Typer(
    help=(
        'Create a Nanopublication from a template '
        'and print it to standard output.'
    ),
    no_args_is_help=True,
)


class DataFormat(StrEnum):
    """Linked Data format."""

    TRIG = 'trig'
    RDF_XML = 'xml'
    NQUADS = 'nquads'
    JSON_LD = 'json-ld'


@dataclass
class CreateParameters:
    output_format: DataFormat

    def show(self, nanopublication: Nanopub):
        print(nanopublication.rdf.serialize(format=self.output_format.value))


class CreateNanopubContext(typer.Context):
    obj: CreateParameters


@create.callback()
def _create_callback(ctx: typer.Context, output_format: DataFormat = DataFormat.TRIG):
    ctx.obj = CreateParameters(output_format=output_format)


cli.add_typer(create, name='create')


@create.command(help='Create a nanopub from an assertion graph')
def from_assertion(
    ctx: CreateNanopubContext,
    filepath: Annotated[Path, Argument(exists=True, dir_okay=False)],
    was_derived_from: Annotated[
        str | None,
        Option(
            help=(
                'URI of a statement which this nanopublication is derived from.'
            )
        )
    ] = None,
):
    """Create a nanopublication based on assertion."""
    config = NanopubConf(
        profile=load_profile(),
        derived_from=was_derived_from,
        add_pubinfo_generated_time=True,
        attribute_publication_to_profile=True,
    )

    np = Nanopub(
        assertion=rdflib.Graph().parse(filepath),
        conf=config,
    )

    ctx.obj.show(np)


@create.command()
def claim(
    ctx: CreateNanopubContext,
    text: Annotated[list[str], typer.Argument()],
):
    """
    Create a nanopublication based on a free-form textual claim.

    If multiple arguments are provided, they will be joined with a whitespace
    to form one text.
    """
    claim_text = ' '.join(text)

    config = NanopubConf(
        profile=load_profile(),
        add_pubinfo_generated_time=True,
        attribute_publication_to_profile=True,
    )

    np = NanopubClaim(
        conf=config,
        claim=claim_text,
    )

    ctx.obj.show(np)


if __name__ == '__main__':
    cli()
