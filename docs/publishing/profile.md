# Set the user profile

!!! info "Prerequisite for publishing"

	Before you can sign and publish you should [setup your profile](/nanopub/getting-started/setup), check if it is properly set by running `np profile` in your terminal.

## 👤 Use the default user profile

If you have setup a profile on your machine following the [setup instructions](/nanopub/getting-started/setup), you can easily load the default profile (defined in `$HOME/.nanopub/profile.yml`):

```python
from nanopub import load_profile

p = load_profile()
```

## ✍️ Define the user profile

Otherwise, if you wish to have flexibility when defining the user profile, there are multiple options:

### Load a profile file

Provide a specific path to a `profile.yml` file when using the `load_profile()` function:

```python
from nanopub import load_profile

p = load_profile(Path('/path/to/profile.yml'))
```

### Provide the keys filepaths

If you need to switch between multiple keys it can be convenient to be able to define the profile directly in your code, you can do so with the `Profile` class:

```python
from pathlib import Path
from nanopub import Profile

p1 = Profile(
    name='Your Name',
    orcid_id='https://orcid.org/0000-0000-0000-0001',
    private_key=Path.home() / "id_rsa",
    public_key=Path.home() / "id_rsa.pub"
)
```

### Provide the keys as strings

If you need to switch between multiple keys you can also provide the private and public keys as string, without needing to store them in files:

```python
from nanopub import Profile

p = Profile(
    name='Your Name',
    orcid_id='https://orcid.org/0000-0000-0000-0001',
    private_key="YOUR_PRIVATE_KEY",
    public_key="YOUR_PUBLIC_KEY"
)
```

### Generate new keys for your nanopub profile

If you do not provide private and public keys a new key pair will be automatically generated. You can then store it where you want.

```python
from nanopub import Profile

p = Profile(
    name='Your Name',
    orcid_id='https://orcid.org/0000-0000-0000-0001',
)
# By default the profile and keys will be stored in $HOME/.nanopub
p.store()
```
