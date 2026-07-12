"""Auto-updater pure logic + offline staging (no network, runs on any OS)."""

from __future__ import annotations

import hashlib
import shutil
import sys
import zipfile
from pathlib import Path

import pytest

from cubalite_poster import updater
from cubalite_poster.config import constants

EXE = constants.UPDATE_EXE_NAME


# --- version parsing / comparison ------------------------------------------
@pytest.mark.parametrize(
    "text, expected",
    [
        ("v0.2.0", (0, 2, 0)),
        ("0.10.3", (0, 10, 3)),
        ("v1.0", (1, 0)),
        ("v2.3.4-rc1", (2, 3, 4)),
        ("", None),
        (None, None),
        ("latest", None),
    ],
)
def test_parse_version(text: str | None, expected: tuple[int, ...] | None) -> None:
    assert updater.parse_version(text) == expected


def test_is_newer_strict_and_padded() -> None:
    assert updater.is_newer((0, 2, 0), (0, 1, 9)) is True
    assert updater.is_newer((0, 10, 0), (0, 9, 9)) is True
    assert updater.is_newer((0, 1, 0), (0, 1, 0)) is False
    assert updater.is_newer((0, 2), (0, 2, 0)) is False  # padded equal
    assert updater.is_newer((0, 2, 0), (0, 2)) is False
    assert updater.is_newer((0, 1, 9), (0, 2, 0)) is False


# --- release JSON parsing ---------------------------------------------------
def _release(tag: str = "v0.3.0", *, zip_asset: bool = True, sha: bool = True) -> dict:
    assets = []
    if zip_asset:
        assets.append(
            {"name": EXE.replace(".exe", ".zip"), "browser_download_url": "http://x/z"}
        )
    assets.append(
        {"name": constants.UPDATE_ASSET_NAME, "browser_download_url": "http://x/z.zip"}
    )
    if sha:
        assets.append(
            {
                "name": constants.UPDATE_SHA256_ASSET_NAME,
                "browser_download_url": "http://x/z.sha",
            }
        )
    return {"tag_name": tag, "assets": assets}


def test_parse_release_json_valid() -> None:
    info = updater.parse_release_json(_release())
    assert info is not None
    assert info.tag == "v0.3.0"
    assert info.version == (0, 3, 0)
    assert info.zip_url == "http://x/z.zip"
    assert info.sha256_url == "http://x/z.sha"


def test_parse_release_json_missing_zip_returns_none() -> None:
    data = {"tag_name": "v0.3.0", "assets": [{"name": "other.txt"}]}
    assert updater.parse_release_json(data) is None


def test_parse_release_json_no_sha_is_ok() -> None:
    info = updater.parse_release_json(_release(sha=False))
    assert info is not None and info.sha256_url is None


@pytest.mark.parametrize("data", [None, [], "nope", {"assets": []}])
def test_parse_release_json_garbage(data: object) -> None:
    assert updater.parse_release_json(data) is None


# --- update decision --------------------------------------------------------
def test_should_update_matrix() -> None:
    info = updater.parse_release_json(_release("v0.3.0"))
    assert updater.should_update(info, (0, 2, 0), set()) is True
    assert updater.should_update(info, (0, 3, 0), set()) is False  # equal
    assert updater.should_update(info, (0, 4, 0), set()) is False  # older release
    assert updater.should_update(info, (0, 2, 0), {"v0.3.0"}) is False  # skipped
    assert updater.should_update(info, None, set()) is False  # unknown installed
    assert updater.should_update(None, (0, 2, 0), set()) is False


# --- sha256 -----------------------------------------------------------------
def test_parse_sha256_text_formats() -> None:
    digest = "a" * 64
    assert updater.parse_sha256_text(f"{digest.upper()}  CubalitePoster.zip") == digest
    assert updater.parse_sha256_text(digest) == digest
    assert updater.parse_sha256_text("no hash here") is None
    assert updater.parse_sha256_text(None) is None


def test_verify_sha256(tmp_path: Path) -> None:
    blob = tmp_path / "b.bin"
    blob.write_bytes(b"hello world")
    good = hashlib.sha256(b"hello world").hexdigest()
    assert updater.verify_sha256(blob, good) is True
    assert updater.verify_sha256(blob, "0" * 64) is False


# --- payload discovery ------------------------------------------------------
def test_find_payload_root_nested_and_flat(tmp_path: Path) -> None:
    nested = tmp_path / "nested"
    (nested / "CubalitePoster").mkdir(parents=True)
    (nested / "CubalitePoster" / EXE).write_bytes(b"MZ")
    assert updater.find_payload_root(nested, EXE) == nested / "CubalitePoster"

    flat = tmp_path / "flat"
    flat.mkdir()
    (flat / EXE).write_bytes(b"MZ")
    assert updater.find_payload_root(flat, EXE) == flat

    empty = tmp_path / "empty"
    (empty / "_internal").mkdir(parents=True)
    assert updater.find_payload_root(empty, EXE) is None


def test_read_skipped(tmp_path: Path) -> None:
    f = tmp_path / "skip.txt"
    assert updater.read_skipped(f) == set()  # missing file
    f.write_text("v0.3.0\n\nv0.4.0\n")
    assert updater.read_skipped(f) == {"v0.3.0", "v0.4.0"}


# --- path resolution --------------------------------------------------------
def test_resolve_paths_uses_folder_name(tmp_path: Path) -> None:
    exe = tmp_path / "MyPoster" / EXE
    paths = updater.resolve_paths(exe)
    assert paths.install == tmp_path / "MyPoster"
    assert paths.staging == tmp_path / ("MyPoster" + constants.UPDATE_STAGING_SUFFIX)
    assert paths.backup == tmp_path / ("MyPoster" + constants.UPDATE_BACKUP_SUFFIX)


# --- staging from a real zip (offline) --------------------------------------
def _make_nested_zip(dest: Path, *, with_exe: bool = True, evil: bool = False) -> None:
    with zipfile.ZipFile(dest, "w") as zf:
        if evil:
            zf.writestr("../escaped.txt", b"x")
            return
        if with_exe:
            zf.writestr(f"CubalitePoster/{EXE}", b"MZ fake exe")
        zf.writestr("CubalitePoster/_internal/base_library.zip", b"stub")


def _paths_in(tmp_path: Path) -> updater.UpdatePaths:
    install = tmp_path / "CubalitePoster"
    install.mkdir()
    (install / EXE).write_bytes(b"OLD")
    return updater.resolve_paths(install / EXE)


def _stage_with_local_zip(
    monkeypatch: pytest.MonkeyPatch, zip_src: Path, info: updater.ReleaseInfo, paths
) -> bool:
    def fake_download(url: str, dest: Path, *_a: object, **_k: object) -> None:
        shutil.copy(zip_src, dest)

    monkeypatch.setattr(updater, "_download", fake_download)
    return updater.stage_update(info, paths)


def test_stage_update_nested_zip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    zip_src = tmp_path / "src.zip"
    _make_nested_zip(zip_src)
    paths = _paths_in(tmp_path)
    info = updater.ReleaseInfo("v0.9.0", (0, 9, 0), "http://x/z.zip", None)

    assert _stage_with_local_zip(monkeypatch, zip_src, info, paths) is True
    assert (paths.staging / EXE).is_file()
    assert updater.has_staged_update(paths) is True
    # tag sidecar written so the exit-time swapper can skip a bad build
    assert paths.tag_file.read_text().strip() == "v0.9.0"
    # transient dirs cleaned up
    assert not paths.extract.exists()
    assert not paths.zip_tmp.exists()


def test_stage_update_missing_exe_returns_false(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    zip_src = tmp_path / "src.zip"
    _make_nested_zip(zip_src, with_exe=False)
    paths = _paths_in(tmp_path)
    info = updater.ReleaseInfo("v0.9.0", (0, 9, 0), "http://x/z.zip", None)

    assert _stage_with_local_zip(monkeypatch, zip_src, info, paths) is False
    assert not paths.staging.exists()


def test_stage_update_rejects_zip_slip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    zip_src = tmp_path / "evil.zip"
    _make_nested_zip(zip_src, evil=True)
    paths = _paths_in(tmp_path)
    info = updater.ReleaseInfo("v0.9.0", (0, 9, 0), "http://x/z.zip", None)

    assert _stage_with_local_zip(monkeypatch, zip_src, info, paths) is False
    assert not (tmp_path / "escaped.txt").exists()


def test_stage_update_bad_sha_returns_false(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    zip_src = tmp_path / "src.zip"
    _make_nested_zip(zip_src)
    paths = _paths_in(tmp_path)
    info = updater.ReleaseInfo("v0.9.0", (0, 9, 0), "http://x/z.zip", "http://x/z.sha")

    monkeypatch.setattr(updater, "_http_get_text", lambda *_a, **_k: "0" * 64)
    assert _stage_with_local_zip(monkeypatch, zip_src, info, paths) is False
    assert not paths.staging.exists()


def test_stage_update_good_sha_succeeds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    zip_src = tmp_path / "src.zip"
    _make_nested_zip(zip_src)
    good = hashlib.sha256(zip_src.read_bytes()).hexdigest()
    paths = _paths_in(tmp_path)
    info = updater.ReleaseInfo("v0.9.0", (0, 9, 0), "http://x/z.zip", "http://x/z.sha")

    monkeypatch.setattr(updater, "_http_get_text", lambda *_a, **_k: f"{good}  x.zip")
    assert _stage_with_local_zip(monkeypatch, zip_src, info, paths) is True
    assert (paths.staging / EXE).is_file()


# --- swapper script generation ---------------------------------------------
def test_build_swapper_script_is_rename_only(tmp_path: Path) -> None:
    paths = updater.resolve_paths(tmp_path / "CubalitePoster" / EXE)
    script = updater.build_swapper_script(
        paths, pid=4321, skip_path=tmp_path / "skip.txt", tag="v0.9.1"
    )
    assert "4321" in script
    assert constants.UPDATE_SELFCHECK_FLAG in script
    assert EXE in script  # tasklist filters on the image name
    assert str(paths.staging) in script and str(paths.backup) in script
    # the real tag must be baked as a literal, not the empty self-reference
    # `set "TAG=%TAG%"` that made the skip guard write "ECHO is on." forever
    assert 'set "TAG=v0.9.1"' in script
    assert 'set "TAG=%TAG%"' not in script
    assert 'del "%~f0"' in script  # self-deletes
    # rename-only invariant: never copy, and never rmdir the *live* install dir
    lowered = script.lower()
    assert "xcopy" not in lowered and "robocopy" not in lowered
    assert "copy " not in lowered
    assert 'rmdir /s /q "%install%"' not in lowered
    # the first rollback move is guarded so a locked bad build can't nest BACKUP
    assert "if errorlevel 1 goto rollbacklocked" in script
    # the tag file is dropped only on the 3 paths where staging is consumed
    # (success, rollback, rollbacklocked) — never on giveup/restore, or a
    # surviving staged tree would lose its tag and re-open the skip loop
    assert script.count('del "%TAGFILE%"') == 3


def test_build_swapper_script_sanitizes_tag(tmp_path: Path) -> None:
    paths = updater.resolve_paths(tmp_path / "CubalitePoster" / EXE)
    script = updater.build_swapper_script(
        paths, pid=1, skip_path=tmp_path / "skip.txt", tag='v1.0 & echo "x"'
    )
    # metacharacters that could break the `echo <tag>` line are stripped
    assert 'set "TAG=v1.0echox"' in script


def test_has_staged_update_requires_tag(tmp_path: Path) -> None:
    """An exit-race can leave `.new` without its tag; that must not count as
    staged (else the swapper would apply it with an empty, non-recording tag)."""
    paths = _paths_in(tmp_path)
    paths.staging.mkdir()
    (paths.staging / EXE).write_bytes(b"MZ")
    assert updater.has_staged_update(paths) is False  # tag sidecar missing
    paths.tag_file.write_text("v0.9.0")
    assert updater.has_staged_update(paths) is True


def test_run_selfcheck_survives_no_stdout(monkeypatch: pytest.MonkeyPatch) -> None:
    """Regression: the windowed frozen exe has ``sys.stdout is None``. The
    diagnostic write must not raise, or the swapper would roll back and
    skip-list every good build (auto-update silently 100% dead)."""
    monkeypatch.setattr(sys, "stdout", None)
    assert updater.run_selfcheck() == 0
