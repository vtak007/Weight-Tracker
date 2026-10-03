<?php
declare(strict_types=1);
require __DIR__ . '/lib.php';

wt_security_headers();
header('Content-Type: application/json; charset=utf-8');
$cfg = wt_config();

if (!wt_authed($cfg)) {
    http_response_code(401);
    echo '{"error":"auth"}';
    exit;
}

$files = glob(wt_private_dir() . '/weight-tracker-data_*.json') ?: [];
usort($files, fn($a, $b) => filemtime($b) <=> filemtime($a));
if (!$files) {
    http_response_code(404);
    echo '{"error":"no data"}';
    exit;
}
readfile($files[0]);
