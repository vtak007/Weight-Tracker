#!/usr/bin/env bash
# Local end-to-end test of the login gate. Requires PHP_BIN (php.exe) and python+bcrypt.
set -u
PHP="${PHP_BIN:?set PHP_BIN to the full path of php.exe}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
T="$(mktemp -d)"
mkdir -p "$T/web" "$T/private"
cp "$ROOT"/server/index.php "$ROOT"/server/data.php "$ROOT"/server/lib.php "$T/web/"
cp "$ROOT/weight-tracker.html" "$T/web/app.html"
export WT_PRIVATE_DIR="$(cygpath -m "$T/private")"
export WT_SECRETS_DIR="$WT_PRIVATE_DIR"
PW='test-password-12345'
PW="$PW" ROOT_PY="$(cygpath -m "$ROOT")" python - <<'PY'
import getpass, importlib.util, os, pathlib
getpass.getpass = lambda prompt="": os.environ["PW"]
spec = importlib.util.spec_from_file_location("mac", pathlib.Path(os.environ["ROOT_PY"]) / "deploy" / "make-auth-config.py")
mac = importlib.util.module_from_spec(spec); spec.loader.exec_module(mac); mac.main()
PY
echo '{"entries":[{"date":"2026-02-01","weight":250}],"savedAt":"2026-02-01T00:00:00Z"}' > "$T/private/weight-tracker-data_2026.json"
echo '{"entries":[{"date":"2025-02-01","weight":999}]}' > "$T/private/weight-tracker-data_2025.json"
touch -d '2025-01-01' "$T/private/weight-tracker-data_2025.json"

PORT=8099
"$PHP" -S 127.0.0.1:$PORT -t "$(cygpath -m "$T/web")" >/dev/null 2>&1 &
SRV=$!
trap 'kill $SRV 2>/dev/null; rm -rf "$T"' EXIT
curl -s --retry 15 --retry-connrefused --retry-delay 1 -o /dev/null "http://127.0.0.1:$PORT/data.php"

fail=0
check() { if [ "$2" = "$3" ]; then echo "PASS $1"; else echo "FAIL $1 (got '$2', want '$3')"; fail=1; fi; }
B="http://127.0.0.1:$PORT"
code() { curl -s -o /dev/null -w '%{http_code}' "$@"; }

check "data.php without cookie -> 401" "$(code $B/data.php)" 401
check "login page is served" "$(curl -s $B/index.php | grep -c 'type="password"')" 1
check "tampered cookie -> 401" "$(code -H 'Cookie: wt_auth=9999999999.deadbeef' $B/data.php)" 401
check "malformed cookie -> 401" "$(code -H 'Cookie: wt_auth=garbage' $B/data.php)" 401
check "no-store header on data.php" "$(curl -si $B/data.php | grep -ci '^cache-control: no-store')" 1
check "noindex header on login" "$(curl -si $B/index.php | grep -ci '^x-robots-tag: noindex')" 1

check "wrong password -> 401" "$(code -d 'password=nope' $B/index.php)" 401
check "wrong password sets no cookie" "$(curl -si -d 'password=nope' $B/index.php | grep -ci 'set-cookie: wt_auth')" 0

JAR="$T/jar"
check "right password -> 302" "$(code -c $JAR -d "password=$PW" $B/index.php)" 302
check "cookie flags HttpOnly+SameSite" "$(curl -si -d "password=$PW" $B/index.php | grep -i 'set-cookie: wt_auth' | grep -ci 'httponly.*samesite=strict\|samesite=strict.*httponly')" 1
check "data.php with cookie -> 200" "$(code -b $JAR $B/data.php)" 200
check "serves newest data file" "$(curl -s -b $JAR $B/data.php | python -c 'import json,sys;print(json.load(sys.stdin)["entries"][0]["weight"])')" 250
check "index.php with cookie serves app" "$(curl -s -b $JAR $B/index.php | grep -c '<h1>Weight & Food Tracker</h1>')" 1
check "logout clears cookie" "$(curl -si -b $JAR "$B/index.php?logout=1" | grep -ci 'set-cookie: wt_auth=deleted\|set-cookie: wt_auth=;')" 1

rm "$T"/private/weight-tracker-data_*.json
check "no data file -> 404 json" "$(curl -s -b $JAR -o /dev/null -w '%{http_code}' $B/data.php)" 404
check "404 body is json" "$(curl -s -b $JAR $B/data.php)" '{"error":"no data"}'

# Lockout last: 5 wrong passwords, then even the right one is refused.
for i in 1 2 3 4 5; do code -d 'password=nope' $B/index.php >/dev/null; done
check "6th attempt (wrong) -> 429" "$(code -d 'password=nope' $B/index.php)" 429
check "right password during lockout -> 429" "$(code -d "password=$PW" $B/index.php)" 429

exit $fail
