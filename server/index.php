<?php
declare(strict_types=1);
require __DIR__ . '/lib.php';

wt_security_headers();
$cfg = wt_config();

if (isset($_GET['logout'])) {
    wt_clear_cookie();
    header('Location: index.php');
    exit;
}

$error = '';
if ($_SERVER['REQUEST_METHOD'] === 'POST' && !wt_authed($cfg)) {
    $wait = wt_lock_remaining();
    if ($wait > 0) {
        http_response_code(429);
        $error = 'Too many attempts. Try again in ' . (int)ceil($wait / 60) . ' min.';
    } else {
        $pw = (string)($_POST['password'] ?? '');
        if (strlen($pw) <= 1024 && password_verify($pw, $cfg['hash'])) {
            wt_clear_fails();
            wt_set_cookie($cfg);
            header('Location: index.php');
            exit;
        }
        wt_record_fail();
        sleep(1);
        http_response_code(401);
        $error = 'Wrong password.';
    }
}

header('Content-Type: text/html; charset=utf-8');

if (wt_authed($cfg)) {
    readfile(__DIR__ . '/app.html');
    exit;
}
?>
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Weight Tracker</title>
<style>
  body { margin: 0; min-height: 100vh; display: flex; align-items: center; justify-content: center;
         background: #0f172a; color: #e2e8f0; font-family: system-ui, sans-serif; }
  form { width: min(320px, 90vw); background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 24px; }
  h1 { font-size: 1.2rem; margin: 0 0 16px; }
  input, button { width: 100%; box-sizing: border-box; font-size: 1rem; padding: 10px; border-radius: 6px; border: 1px solid #334155; }
  input { background: #0f172a; color: #e2e8f0; margin-bottom: 12px; }
  button { background: #0284c7; color: #fff; border: 0; cursor: pointer; }
  .err { color: #f87171; font-size: 0.9rem; margin-bottom: 12px; }
</style>
</head>
<body>
<form method="post" action="index.php">
  <h1>Weight Tracker</h1>
  <?php if ($error !== ''): ?><div class="err"><?= htmlspecialchars($error, ENT_QUOTES, 'UTF-8') ?></div><?php endif; ?>
  <input type="password" name="password" autocomplete="current-password" autofocus required placeholder="Password">
  <button type="submit">Sign in</button>
</form>
</body>
</html>
