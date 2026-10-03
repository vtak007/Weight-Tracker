<?php
declare(strict_types=1);

const WT_COOKIE   = 'wt_auth';
const WT_TTL      = 2592000;   // 30 days
const WT_MAX_FAIL = 5;
const WT_LOCK_SEC = 600;       // 10 minutes

function wt_private_dir(): string {
    $env = getenv('WT_PRIVATE_DIR');
    return ($env !== false && $env !== '') ? $env : dirname(__DIR__, 3) . '/weight-private';
}

function wt_security_headers(): void {
    header('Cache-Control: no-store');
    header('X-Content-Type-Options: nosniff');
    header('X-Robots-Tag: noindex, nofollow');
    header('Referrer-Policy: no-referrer');
}

function wt_config(): array {
    $file = wt_private_dir() . '/auth-config.php';
    $cfg = is_file($file) ? include $file : null;
    if (!is_array($cfg) || !isset($cfg['hash'], $cfg['secret']) || !is_string($cfg['hash'])
        || !is_string($cfg['secret']) || $cfg['secret'] === '') {
        http_response_code(500);
        exit('Server not configured.');
    }
    return $cfg;
}

function wt_token(string $secret, int $expires): string {
    return $expires . '.' . hash_hmac('sha256', (string)$expires, $secret);
}

function wt_token_valid(string $token, string $secret, int $now): bool {
    $parts = explode('.', $token, 2);
    if (count($parts) !== 2 || $parts[0] === '' || !ctype_digit($parts[0]) || $parts[1] === '') {
        return false;
    }
    if ((int)$parts[0] < $now) {
        return false;
    }
    return hash_equals(hash_hmac('sha256', $parts[0], $secret), $parts[1]);
}

function wt_authed(array $cfg): bool {
    return isset($_COOKIE[WT_COOKIE]) && is_string($_COOKIE[WT_COOKIE])
        && wt_token_valid($_COOKIE[WT_COOKIE], $cfg['secret'], time());
}

function wt_cookie_opts(int $expires): array {
    $path = rtrim(dirname($_SERVER['SCRIPT_NAME'] ?? '/'), '/') . '/';
    $https = !empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off';
    return ['expires' => $expires, 'path' => $path, 'secure' => $https,
            'httponly' => true, 'samesite' => 'Strict'];
}

function wt_set_cookie(array $cfg): void {
    $exp = time() + WT_TTL;
    setcookie(WT_COOKIE, wt_token($cfg['secret'], $exp), wt_cookie_opts($exp));
}

function wt_clear_cookie(): void {
    setcookie(WT_COOKIE, '', wt_cookie_opts(1));
}

// ── Login rate limiting (state in the private dir, one JSON file, flock-protected) ──

function wt_attempts(callable $fn) {
    $fh = fopen(wt_private_dir() . '/login-attempts.json', 'c+');
    if ($fh === false) {
        http_response_code(500);
        exit('Server error.');
    }
    flock($fh, LOCK_EX);
    $data = json_decode((string)stream_get_contents($fh), true);
    if (!is_array($data)) $data = [];
    $now = time();
    foreach ($data as $k => $v) {
        if (($v['last'] ?? 0) < $now - 86400) unset($data[$k]);
    }
    $result = $fn($data, $now);
    ftruncate($fh, 0);
    rewind($fh);
    fwrite($fh, json_encode($data));
    fflush($fh);
    flock($fh, LOCK_UN);
    fclose($fh);
    return $result;
}

function wt_client_key(): string {
    return hash('sha256', $_SERVER['REMOTE_ADDR'] ?? 'unknown');
}

function wt_lock_remaining(): int {
    $key = wt_client_key();
    return wt_attempts(function (array &$d, int $now) use ($key): int {
        $until = $d[$key]['locked_until'] ?? 0;
        return $until > $now ? $until - $now : 0;
    });
}

function wt_record_fail(): void {
    $key = wt_client_key();
    wt_attempts(function (array &$d, int $now) use ($key): void {
        $e = $d[$key] ?? ['fails' => 0, 'locked_until' => 0];
        $e['fails']++;
        $e['last'] = $now;
        if ($e['fails'] >= WT_MAX_FAIL) {
            $e['locked_until'] = $now + WT_LOCK_SEC;
            $e['fails'] = 0;
        }
        $d[$key] = $e;
    });
}

function wt_clear_fails(): void {
    $key = wt_client_key();
    wt_attempts(function (array &$d, int $now) use ($key): void {
        unset($d[$key]);
    });
}
