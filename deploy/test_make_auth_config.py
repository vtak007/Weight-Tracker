import importlib.util, os, pathlib, re, tempfile, unittest
from unittest import mock

import bcrypt

HERE = pathlib.Path(__file__).parent
spec = importlib.util.spec_from_file_location("mac", HERE / "make-auth-config.py")
mac = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mac)


class BuildConfig(unittest.TestCase):
    def test_hash_is_php_compatible_and_verifies(self):
        php = mac.build_config_php("correct horse battery")
        m = re.search(r"'hash' => '(\$2y\$12\$[./A-Za-z0-9]{53})'", php)
        self.assertIsNotNone(m, php)
        self.assertTrue(bcrypt.checkpw(b"correct horse battery", m.group(1).encode()))
        self.assertFalse(bcrypt.checkpw(b"wrong", m.group(1).encode()))

    def test_secret_is_64_hex_and_random(self):
        a = re.search(r"'secret' => '([0-9a-f]{64})'", mac.build_config_php("x" * 12))
        b = re.search(r"'secret' => '([0-9a-f]{64})'", mac.build_config_php("x" * 12))
        self.assertTrue(a and b)
        self.assertNotEqual(a.group(1), b.group(1))

    def test_password_not_present_in_output(self):
        self.assertNotIn("correct horse battery", mac.build_config_php("correct horse battery"))


class Main(unittest.TestCase):
    def run_main(self, answers):
        with tempfile.TemporaryDirectory() as d, \
             mock.patch.dict(os.environ, {"WT_SECRETS_DIR": d}), \
             mock.patch("getpass.getpass", side_effect=answers):
            try:
                mac.main()
                return (pathlib.Path(d) / "auth-config.php").exists()
            except SystemExit:
                return False

    def test_writes_file_when_passwords_match(self):
        self.assertTrue(self.run_main(["a-long-password-1", "a-long-password-1"]))

    def test_rejects_mismatch(self):
        self.assertFalse(self.run_main(["a-long-password-1", "a-long-password-2"]))

    def test_rejects_short(self):
        self.assertFalse(self.run_main(["short", "short"]))

    def test_rejects_over_72_bytes(self):
        self.assertFalse(self.run_main(["x" * 73, "x" * 73]))


if __name__ == "__main__":
    unittest.main()
