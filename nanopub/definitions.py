from pathlib import Path

from rdflib import Namespace

ROOT_FILEPATH = Path(__file__).parent.parent
TESTS_FILEPATH = ROOT_FILEPATH / "tests"
TEST_RESOURCES_FILEPATH = TESTS_FILEPATH / "resources"
USER_CONFIG_DIR = Path.home() / ".nanopub"
DEFAULT_PROFILE_PATH = USER_CONFIG_DIR / "profile.yml"

TEST_NANOPUB_REGISTRY_URL = 'https://test.registry.knowledgepixels.com/np/'
# List of servers: https://monitor.petapico.org/.csv
NANOPUB_REGISTRY_URLS = [
    'https://registry.petapico.org/np/',
    'https://registry.knowledgepixels.com/np/',
    'https://registry.np.trustyuri.net/np/',
]
NANOPUB_FETCH_FORMAT = "trig"

DUMMY_NANOPUB_URI = "http://purl.org/nanopub/temp/np"
DUMMY_NAMESPACE = Namespace(DUMMY_NANOPUB_URI + "/")
DUMMY_URI = DUMMY_NAMESPACE[""]

NP_TEMP_PREFIX = "http://purl.org/nanopub/temp/"
NP_PREFIX = "https://w3id.org/np/"

MAX_NP_PER_INDEX = 1100
MAX_TRIPLES_PER_NANOPUB = 1200

RSA_KEY_SIZE = 2048

NANOPUB_QUERY_URLS = [
    'https://query.knowledgepixels.com/api/',
    'https://query.petapico.org/api/',
    # 'https://query.np.trustyuri.net/api/',
]
TEST_NANOPUB_QUERY_URL = 'https://query.knowledgepixels.com/api/' # we don't yet have a test server for this
