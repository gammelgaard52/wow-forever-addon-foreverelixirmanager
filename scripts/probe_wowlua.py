"""Optional, non-gating emulator experiment for issue #4. Never deploys an addon."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--offline", action="store_true", help="Require previously cached Blizzard UI source")
    args = parser.parse_args()
    binary = args.binary.resolve()
    version = subprocess.run([str(binary), "--version"], check=True, capture_output=True, text=True).stdout.strip()
    if version != "wowlua 0.13.8":
        raise ValueError("This experiment requires the reviewed wowlua 0.13.8 binary")
    with tempfile.TemporaryDirectory(prefix="fem-wowlua-probe-") as directory:
        addon = Path(directory) / "ForeverElixirManager"
        addon.mkdir()
        for name in ("ForeverElixirManager.lua", "ForeverElixirManager.toc"):
            shutil.copyfile(ROOT / "ForeverElixirManager" / name, addon / name)
        env = {**os.environ, "WOWLUA_HOME": str(ROOT / "dist/wowlua-cache"),
               "WOWLUA_WOW_PATH": str(Path(directory) / "no-game")}
        # init moves only the disposable copy; the repository layout is untouched.
        subprocess.run([str(binary), "init", "--offline"], cwd=addon, env=env, check=True)
        manifest_path = addon / "wowlua.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["test"] = {"blizzard-ui": True}
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        shutil.copytree(ROOT / "tests/wowlua", addon / "tests")
        command = [str(binary), "test", "--flavor", "camelot", "--color", "never"]
        if args.offline:
            command.append("--offline")
        return subprocess.run(command, cwd=addon, env=env).returncode


if __name__ == "__main__":
    raise SystemExit(main())
