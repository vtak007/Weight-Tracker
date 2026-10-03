"""Create auth-config.php (bcrypt hash + random cookie secret) for the Weight Tracker phone site.

The password is typed here (hidden) and never stored; only its hash is written. Output goes to
%USERPROFILE%\\weight-tracker-secrets\\auth-config.php (or $WT_SECRETS_DIR), outside the repo and
outside Dropbox. Upload that one file to /weight-private/ on NFO.
"""
import getpass
import os
import pathlib
import secrets
import sys

import bcrypt


def build_config_php(password: str) -> str:
    h = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(12)).decode("ascii")
    h = h.replace("$2b$", "$2y$", 1)  # PHP's password_verify accepts $2y$
    secret = secrets.token_hex(32)
    # bcrypt output uses only [./A-Za-z0-9$], so single-quoted PHP strings need no escaping.
    return "<?php\nreturn [\n    'hash' => '%s',\n    'secret' => '%s',\n];\n" % (h, secret)


def secrets_dir() -> pathlib.Path:
    env = os.environ.get("WT_SECRETS_DIR")
    if env:
        return pathlib.Path(env)
    return pathlib.Path(os.environ["USERPROFILE"]) / "weight-tracker-secrets"


def main() -> None:
    pw = getpass.getpass("New password (12-72 bytes): ")
    pw2 = getpass.getpass("Repeat password: ")
    if pw != pw2:
        sys.exit("Passwords do not match.")
    size = len(pw.encode("utf-8"))
    if size < 12 or size > 72:
        sys.exit("Password must be 12-72 bytes.")
    out = secrets_dir()
    out.mkdir(parents=True, exist_ok=True)
    target = out / "auth-config.php"
    target.write_text(build_config_php(pw), encoding="utf-8", newline="\n")
    print("Wrote", target)
    print("Upload it to /weight-private/ on NFO. Do not commit or share it.")


if __name__ == "__main__":
    main()
