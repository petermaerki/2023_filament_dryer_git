import argparse
import importlib
import pathlib
import tempfile
import subprocess
import shutil
import hashlib
import io
import json
import tarfile
import html
from typing import Tuple, Iterator, List, Protocol, runtime_checkable

import git
import mpy_cross_v6_1

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_WEB_DOWNOADSx = "web_downloads"

TAR_SUFFIX = ".tar"
FILENAME_APP_PACKAGE_PY = "app_package.py"


@runtime_checkable
class AppPackage(Protocol):
    name: str
    directory: pathlib.Path
    globs: List[str]


class GitBranch:
    def __init__(self, branch: str, head: git.HEAD):
        assert isinstance(branch, str)
        assert isinstance(head, git.HEAD)
        self.name = branch
        self.head = head

    @property
    def sha(self) -> str:
        return self.head.commit.hexsha

    @property
    def commit_pretty(self) -> str:
        commit = self.head.commit
        return f"{commit.author.name} <{commit.author.email}>: {commit.summary}"

    @property
    def pretty(self) -> str:
        return f"{self.name} - {self.commit_pretty}"


class Git:
    def __init__(self, repo_directory: pathlib.Path):
        assert isinstance(repo_directory, pathlib.Path), str(repo_directory)
        self._repo = git.Repo(repo_directory)
        assert not self._repo.bare
        self.remote_heads: List[str] = [ref.remote_head for ref in self._iter_refs]

    @property
    def _iter_refs(self) -> Iterator[git.RemoteReference]:
        for ref in self._repo.refs:
            if not isinstance(ref, git.RemoteReference):
                continue
            if ref.remote_head == "HEAD":
                continue
            yield ref

    def _get_ref(self, remote_head: str) -> git.RemoteReference:
        for ref in self._iter_refs:
            if ref.remote_head == remote_head:
                return ref
        raise Exception(f"Not found: remote_head '{remote_head}'")

    def checkout(self, remote_head: str, no_checkout: bool) -> GitBranch:
        assert isinstance(remote_head, str)
        assert isinstance(no_checkout, bool)

        if no_checkout:
            return GitBranch(branch=remote_head, head=self._repo.head)

        ref = self._get_ref(remote_head=remote_head)
        head = ref.checkout()
        assert isinstance(head, git.HEAD)
        return GitBranch(branch=remote_head, head=head)


class IndexHtml:
    def __init__(self, directory: pathlib.Path, title: str, verbose: bool):
        assert isinstance(directory, pathlib.Path)
        assert isinstance(title, str)
        assert isinstance(verbose, bool)

        self._verbose = verbose
        self.directory = directory
        directory.mkdir(parents=True, exist_ok=True)
        self.html = self.filename.open("w")
        self.add_h1(title=title)

    @property
    def filename(self) -> pathlib.Path:
        return self.directory / "index.html"

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.html.close()

    def add_h1(self, title: str) -> None:
        self.html.write(f"<h1>{html.escape(title)}</h1>\n")

    def add_href(self, link: pathlib.Path, label: str) -> None:
        relative = str(link.relative_to(self.directory))
        self.html.write(
            f'<p><code>{relative}</code> <a href="{relative}">{html.escape(label)}</a></p>\n'
        )

    def add_italic(self, text: str) -> None:
        self.html.write(f"<p><i>{html.escape(text)}</i></p>\n")

    def add_index(self, link: pathlib.Path, tag: str) -> None:
        size = link.stat().st_size
        relative = str(link.relative_to(self.directory))
        self.html.write(
            f'<{tag}>{relative} (<a href="{relative}">{size} Bytes</a>)</{tag}>\n'
        )

    def new_index(self, relative: str, title: str) -> "IndexHtml":
        directory = self.directory / relative
        self.add_href(link=directory, label=title)
        return IndexHtml(directory=directory, title=title, verbose=self._verbose)

    def add_branch(self, branch: GitBranch, dict_tars: dict) -> None:
        assert isinstance(branch, GitBranch)
        assert isinstance(dict_tars, dict)
        if self._verbose:
            print(
                f"  adding branch='{branch.name}' sha='{branch.sha}' last commit='{branch.commit_pretty}'"
            )
        latest = self.directory / "latest" / branch.name
        latest.parent.mkdir(parents=True, exist_ok=True)
        dict_json = dict(
            commit_sha=branch.sha,
            commit_pretty=branch.commit_pretty,
            dict_tars=dict_tars,
        )
        latest.write_text(json.dumps(dict_json, indent=4))
        self.add_index(link=latest, tag="h2")
        self.add_italic(branch.commit_pretty)


class TarSrc:
    def __init__(
        self,
        branch: GitBranch,
        app_package: AppPackage,
        directory_web_downloads: pathlib.Path,
        verbose: bool,
    ):
        assert isinstance(branch, GitBranch)
        assert isinstance(app_package, AppPackage)
        assert isinstance(directory_web_downloads, pathlib.Path)
        assert isinstance(verbose, bool)

        self._verbose = verbose
        self._app_package = app_package
        link = self.version + "/" + (branch.sha + TAR_SUFFIX)
        self.tar_filename = directory_web_downloads / app_package.name / link

        self.tar_filename.parent.mkdir(parents=True, exist_ok=True)
        with self.tar_filename.open("wb") as f:
            files: List[str] = []
            with tarfile.open(name="app.tar", mode="w", fileobj=f) as tar:

                def add_file(name: str, data: bytes):
                    assert isinstance(name, str)
                    assert isinstance(data, bytes)

                    tarinfo = tarfile.TarInfo(name=name)
                    tarinfo.size = len(data)
                    tar.addfile(tarinfo, io.BytesIO(data))

                for glob in app_package.globs:
                    for file in sorted(app_package.directory.rglob(glob)):
                        name, compiled_bytes = self._compile_to_bytes(file)
                        files.append(name)
                        if verbose:
                            print(f"    TarSrc: {name=}")
                        add_file(name, compiled_bytes)

                dict_manifest = dict(
                    files=files,
                    branch=branch.name,
                    commit_sha=branch.sha,
                    commit_pretty=branch.commit_pretty,
                )
                add_file(
                    "config_package_manifest.json",
                    json.dumps(dict_manifest, indent=4).encode(),
                )

        data = self.tar_filename.read_bytes()
        self.dict_tar = dict(
            link=link,
            sha256=hashlib.sha256(data).hexdigest(),
            size_bytes=len(data),
        )

    def _build_filename_relative(self, file: pathlib.Path, suffix: str) -> str:
        assert isinstance(file, pathlib.Path), str(file)
        assert isinstance(suffix, str)
        assert suffix.startswith(".")
        return str(file.with_suffix(suffix).relative_to(self._app_package.directory))

    def _compile_to_bytes(self, file: pathlib.Path) -> Tuple[str, bytes]:
        assert isinstance(file, pathlib.Path)
        filename = self._build_filename_relative(file, ".py")
        compiled_bytes = pathlib.Path(file).read_bytes()
        return filename, compiled_bytes

    @property
    def version(self) -> str:
        return "src"


class TarMpyCross(TarSrc):
    @property
    def version(self) -> str:
        return "mpy_version/6.1"

    def _compile_to_bytes(self, file: pathlib.Path) -> bytes:
        assert isinstance(file, pathlib.Path)
        with tempfile.NamedTemporaryFile() as tmp_file:
            args = [mpy_cross_v6_1.MPY_CROSS_PATH, "-o", tmp_file.name, str(file)]
            proc = subprocess.run(args, capture_output=True)
            if proc.returncode:
                print(f"ERROR: {args}")
                print(f"  stdout={proc.stdout}")
                print(f"  stderr={proc.stderr}")
                print(f"Error: {args}")
                print("Fallback to uncompiled")
                return super()._compile_to_bytes(file)
            if self._verbose:
                print(
                    f"  mpy-cross returned: {proc.stdout.decode().strip()} / {proc.stderr.decode().strip()}"
                )
            filename = self._build_filename_relative(file, ".mpy")
            compiled_bytes = pathlib.Path(tmp_file.name).read_bytes()
            return filename, compiled_bytes


def iter_package_py(parent_directory: pathlib.Path) -> Iterator[AppPackage]:
    for filename in parent_directory.glob(f"**/{FILENAME_APP_PACKAGE_PY}"):
        spec = importlib.util.spec_from_file_location("app_package", filename)
        app_package = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app_package)

        assert isinstance(app_package.name, str)
        assert isinstance(app_package.directory, pathlib.Path)
        assert isinstance(app_package.globs, list)

        yield app_package


def main(repo_directory: pathlib.Path, verbose: bool, no_checkout: bool) -> None:
    assert isinstance(repo_directory, pathlib.Path)
    assert isinstance(verbose, bool)
    assert isinstance(no_checkout, bool)

    directory_web_downloads = repo_directory / DIRECTORY_WEB_DOWNOADSx
    shutil.rmtree(directory_web_downloads, ignore_errors=True)
    directory_web_downloads.mkdir()
    git = Git(repo_directory)

    with IndexHtml(
        directory=directory_web_downloads, title="Downloads", verbose=verbose
    ) as index_top:
        for app_package in iter_package_py(parent_directory=repo_directory):
            app_package_file = pathlib.Path(app_package.__file__)

            with index_top.new_index(
                relative=app_package.name,
                title=f"Application: {app_package.name}",
            ) as index_app:
                for branch in git.remote_heads:
                    if verbose:
                        print(f"app: '{app_package.name}' on branch '{branch}'")

                    branch = git.checkout(remote_head=branch, no_checkout=no_checkout)

                    if not app_package_file.exists():
                        if verbose:
                            print(
                                f"SKIPPED. File does not exist on this branch: {app_package_file}"
                            )
                        continue

                    dict_tars = {}
                    for cls_tar in (TarSrc, TarMpyCross):
                        tar = cls_tar(
                            branch=branch,
                            app_package=app_package,
                            directory_web_downloads=directory_web_downloads,
                            verbose=verbose,
                        )
                        index_app.add_index(link=tar.tar_filename, tag="p")
                        dict_tars[tar.version] = tar.dict_tar

                    index_app.add_branch(branch=branch, dict_tars=dict_tars)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--verbose",
        type=bool,
        default=False,
    )
    parser.add_argument(
        "--no-checkout",
        type=bool,
        default=False,
    )
    parser.add_argument(
        "--repo",
        help=f"The directory containing the '.git' folder.",
    )
    args = parser.parse_args()

    repo_directory = pathlib.Path(args.repo).resolve()
    assert repo_directory.exists(), repo_directory
    main(
        repo_directory=repo_directory,
        verbose=args.verbose,
        no_checkout=args.no_checkout,
    )
