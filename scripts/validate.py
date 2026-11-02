"""Validate the addon and create an allowlisted installation archive. No publication."""
import argparse
from pathlib import Path
import re
import shutil
import subprocess
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ADDON = ROOT / "ForeverElixirManager"
VERSION_RE = r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"


def metadata():
    toc = (ADDON / "ForeverElixirManager.toc").read_text(encoding="utf-8-sig")
    fields = {}
    files = []
    for line in toc.splitlines():
        line = line.strip()
        if line.startswith("## "):
            key, value = line[3:].split(":", 1)
            assert key not in fields, f"Duplicate metadata: {key}"
            fields[key] = value.strip()
        elif line and not line.startswith("#"):
            files.append(line)
    assert fields["Interface"] == "16001", "Reassess Forever client before changing interface"
    assert fields["Title"] == "ForeverElixirManager"
    assert re.fullmatch(VERSION_RE, fields["Version"]), "Invalid TOC version"
    assert fields["SavedVariables"] == "ForeverElixirManagerDB"
    assert fields["SavedVariablesPerCharacter"] == "ForeverElixirManagerCharDB"
    assert files == ["ForeverElixirManager.lua"], "Unexpected TOC load list"
    assert {p.name for p in ADDON.iterdir()} == {
        "ForeverElixirManager.toc", "ForeverElixirManager.lua"
    }, "Unexpected addon directory content"
    for name in files:
        assert (ADDON / name).is_file() and (ADDON / name).stat().st_size
    ET.parse(ROOT / "assets/logo.svg")
    assert (ROOT / "assets/logo.jpg").stat().st_size
    assert "Martin Gammelgård Rasmussen" in (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert f"## {fields['Version']}" in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    return fields["Version"]


def lua_tests():
    lua = shutil.which("lua5.1") or shutil.which("lua")
    if lua:
        subprocess.run([lua, "-e", "assert(_VERSION == 'Lua 5.1')"], check=True, cwd=ROOT)
        subprocess.run([lua, "tests/addon_test.lua"], check=True, cwd=ROOT)
    else:
        # Optional Windows development runner; the CI runner uses native Lua 5.1.
        from lupa.lua51 import LuaRuntime
        import os
        previous = Path.cwd()
        try:
            os.chdir(ROOT)
            LuaRuntime().execute((ROOT / "tests/addon_test.lua").read_text(encoding="utf-8"))
        finally:
            os.chdir(previous)


def package(version):
    output = ROOT / "dist" / f"ForeverElixirManager-{version}.zip"
    output.parent.mkdir(exist_ok=True)
    members = {
        "ForeverElixirManager/ForeverElixirManager.toc": ADDON / "ForeverElixirManager.toc",
        "ForeverElixirManager/ForeverElixirManager.lua": ADDON / "ForeverElixirManager.lua",
        "ForeverElixirManager/LICENSE": ROOT / "LICENSE",
    }
    # Stored entries avoid compressor-version differences when comparing release assets.
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, path in members.items():
            entry = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.compress_type = zipfile.ZIP_STORED
            entry.external_attr = 0o644 << 16
            archive.writestr(entry, path.read_bytes())
    with zipfile.ZipFile(output) as archive:
        assert archive.namelist() == list(members)
        assert archive.testzip() is None
        for name, path in members.items():
            assert archive.read(name) == path.read_bytes()
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag")
    args = parser.parse_args()
    version = metadata()
    if args.tag:
        assert re.fullmatch("v" + VERSION_RE, args.tag), "Tag must be vX.Y.Z"
        assert args.tag == "v" + version, "Tag does not match TOC"
    lua_tests()
    archive = package(version)
    print(f"PASS: metadata, Lua 5.1 tests, archive contents: {archive.name}")
    print("NOT VERIFIED: live Forever build, secure clicks, assumed buff names, stacking and taint")


if __name__ == "__main__":
    main()
