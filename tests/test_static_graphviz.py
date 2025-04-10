import os
import shutil
import subprocess
import unittest
from pathlib import Path

from static_graphviz import add_paths


class StaticGraphvizTester(unittest.TestCase):

    def test_basic(self) -> None:
        installed = add_paths()

        ld_path = os.environ.get("LD_LIBRARY_PATH", "")
        print(f"LD_LIBRARY_PATH={ld_path}")
        self.assertTrue(installed, "Failed to add paths")

        dot = shutil.which("dot")
        self.assertIsNotNone(dot, "Failed to find dot in PATH")

        assert isinstance(dot, str)

        result = subprocess.run([dot, "-V"], capture_output=True, text=True, check=True)
        assert isinstance(result.stdout, str)
        assert isinstance(result.stderr, str)
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        output = stdout + "\n" + stderr
        self.assertIn(
            "graphviz version", output, "dot -V did not return expected output"
        )
        print(f"dot -V output: {output}")

    def test_install_dot(self) -> None:
        installed = add_paths()
        ld_path = os.environ.get("LD_LIBRARY_PATH", "")
        print(f"LD_LIBRARY_PATH={ld_path}")
        self.assertTrue(installed, "Failed to add paths")

        rtn = os.system("dot -V")
        self.assertEqual(rtn, 0, "dot -V failed")

    def test_plugin_registry_missing(self) -> None:
        installed = add_paths()
        self.assertTrue(installed, "Failed to add paths")

        dot = shutil.which("dot")
        self.assertIsNotNone(dot, "Failed to find dot in PATH")

        env = os.environ.copy()
        env["GV_PLUGIN_PATH"] = "/nonexistent"  # force plugin discovery to fail
        assert dot is not None
        subprocess.run(
            [dot, "-Tsvg", "-Kneato", "-Grankdir=LR"],
            input="digraph { A -> B }",
            capture_output=True,
            text=True,
            check=True,
            env=env,
        )

    @unittest.skipIf(os.name != "posix", "Only run on Linux")
    def test_plugin_shared_libraries(self) -> None:
        """Run ldd on every libgvplugin_*.so file and print any missing dependencies."""
        installed = add_paths()
        self.assertTrue(installed, "Failed to add paths")

        dot = shutil.which("dot")
        self.assertIsNotNone(dot, "dot not found in PATH")
        assert dot is not None
        dot_path = Path(dot).resolve()
        plugin_dir = dot_path.parent / "graphviz"

        if not plugin_dir.exists():
            self.skipTest(f"Plugin directory {plugin_dir} does not exist")

        so_files = list(plugin_dir.glob("libgvplugin_*.so.*"))
        self.assertGreater(len(so_files), 0, "No plugin .so files found")

        any_missing = False

        for so_file in so_files:
            print(f"\n🔍 ldd output for: {so_file}")
            result = subprocess.run(
                ["ldd", str(so_file)], capture_output=True, text=True
            )
            output = result.stdout.strip()
            print(output)

            # Find missing lines
            missing_lines = [
                line for line in output.splitlines() if "not found" in line
            ]
            if missing_lines:
                any_missing = True
                print(f"\n❌ Missing dependencies in {so_file.name}:")
                for line in missing_lines:
                    print(f"   🚫 {line}")

        if any_missing:
            self.fail(
                "One or more plugin .so files have missing shared library dependencies."
            )


if __name__ == "__main__":
    unittest.main()
