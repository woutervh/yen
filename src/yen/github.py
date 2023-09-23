import json
import platform
import re
from urllib.request import urlopen

# https://github.com/indygreg/python-build-standalone/releases/download/20230826/cpython-3.11.5+20230826-
MACHINE_SUFFIX = {
    "Darwin": {
        "arm64": "aarch64-apple-darwin-install_only.tar.gz",
        "x86_64": "x86_64-apple-darwin-install_only.tar.gz",
    },
    "Linux": {
        "arm64": {
            "glibc": "aarch64-unknown-linux-gnu-install_only.tar.gz",
            # musl doesn't exist
        },
        "x86_64": {
            "glibc": "x86_64_v3-unknown-linux-gnu-install_only.tar.gz",
            "musl": "x86_64_v3-unknown-linux-musl-install_only.tar.gz",
        },
    },
}

REPO = "indygreg/python-build-standalone"
GITHUB_API_URL = f"https://api.github.com/repos/{REPO}/releases/latest"
DOWNLOAD_URL_TEMPLATE = (
    f"https://github.com/{REPO}/releases/download/{{tag}}/cpython-{{version}}+{{tag}}-"
)
PYTHON_VERSION_REGEX = re.compile(r"cpython-(\d+\.\d+\.\d+)")


class NotAvailable(Exception):
    """Raised when the asked Python version is not available."""


def get_latest_python_releases() -> list[str]:
    """Returns the list of python download links from the latest github release."""
    with urlopen(GITHUB_API_URL) as response:
        release_data = json.load(response)

    return [asset["browser_download_url"] for asset in release_data["assets"]]


def list_pythons() -> dict[str, str]:
    """Returns available python versions for your machine and their download links."""
    download_link_suffix = MACHINE_SUFFIX[platform.system()][platform.machine()]
    # linux names are nested under glibc or musl builds
    libc_version = platform.libc_ver()[0]
    if libc_version:
        download_link_suffix = download_link_suffix[libc_version]

    python_releases = get_latest_python_releases()

    available_python_links = [
        link for link in python_releases if link.endswith(download_link_suffix)
    ]

    python_versions: dict[str, str] = {}
    for link in available_python_links:
        match = PYTHON_VERSION_REGEX.search(link)
        assert match is not None
        python_version = match[1]
        python_versions[python_version] = link

    sorted_python_versions = {
        version: python_versions[version]
        for version in sorted(
            python_versions,
            # sort by semver
            key=lambda version: [int(k) for k in version.split(".")],
            reverse=True,
        )
    }
    return sorted_python_versions


def resolve_python_version(requested_version: str) -> None:
    pythons = list_pythons()

    for version, version_download_link in pythons.items():
        if version.startswith(requested_version):
            python_version = version
            download_link = version_download_link
            break
    else:
        raise NotAvailable

    return python_version, download_link
