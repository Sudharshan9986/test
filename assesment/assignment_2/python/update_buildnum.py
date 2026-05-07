"""Update the build number in two files.

Reads:
- BuildNum (env var or --build-num)
- SourcePath (env var or --source-path)

Edits:
- $SourcePath/develop/global/src/SConstruct : point=123,  -> point=<BuildNum>,
- $SourcePath/develop/global/src/VERSION    : ADLMSDK_VERSION_POINT= 123 -> ...= <BuildNum>
"""

from __future__ import annotations

import argparse
import os
import re
import tempfile
from pathlib import Path


class UpdateError(RuntimeError):
    pass


_SCONSTRUCT_RE = re.compile(r"\bpoint\s*=\s*(\d+)\s*,")
_VERSION_RE = re.compile(r"^(ADLMSDK_VERSION_POINT=\s*)(\d+)(\s*)$", re.MULTILINE)


def _parse_build_num(value: str) -> int:
    v = value.strip()
    try:
        n = int(v, 10)
    except ValueError as e:
        raise UpdateError(f"BuildNum must be an integer, got {value!r}") from e
    if n < 0:
        raise UpdateError(f"BuildNum must be >= 0, got {n}")
    return n


def resolve_config(build_num: int | None = None, source_path: str | Path | None = None) -> tuple[int, Path]:
    if build_num is None:
        if "BuildNum" not in os.environ:
            raise UpdateError("Missing env var BuildNum (or pass --build-num).")
        build_num = _parse_build_num(os.environ["BuildNum"])

    if source_path is None:
        if "SourcePath" not in os.environ:
            raise UpdateError("Missing env var SourcePath (or pass --source-path).")
        source_path = os.environ["SourcePath"]

    return int(build_num), Path(source_path)


def atomic_write_text(path: Path, text: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Preserve file mode if the file already exists.
    old_mode = None
    try:
        old_mode = path.stat().st_mode
    except FileNotFoundError:
        pass

    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())

        os.replace(tmp_path, path)  # atomic on Windows + POSIX
        if old_mode is not None:
            os.chmod(path, old_mode)
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            # Best-effort cleanup; replacement may have succeeded.
            pass


def update_sconstruct(contents: str, build_num: int) -> tuple[str, int]:
    """
    Replace occurrences of `point=<digits>,` (allowing whitespace) with `point=<build_num>,`.
    Returns (new_contents, replacements_count).
    """

    def repl(_: re.Match[str]) -> str:
        return f"point={build_num},"

    new, count = _SCONSTRUCT_RE.subn(repl, contents)
    return new, count


def update_version(contents: str, build_num: int) -> tuple[str, int]:
    """
    Replace the numeric value on the `ADLMSDK_VERSION_POINT=` line.
    Preserves whitespace after '=' and at end-of-line (including newline).
    Returns (new_contents, replacements_count).
    """

    def repl(m: re.Match[str]) -> str:
        return f"{m.group(1)}{build_num}{m.group(3)}"

    new, count = _VERSION_RE.subn(repl, contents)
    return new, count


def update_files(build_num: int, source_path: Path) -> None:
    base = Path(source_path) / "develop" / "global" / "src"
    s_path = base / "SConstruct"
    v_path = base / "VERSION"

    try:
        s_in = s_path.read_text(encoding="utf-8")
    except FileNotFoundError as e:
        raise UpdateError(f"Missing file: {s_path}") from e

    try:
        v_in = v_path.read_text(encoding="utf-8")
    except FileNotFoundError as e:
        raise UpdateError(f"Missing file: {v_path}") from e

    s_out, s_count = update_sconstruct(s_in, build_num)
    if s_count == 0:
        raise UpdateError(f"Did not find `point=<number>,` in {s_path}")

    v_out, v_count = update_version(v_in, build_num)
    if v_count == 0:
        raise UpdateError(f"Did not find `ADLMSDK_VERSION_POINT= <number>` in {v_path}")

    atomic_write_text(s_path, s_out)
    atomic_write_text(v_path, v_out)


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Update build number in SConstruct and VERSION.")
    p.add_argument("--build-num", type=int, default=None, help="Override env var BuildNum")
    p.add_argument("--source-path", type=Path, default=None, help="Override env var SourcePath")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    build_num, source_path = resolve_config(build_num=args.build_num, source_path=args.source_path)
    update_files(build_num, source_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
