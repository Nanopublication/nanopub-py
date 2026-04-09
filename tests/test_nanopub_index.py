from nanopub import create_nanopub_index
from tests.conftest import default_conf


class TestCreation:

    def test_nanopub_index(self):
        np_list = create_nanopub_index(
            conf=default_conf,
            np_list=[
                "https://purl.org/np/RA5cwuR2b7Or9Pkb50nhPcHa2-cD0-gEPb2B3Ly5IxyuA",
                "https://purl.org/np/RAj1G7tgntNvXEgaMDmrc3rhxLekjZX6qsPIaEjUJ49NU",
            ],
            title="My nanopub index",
            description="This is my nanopub index",
            creation_time="2020-09-21T00:00:00",
            creators=["https://orcid.org/0000-0000-0000-0000"],
            see_also="https://github.com/Nanopublication/nanopub-py",
        )
        for np in np_list:
            assert np.source_uri is not None
