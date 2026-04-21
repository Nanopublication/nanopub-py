## [2.2.0](https://github.com/Nanopublication/nanopub-py/compare/v2.1.0...v2.2.0) (2026-04-21)

### Features

* adding retracting CLI option ([f9caecd](https://github.com/Nanopublication/nanopub-py/commit/f9caecd553a4833484630eccffbb3e9ce5917616))
* **fdo:** import handle-record URL/handle values as IRIs ([ef7140e](https://github.com/Nanopublication/nanopub-py/commit/ef7140e75653eae899299111ca6a57d359b408f5))
* **nanopub:** add signature verification to `is_valid` method for signed nanopubs ([a90c54d](https://github.com/Nanopublication/nanopub-py/commit/a90c54d7ae577dbc205b0cfb88245908a201f588))
* **nanopub:** add trusty check to assert that a trusty nanopub is a valid one ([7bb477f](https://github.com/Nanopublication/nanopub-py/commit/7bb477f7f64da8f1e38b2a306cce8dd9095974f0))

### Dependency updates

* **core-deps:** update rdflib to >=6.3.2 and pyshacl to >=0.28.1 ([37ef706](https://github.com/Nanopublication/nanopub-py/commit/37ef706f3423068f80b342a0c3aad81030cf3244))
* **deps:** add setuptools to dependencies used by pyshacl ([a114626](https://github.com/Nanopublication/nanopub-py/commit/a114626172ce5f287865d482590d3ac57200492d))
* **deps:** update dependencies for `docs` group ([edc55a9](https://github.com/Nanopublication/nanopub-py/commit/edc55a9052eda861fcf23dc4b97be1965b59d42d))

### Bug Fixes

* adding genrated pubinfo time by default ([4c4ac9d](https://github.com/Nanopublication/nanopub-py/commit/4c4ac9db64697c3b5de2c0675b6c6e59869488fe))
* **nanopub:** add local time zone to creation time ([5950bba](https://github.com/Nanopublication/nanopub-py/commit/5950bbac5d9e1306d54bd2ec276a95b42c100681))
* **nanopub:** add validation for named graphs to ensure distinct URIs and correct namespace ([d225ce2](https://github.com/Nanopublication/nanopub-py/commit/d225ce2f169408db84f0f4ed6708623e10e79737))
* **Nanopub:** avoid mutable default arguments in constructor ([76a9932](https://github.com/Nanopublication/nanopub-py/commit/76a99322f58494bfbdb044eb2f08045e16b81852))
* **Nanopub:** ensure valid source URI handling for trusty nanopubs and set it correctly after fetching ([3ce983b](https://github.com/Nanopublication/nanopub-py/commit/3ce983bd4fe4584381a652601d8ca3e1e2ff19bf))
* **Nanopub:** improve bnode handling and ensure deep copy of RDF graphs on initialization with Dataset ([60e8bf4](https://github.com/Nanopublication/nanopub-py/commit/60e8bf412cef86bc55a8464f66850af3d45fff69))
* **nanopub:** read `source_uri` from head graph when a trusty nanopub is loaded ([9d9dda3](https://github.com/Nanopublication/nanopub-py/commit/9d9dda392fcb1ecf5d50c07ce718ee76193b8f2b))
* **nanopub:** the NanopubConf is only considered during init when the nanopub was not provided as trig/nquads ([6e302dc](https://github.com/Nanopublication/nanopub-py/commit/6e302dcdd24bbec98054628ce980d448ba865f93))
* **nanopub:** use UTC timezone for creation time in constructor ([219226b](https://github.com/Nanopublication/nanopub-py/commit/219226b12544d8eee38dec40f4eb7df53512eb75))
* **RdfUtils, utils:** improve separator handling for nanopub URIs ([bcfb024](https://github.com/Nanopublication/nanopub-py/commit/bcfb0244baa43b9a9628202b5e2d20dcaee191a0))
* **RdfUtils:** update `get_trustyuri` to handle correctly trustyuri passed as baseuri parameter ([c13f42b](https://github.com/Nanopublication/nanopub-py/commit/c13f42b32a8f7eb5cd237ce0b64573d398f6568f))
* **RdfUtils:** when URIs are trusty but externals were not rewritten and when trusty base is passed trusty code wasn't extract ([5e13b35](https://github.com/Nanopublication/nanopub-py/commit/5e13b35919158fc4756099f939d6f6a256c998c7))
* **sign_utils:** update  to ensure that a signed nanopub has the  triple in the publication info graph ([22abc56](https://github.com/Nanopublication/nanopub-py/commit/22abc56fadd68ded874951308925af90b9eb2662))
* **sign_utils:** update signature verification to use local nanopub metadata and ensure the signature targets the correct nanopub ([907ca3a](https://github.com/Nanopublication/nanopub-py/commit/907ca3a0a420d853c65cf6805ed5833293814c0d))
* **TestVerifyTrusty:** update tests to use has_valid_trusty and ensure named graph context is preserved in quads ([bfe21a6](https://github.com/Nanopublication/nanopub-py/commit/bfe21a6ac4a9e0c155355d070a52a19942daa93b))
* **utils:** extract_np_metadata takes into account if nanopub is using both # and / ([8135018](https://github.com/Nanopublication/nanopub-py/commit/8135018dc80d30a3909b35408b7bfed2dee5cb03))

### Documentation

* **nanopubs:** update link to nanopub.net ([9bee7ee](https://github.com/Nanopublication/nanopub-py/commit/9bee7ee2b96fcb17741af90b63d37c66eea662cc))
* update development and README to use `uv` ([0cd4679](https://github.com/Nanopublication/nanopub-py/commit/0cd4679a4ac5577e38b58818f9f4e793f0ab99fc))

### Tests

* **deps:** add nanopub-testsuite-connector dependency to v1.0.0 ([0bd98d8](https://github.com/Nanopublication/nanopub-py/commit/0bd98d888535db338a7fd4b7434867e27e7f39ba))
* **deps:** move setuptools to test dependencies group ([dcaaaee](https://github.com/Nanopublication/nanopub-py/commit/dcaaaeea6f284eb6a790d47a61c6c9fce608dc1a))
* **deps:** update nanopub-testsuite-connector test dependency ([a2a458d](https://github.com/Nanopublication/nanopub-py/commit/a2a458d9f0a2ad4019c0740024089cedd8b7fc79))
* **deps:** update nanopub-testsuite-connector test library dependency to v1.0.3 ([b98f0d6](https://github.com/Nanopublication/nanopub-py/commit/b98f0d6f45eae8c7aae992e4d812a274f561b1ef))
* **deps:** update nanopub-testsuite-connector test library to v1.0.4 ([9a2f3a1](https://github.com/Nanopublication/nanopub-py/commit/9a2f3a19e3850d5eedadcc5483a9c34ff3c5e926))
* **nanopub:** add extensive unit tests for nanopub creation ([77677f7](https://github.com/Nanopublication/nanopub-py/commit/77677f78f76985c3367b0b0b35d30282a016c190))
* **nanopub:** add validity checks for trusty nanopub instances ([891cc2f](https://github.com/Nanopublication/nanopub-py/commit/891cc2f8c1a2e475794243d6050242fcc9e94cbd))
* **nanopub:** enable test_metadata_matches_graph and use NanopubTestSuite ([0d34bdf](https://github.com/Nanopublication/nanopub-py/commit/0d34bdfe7c76ac778eabe71f20f296c225e39154))
* **nanopub:** refactor and enhance signing tests ([44c1722](https://github.com/Nanopublication/nanopub-py/commit/44c1722ca4d0cdecfad225978e859556c7984a9a))
* **nanopub:** refactor tests to add granularity ([c2d4225](https://github.com/Nanopublication/nanopub-py/commit/c2d422547c97109447924eaaf56b9990cc949544))
* **nanopub:** remove java_wrap checks ([5ab2047](https://github.com/Nanopublication/nanopub-py/commit/5ab20477855526ead5d07d89c8ae9f481f031958))
* **nanopub:** update test_invalid_fetching with Exception raise check ([8b0d97a](https://github.com/Nanopublication/nanopub-py/commit/8b0d97a32c4432f698d5a8208551e08611f3264e))
* **RdfUtils:** add test for trustyuri with hash char as separator ([2ab4e44](https://github.com/Nanopublication/nanopub-py/commit/2ab4e449bba50b7825392023847b9b417bc6bd8b))
* **RdfUtils:** add TestGetTrustyUri unit tests ([a028c23](https://github.com/Nanopublication/nanopub-py/commit/a028c23fae94dbd56f6015228179006aff70772f))
* **RdfUtils:** add tests for get_trustyuri to verify trustyuri as baseuri handling ([377c332](https://github.com/Nanopublication/nanopub-py/commit/377c33212c6f9b5fd0b98802be0aa87eb9d2f4e4))
* **RdfUtils:** add tests for temporary base URI handling in `get_trustyuri` ([066dca0](https://github.com/Nanopublication/nanopub-py/commit/066dca0714462f659e97f24fb133cbf2c23f6d4b))
* **RdfUtils:** add unit tests ([c6981fc](https://github.com/Nanopublication/nanopub-py/commit/c6981fcc5f13b7bf531def9b332e7ddc0555c293))
* replace test files with testsuite project ([6681b8c](https://github.com/Nanopublication/nanopub-py/commit/6681b8ca571780215ce8ad4216560b90e5e57f75))
* **sign_utils:** add unit test for verify_trusty function with real URI ([8918bca](https://github.com/Nanopublication/nanopub-py/commit/8918bcae47b78e75a83ac2d56334dbf2f7e2daed))
* **sign_utils:** add unit test to test the `add_signature` method ([92ad213](https://github.com/Nanopublication/nanopub-py/commit/92ad21324f9e6aef1b28d065440760eac6d7b894))
* **sign_utils:** update test for verify_trusty with a new real URI and remove unused tests ([4a975b2](https://github.com/Nanopublication/nanopub-py/commit/4a975b2916f14d6e38f2b2a0d06db80346b7ea14))
* update `nanopub-java` to v1.86.1 ([1b954d5](https://github.com/Nanopublication/nanopub-py/commit/1b954d565892dde0028799632cabf2814c408dd1))

### Build and continuous integration

* add submodule fetch to git checkout command ([948d16c](https://github.com/Nanopublication/nanopub-py/commit/948d16c834f4c3774e2e08edc403cadf956278a0))
* **autorelease:** update workflow for publishing to PyPI using semantic-release ([2b718bd](https://github.com/Nanopublication/nanopub-py/commit/2b718bd7c7e04d4021fa053949426beaeda5a601))
* disable fail-fast in test strategy for testing with both rdflib versions ([97a5204](https://github.com/Nanopublication/nanopub-py/commit/97a52042628323e3f6e237e100f73c2428235545))
* migrate from Poetry to UV for dependency management and CI setup ([16bed0b](https://github.com/Nanopublication/nanopub-py/commit/16bed0ba7284214815741f717a27c6e5014852b8))
* **test:** update rdflib version to v6.3.2 ([a402496](https://github.com/Nanopublication/nanopub-py/commit/a4024968dce2908a1ee92272d5aca2436d2c3f5f))
* update actions/checkout action to v6.0.2 ([e1cd994](https://github.com/Nanopublication/nanopub-py/commit/e1cd994329874e4f95a78c58496e9700fa39e2bb))
* update actions/setup-python action to v6.2.0 ([13e8f8b](https://github.com/Nanopublication/nanopub-py/commit/13e8f8b0bc1f2231c564f3b87b09475195949877))
* update poetry install command to install main, test and dev dependencies for testing in CI ([dce623c](https://github.com/Nanopublication/nanopub-py/commit/dce623c6057a9e70ab7268c1d18e223b31d71510))
* update Poetry to v2.3.2 ([cc50ddd](https://github.com/Nanopublication/nanopub-py/commit/cc50ddd4cf36ed92a288c560ec30dccd0bf3e554))
* update Poetry to v2.3.2 ([b941417](https://github.com/Nanopublication/nanopub-py/commit/b9414174cc05d177deb4eb29d92b3f8c8fcc4be3))

### General maintenance

* **gitignore:** add examples/*.trig files ([ea5559b](https://github.com/Nanopublication/nanopub-py/commit/ea5559bcc9783ae0e18bf7321b20ce5e2128aa6b))
* **RdfUtils, utils:** improve separator handling for nanopub URIs ([3c5bc85](https://github.com/Nanopublication/nanopub-py/commit/3c5bc85a18cb6030efb7b62ed45e0a8502a7fc2c))
* **README:** add semantic-release badge and improve formatting ([d77d34a](https://github.com/Nanopublication/nanopub-py/commit/d77d34ae19f67c363490040efdfe5023a6080a19))
* **README:** update broken DOI badge link ([550113a](https://github.com/Nanopublication/nanopub-py/commit/550113a489cd207f1126bf68d900408dbaad6a50))
* **readme:** update test badge workflow link ([7347463](https://github.com/Nanopublication/nanopub-py/commit/7347463ba9497b16df4ec544b905d61acc6bb3d7))
* remove JavaWrapper and nanopub-java references ([98326e1](https://github.com/Nanopublication/nanopub-py/commit/98326e1f68424a7b1b0806601f3f7eb3e133eead))
* remove redundant parhenteses ([140cf29](https://github.com/Nanopublication/nanopub-py/commit/140cf29d140deffc568fe26b0fb8f7be86c7d7ec))
* remove testsuite submodule ([c02fbeb](https://github.com/Nanopublication/nanopub-py/commit/c02fbebf6c37466752431c0155b6781f41db1175))
* remove unnecessary parameter from test_nanopub_fetch function ([8bbe81a](https://github.com/Nanopublication/nanopub-py/commit/8bbe81ad863256a895978fb5366610e6a3135e24))
* remove unused imports ([8468f26](https://github.com/Nanopublication/nanopub-py/commit/8468f26b1df602a09747dbffa29f12a498824a86))
* replace `poetry` with `uv` ([a56ef65](https://github.com/Nanopublication/nanopub-py/commit/a56ef6513a07b5a9156cac561c9fd37085bbae6e))
* **sem-release:** add configuration ([91e2c1f](https://github.com/Nanopublication/nanopub-py/commit/91e2c1f2f89d78a42f94c17799b396ee7531b0ce))
* **sem-release:** add dependencies ([a2ae24b](https://github.com/Nanopublication/nanopub-py/commit/a2ae24b0f37737aa0caec968320b95e1fafec6d0))
* **sem-release:** update tag format in configuration ([5ec1223](https://github.com/Nanopublication/nanopub-py/commit/5ec1223e9b0cee9018f072756a3bfd8a88ee9da2))
* update docs annotations ([90c0553](https://github.com/Nanopublication/nanopub-py/commit/90c055337c5d91a2bd46160cab4c5f8bc8cb9291))
* update documentation to remove references to nanopub-java ([4e706b7](https://github.com/Nanopublication/nanopub-py/commit/4e706b767c9aabe05dee5dbde87ea41684c9eafd))
* update homepage URL ([b414e09](https://github.com/Nanopublication/nanopub-py/commit/b414e0919b856cadfca93e357537743dcba335a3))
* update poetry.lock ([e0c5df0](https://github.com/Nanopublication/nanopub-py/commit/e0c5df0003c7e3e41308f45ebf2ec6f9d8922c6a))
* update testsuite submodule reference ([263ffff](https://github.com/Nanopublication/nanopub-py/commit/263ffffa35a5159a18df20e16cb9764dcdfc1682))

### Refactoring

* clean up imports and formatting in test files ([06833fb](https://github.com/Nanopublication/nanopub-py/commit/06833fbd1020383337fbe0bc99e02f48319799b6))
* **namespaces:** remove PROV namespace definition and use the one provided by rdflib ([b960e2d](https://github.com/Nanopublication/nanopub-py/commit/b960e2d47ec6510561778bc8b791ec4ecb15699a))
* **RdfUtils:** move trusty uri checker to TrustyUriUtils class ([6367cc8](https://github.com/Nanopublication/nanopub-py/commit/6367cc84778b4bfeb4a81d4d2b40a5d8c9286d10))
* **test_cli:** use NanopubTestSuite fixture instead of local testsuite files ([7e02527](https://github.com/Nanopublication/nanopub-py/commit/7e0252795a3b51a6bc945a2b8c40b952d23500cf))
* **test_nanopub:** improve readability of test_metadata_matches_graph and remove redundant test_source_uri_resolved_from_trusty_fetch ([292918f](https://github.com/Nanopublication/nanopub-py/commit/292918f0beec5be3316c155efa60e02df14aea73))
* **test_nanopub:** integrate TestSuiteSubfolder for fixture management ([c787cda](https://github.com/Nanopublication/nanopub-py/commit/c787cdad2deeb5425af0c1809b50bcfd65875982))
* **test_profile:** replace local keys with signing keys from NanopubTestSuite ([498e781](https://github.com/Nanopublication/nanopub-py/commit/498e7819e4ceeec813a184430a77799ee34d9896))
* **test_testsuite:** update tests to use parameterized fixtures ([0e80ee6](https://github.com/Nanopublication/nanopub-py/commit/0e80ee6a098e5f382ccf2cdde2ff96c7a27b5c7e))

# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2022-12-15
Massive overhaul of the nanopub library with backwards incompatible changes.
### Changed
* The documentation website has been updated to use mkdocs
* The doc website is now published to GitHub Pages via the build.yml workflow if the tests pass.
* Profile private key can be now be loaded from a string instead of only a Path. This can be convenient if someone wants to load keys from anywhere else than a local file (e.g. network). There are still helpers functions to easily load from the profile.yml file.
* The private and public key are now optional, a new keypair will be generated if the private key is missing. And the public key can be generated from the private key automatically if it is missing (orcid_id, name are still mandatory)
* There is now a NanopubConfig object to hold the various arguments used to define the nanopub server where it will be published and which infos to attach to a nanopub.
* Signing is now done in python, removing the dependency on java
* java_wrapper is moved to the tests so it can still be used to compare signed nanopubs when testing
* The Publication class has been renamed to Nanopub. That makes a lot of "Nanopub" in the code, but it is more consistent and easier to remember
* Signing is now done directly on the Nanopub object (we don't use the client anymore for this): np.sign() and the np object is updated with the signed RDF (cf. the new doc below to see complete examples). This is convenient because it allows to define Templates for common nanopublications by inhereting the main Nanopub object, cf. existing template: Nanopub intro, Nanopub Index, Claim, Retract, Update
* The NanopubClient object is now mainly used for search functions (through the grlc API), no changes there
* The setup_nanopub_profile CLI was changed to a new CLI with multiple actions:
  * np setup prompt the existing CLI workflow to setup your nanopub profile
  * np profile check the current user profile used by the nanopub library (~/.nanopub/profile.yml)
  * np sign nanopub.trig to sign a nanopub file
  * np publish signed.nanopub.trig to publish a nanopub file (signed or not)
  * np check signed.nanopub.trig to check if a signed nanopub file is valid
* Changed the uses of print() to use python logging (which enable users of the library to configure the level of logs they want, setting to INFO will show all existing prints)
* A battery of tests was added using the same testsuite as nanopub-java to make sure the nanopubs signed with python are valid and follows the same standards: https://github.com/vemonet/nanopub/blob/sign-in-python/tests/test_testsuite.py#L10
* Most of the existing tests for the client search have been kept
* Updated the build.yml workflow to tests with all python versions from 3.7 to 3.10
* Linting now also check types with mypy (not strict)
* The setup.py + all files for python dev config such as .flake8 have been merged in 1 pyproject.tml file using the hatch build backend
* Updated the setup for development, it does not require any tool that is not built in python: only venv ands pip are required (or you can use hatch to handle install and virtual envs for you). Checkout the development docs page for the complete instructions.

## [1.2.11] - 2022-09-27
### Added
* Support for rdflib v6
* Added options to let users choose if they want prov:generatedAtTime and prov:attributedTo automatically added to prov/pubinfo graphs

## [1.2.10] - 2021-09-01
### Changed
* Use latest yatiml version instead of pinned version

## [1.2.9] - 2021-09-01
### Added
* Include LICENSE file in python setup

## [1.2.8] - 2021-09-01

### Added
* Also publish sdist when publishing to pypi

## [1.2.7] - 2021-06-25

### Changed
* Prevent `setup_nanopub_profile` from ever overwriting key pair

### Fixed
* Pin `click` at version 7.1.2, as versions >8 break `setup_nanopub_profile`

## [1.2.6] - 2021-04-30

### Added
* Search result dicts now contain nanopublication label too, if provided by the grlc endpoint.

## [1.2.5] - 2021-03-05

### Fixed
* Fix bug that overwrites optional pubinfo and prov in `from_assertion()` calls.

## [1.2.4] - 2021-03-04

### Fixed
* Fix bug where user rdf was being mutated during publishing.

## [1.2.3] - 2021-02-05

### Added
* Added new `publication_attributed_to` argument to `Publication.from_assertion()`. Allows the `pubinfo` attribution to be manually set if desired.

## [1.2.2] - 2021-01-29

### Fixed
* Fix FileAlreadyExists bug in `setup_nanopub_profile`

## [1.2.1] - 2021-01-22

### Changed
* Rename `setup_profile` to `setup_nanopub_profile` to avoid ambiguity/clashes with other tools

### Fixed
* Make `nanopub` package compatible Windows operating system
* Added UTF-8 related flags to nanopub-java (in java call) to fix issues with certain characters on certain java builds
* Make regex in orcid validation accept ids ending with 'X'

## [1.2.0] - 2020-12-23

### Added
* Added Zenodo badge to README
* Pagination of results for search methods of `NanopubClient`

### Changed
* `nanopub-java` dependency is installed upon installation instead of upon runtime.
* search methods of `NanopubClient` return iterator instead of list


## [1.1.0] - 2020-12-17

### Added
* `.zenodo.json` for linking to zenodo
* `pubkey` option to methods of `NanopubClient` that allows searching for publications
    signed with the given pubkey. For these methods:
    - `find_nanopubs_with_text`
    - `find_nanopubs_with_pattern`
    - `find_things`
* `filter_retracted` option to methods of `NanopubClient` that allows searching for publications
    that are note retracted. For these methods:
    - `find_nanopubs_with_text`
    - `find_nanopubs_with_pattern`
    - `find_things`
* `NanopubClient.find_retractions_of` method to search retractions of a given nanopublication.
* `Publication.signed_with_public_key` property: the public key that the publication was signed with.
* `Publication.is_test_publication` property: denoting whether this is a publicaion on the test server.

### Changed
* Improved error message by pointing to documentation instead of Readme upon ProfileErrors

### Fixed
* Catch FileNotFoundError when profile.yml does not exist, raise ProfileError with useful messageinstead.
* Fixed broken link to documentation in README.md

## [1.0.0] - 2020-12-08

NB: All changes before [1.0.0] are collapsed in here (even though there were multiple pre-releases)
### Added
- `nanopub.client` module with the NanopubClient class that implements:
  * Searching (being a client with a direct (but incomplete) mapping to the nanopub server grlc endpoint):
    * `find_nanopubs_with_text` method
    * `find_nanopubs_with_pattern` method
    * `find_things` method
  * Fetching:
    * `fetch` method to fetch a nanopublication
  * Publishing:
    * Publish a statement using `claim` method
    * Publish a `Publication` object with `publish` method
  * Retracting:
    * Publish a retraction of an existing nanopublication created by this user (i.e. signed with same RSA key)

  * Test server functionality
    * Client can optionally be set to publish to (and fetch from) the nanopub test servers only.

- `nanopub.publication` module
  * `Publication` class to represent a nanopublication.
  Includes `from_assertion` class method to construct a Publication object
  from an assertion graph
  * `replace_in_rdf` helper method to replace values in RDF
- `nanopub.java_wrapper` module, provides an interface to the nanopub-java tool for
  signing and publishing nanopublications.
- `nanopub.profile` module, getters and setters for the nanopub user profile
- `nanopub.setup_profile`, interactive command-line client to setup user profile
- `nanopub.namespaces`, often-used RDF namespaces
- `examples/`, holds a few notebooks that serve as examples of using the library
- User documentation
