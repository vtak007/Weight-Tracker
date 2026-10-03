<?php
declare(strict_types=1);
require __DIR__ . '/../../server/lib.php';

$fail = 0;
function check(string $name, bool $ok): void {
    global $fail;
    echo ($ok ? "PASS " : "FAIL ") . $name . "\n";
    if (!$ok) $fail = 1;
}

$secret = str_repeat('a', 64);
$now = 1_000_000;
$good = wt_token($secret, $now + 100);

check('valid token accepted', wt_token_valid($good, $secret, $now));
check('expired token rejected', !wt_token_valid(wt_token($secret, $now - 1), $secret, $now));
check('tampered expiry rejected', !wt_token_valid(($now + 99999) . '.' . explode('.', $good)[1], $secret, $now));
check('tampered mac rejected', !wt_token_valid($now + 100 . '.' . str_repeat('0', 64), $secret, $now));
check('wrong secret rejected', !wt_token_valid($good, str_repeat('b', 64), $now));
foreach (['', '.', 'abc', '123', '123.', '.abc', 'x.y', '123.abc.def', "12\x003.abc"] as $bad) {
    check('malformed rejected: ' . json_encode($bad), !wt_token_valid($bad, $secret, $now));
}
exit($fail);
