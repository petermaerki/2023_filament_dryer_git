import json
import urequests
import config_secrets


def _read_manifest() -> dict:
    try:
        with open("config_package_manifest.json", "r") as f:
            return json.load(f)
    except OSError:
        return None


def sw_version() -> str:
    manifest = _read_manifest()
    if manifest is None:
        return "?"
    return manifest['commit_sha']
    # return f"{manifest['commit_sha']} {manifest['commit_pretty']}"


def new_version_available(tar_version="src", wdt_feed=lambda: False):
    """
    Return download url if new package is available
    """
    wdt_feed()
    url = config_secrets.APP_PACKAGE_URL + config_secrets.APP_PACKAGE_BRANCH
    response = urequests.get(url)
    wdt_feed()
    assert response.status_code == 200, (response.status_code, url)
    latest_package = response.json()

    dict_tar = latest_package["dict_tars"][tar_version]

    manifest = _read_manifest()
    if manifest is None:
        print("New download: Failed to read 'config_package_manifest.json'")
        return dict_tar

    # print("dict_tar", dict_tar)
    if latest_package["commit_sha"] == manifest["commit_sha"]:
        print("No new download!")
        return None

    print(f"New download: {latest_package['commit_pretty']}")
    return dict_tar
