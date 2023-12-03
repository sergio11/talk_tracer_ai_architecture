# googletrans-py

This is a fork of the [googletrans](https://github.com/ssut/py-googletrans) which makes the original package compatible with the latest versions of `httpx`, `httpcore` and their dependencies. This compatibility makes it possible to use `httpx`'s newer versions than `0.13.3`.

The base is taken from the [feature/rpc](https://github.com/ssut/py-googletrans/tree/feature/rpc) branch of googletrans which was the last version, including pre-releases.

Comparing with PyPI, the base uses [v4.0.0rc1](https://pypi.org/project/googletrans/4.0.0rc1/) which was the last version on pypi, including pre-releases.

> **Note**: I have no intention to add features or to maintain this project. This is a temporary solution to a temporary a problem, hopefully.

As the original project ended with version `4.0.0rc1` (pre-release), this fork's versioning starts from `4.0.0` (stable release).

## Installation

### PyPI

This project is available on [PyPI](https://pypi.org/project/googletrans-py) and can be installed using pip.

```shell
pip install googletrans-py
```

### Repository

You can also install the project directly from this repository.

```shell
pip install git+https://github.com/StarkBotsIndustries/googletrans.git
```

## Credits

Original Author - [Suhun Han](https://github.com/ssut)

Original Repository - [googletrans](https://github.com/ssut/py-googletrans)
