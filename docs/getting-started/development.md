[![Version](https://img.shields.io/pypi/v/nanopub)](https://pypi.org/project/nanopub) [![Python versions](https://img.shields.io/pypi/pyversions/nanopub)](https://pypi.org/project/nanopub) [![Pull requests welcome](https://img.shields.io/badge/pull%20requests-welcome-brightgreen)](https://github.com/Nanopublication/nanopub-py/fork)

[![Python application](https://github.com/Nanopublication/nanopub-py/actions/workflows/build.yml/badge.svg)](https://github.com/Nanopublication/nanopub-py/actions/workflows/build.yml){:
target="_
blank"} [![Publish](https://github.com/Nanopublication/nanopub-py/actions/workflows/pypi.yml/badge.svg)](https://github.com/Nanopublication/nanopub-py/actions/workflows/pypi.yml){:
target="_
blank"} [![cffconvert](https://github.com/Nanopublication/nanopub-py/actions/workflows/cffconvert.yml/badge.svg)](https://github.com/Nanopublication/nanopub-py/actions/workflows/cffconvert.yml){:
target="_blank"}

## 📥 Install for development

Clone the repository and go in the project folder:

```bash
git clone https://github.com/Nanopublication/nanopub-py
cd nanopub
```

To install the project for development you can use [`uv`](https://docs.astral.sh/uv/).

If you don't have it installed, first install it following the
official [installation guide](https://docs.astral.sh/uv/getting-started/installation/).

Once `uv` is installed, you can install all the project dependencies by running:

```bash
uv sync
```

Optionally, install `pre-commit` to enable automated formatting and linting of the code at each commit:

```bash
pre-commit install
```

## 🧑‍💻 Development workflow

Try to sign a nanopublication with the code defined in `scripts/dev.py` to test your changes:

```bash
./scripts/dev.sh
```

The code will be automatically formatted when you commit your changes using `pre-commit`. But you can also run the
script to format the code yourself:

```bash
./scripts/format.sh
```

Check the code for errors, and if it is in accordance with the PEP8 style guide, by running `flake8` and `mypy`:

```bash
./scripts/lint.sh
```

## ✅ Run the tests

[![Python application](https://github.com/Nanopublication/nanopub-py/actions/workflows/build.yml/badge.svg)](https://github.com/Nanopublication/nanopub-py/actions/workflows/build.yml){:
target="_blank"}

Tests are automatically run by a GitHub Actions workflow when new code is pushed to the GitHub repository.

=== "bash"

	Run the tests locally:

	```bash
	./scripts/test.sh
	```

	You can also run only a specific test:

	```bash
	./scripts/test.sh tests/test_nanopub.py::test_nanopub_sign_uri
	```

=== "uv"

	Run the tests locally:

	```bash
	uv run pytest
	```

	You can also run only a specific test:

	```bash
	uv run pytest tests/test_nanopub.py::test_nanopub_sign_uri
	```

## 📖 Generate docs

[![Publish docs](https://github.com/Nanopublication/nanopub-py/actions/workflows/build.yml/badge.svg)](https://github.com/Nanopublication/nanopub-py/actions/workflows/build.yml){:
target="_blank"}

The documentation (this website) is automatically generated from the markdown files in the `docs` folder and python
docstring comments, and published by a GitHub Actions workflow.

Serve the docs on [http://localhost:8008](http://localhost:8008){:target="_blank"}

=== "bash"

    ```bash
    ./scripts/docs.sh
    ```

=== "uv"

    ```bash
    uv run mkdocs serve
    ```

## 🏷️ Publish a new release

[![Publish to PyPI](https://github.com/Nanopublication/nanopub-py/actions/workflows/pypi.yml/badge.svg)](https://github.com/Nanopublication/nanopub-py/actions/workflows/pypi.yml){:
target="_blank"}

The release are automatically triggered using the `semantic-release` plugin together with conventional commits.
