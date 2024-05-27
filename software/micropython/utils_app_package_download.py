import os
import urequests
import machine
import hashlib
import lib_tarfile
import json
import binascii
import config_secrets

TAR_FILENAME = const("config_package.tar")
FILENAME_UPDATE_SUCCESS = const("update_success.txt")


# class _DirCacheObsolete:
#     def __init__(self):
#         # List all directories
#         # See: https://docs.micropython.org/en/latest/library/os.html#module-os
#         self._dirs = [i[0] for i in os.ilistdir() if i[1] == 0x4000]

#     def makedir_for_file(self, filename: str) -> None:
#         """
#         If the filename is in a directory,
#         creates that directory if it not exists.
#         """
#         dirname = filename.rpartition("/")[0]
#         if dirname == "":
#             return
#         if dirname in self._dirs:
#             return
#         print(f"Create directory {dirname}")
#         os.mkdir(dirname)
#         self._dirs.append(dirname)


# def _makedirs_obsolete(filename: str):
#     """
#     If the filename is in a directory,
#     creates that directory if it not exists.
#     Recurses if required.
#     """
#     dirname = filename.rpartition("/")[0]
#     if dirname == "":
#         # Top directory
#         return
#     try:
#         os.mkdir(dirname)
#     except OSError as ex:
#         if ex.errno == errno.EEXIST:
#             return
#         if ex.errno == errno.ENOENT:
#             # The top directory is missing
#             _makedirs_obsolete(dirname)
#             _makedirs_obsolete(filename)
#         assert False, ex


def _save_response_to_file(response, wdt_feed, chunk_size=2048):
    # https://github.com/SpotlightKid/mrequests/
    with open(TAR_FILENAME, "wb") as f:
        hash = hashlib.sha256()

        while True:
            chunk = response.raw.read(chunk_size)
            if not chunk:
                break
            hash.update(chunk)
            f.write(chunk)
            wdt_feed()

        response.raw.close()
        return binascii.hexlify(hash.digest()).decode("ascii")


def _unpack_tarfile():
    t = lib_tarfile.TarFile(TAR_FILENAME)
    for i in t:
        if i.type == lib_tarfile.DIRTYPE:
            os.mkdir(i.name)
            continue
        f = t.extractfile(i)
        print(f"  {TAR_FILENAME}: {i.name}")
        with open(i.name, "wb") as of:
            of.write(f.read())


def _remove_obsolete_files():
    with open("config_package_manifest.json", "r") as f:
        files = json.load(f)["files"]

    for file in os.listdir():
        if file.startswith("config_"):
            continue
        if file in files:
            continue
        print(f"Remove file {file}")
        try:
            os.remove(file)
        except OsError as e:
            print(f"Failed to remove '{file}': {e}")

    if "main.mpy" in files:
        print("'main.mpy' will not be started by micropython. Add patch!")
        os.rename("main.mpy", "main2.mpy")
        with open("main.py", "w") as f:
            f.write("import main2\n")


def download_new_version(dict_tar: dict, wdt_feed = lambda: False) -> None:
    url = f"{config_secrets.APP_PACKAGE_URL}/{dict_tar['link']}"
    print(f"Download new package from: {url}")
    wdt_feed()
    response = urequests.get(url, stream=True)
    wdt_feed()
    assert response.status_code == 200, response.status_code

    sha256 = _save_response_to_file(response, wdt_feed=wdt_feed)
    sha256_expected = dict_tar["sha256"]
    if sha256 != sha256_expected:
        print(f"{TAR_FILENAME}: {sha256=} {sha256_expected=}!")
        os.remove(TAR_FILENAME)
        return

    wdt_feed()
    _unpack_tarfile()

    wdt_feed()
    _remove_obsolete_files()

    with open(FILENAME_UPDATE_SUCCESS, "w"):
        pass

    os.sync()
    machine.soft_reset()
