import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from assesment.assignment_2.python.update_buildnum import (
    UpdateError,
    resolve_config,
    update_sconstruct,
    update_version,
    update_files,
)


class UpdateBuildNumTests(unittest.TestCase):
    def test_update_sconstruct_replaces_point(self) -> None:
        src = "major=1\npoint=123,\npoint = 9 ,\n"
        out, count = update_sconstruct(src, 456)
        self.assertEqual(count, 2)
        self.assertIn("point=456,", out)
        self.assertNotIn("point=123,", out)

    def test_update_version_preserves_whitespace(self) -> None:
        src = "X=1\nADLMSDK_VERSION_POINT=\t123\nY=2\n"
        out, count = update_version(src, 7)
        self.assertEqual(count, 1)
        self.assertIn("ADLMSDK_VERSION_POINT=\t7\n", out)

    def test_update_files_end_to_end(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            target = root / "develop" / "global" / "src"
            target.mkdir(parents=True, exist_ok=True)

            (target / "SConstruct").write_text("env={}\npoint=123,\n", encoding="utf-8")
            (target / "VERSION").write_text(
                "ADLMSDK_VERSION_POINT= 123\n", encoding="utf-8"
            )

            update_files(build_num=999, source_path=root)

            self.assertEqual(
                (target / "SConstruct").read_text(encoding="utf-8"),
                "env={}\npoint=999,\n",
            )
            self.assertEqual(
                (target / "VERSION").read_text(encoding="utf-8"),
                "ADLMSDK_VERSION_POINT= 999\n",
            )

    def test_resolve_config_uses_env_vars(self) -> None:
        with TemporaryDirectory() as td:
            old = dict(os.environ)
            try:
                os.environ["BuildNum"] = "12"
                os.environ["SourcePath"] = td
                build_num, source_path = resolve_config()
                self.assertEqual(build_num, 12)
                self.assertEqual(source_path, Path(td))
            finally:
                os.environ.clear()
                os.environ.update(old)

    def test_missing_env_raises(self) -> None:
        old = dict(os.environ)
        try:
            os.environ.pop("BuildNum", None)
            os.environ.pop("SourcePath", None)
            with self.assertRaises(UpdateError):
                resolve_config()
        finally:
            os.environ.clear()
            os.environ.update(old)


if __name__ == "__main__":
    unittest.main()