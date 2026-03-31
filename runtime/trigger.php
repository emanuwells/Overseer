<?php
/**
 * Overseer Trigger Receiver — PHP endpoint that writes trigger JSON files.
 * Deployed on nginx server, accessed by the frontend to submit "Run now" and
 * schedule change triggers. The scheduler daemon polls the triggers/ directory
 * via SSH/SFTP to pick up and execute pending triggers.
 *
 * URL: http://baze2.cm-maia.pt/MAIATRON/apps/overseer/trigger.php
 * Method: POST with JSON body
 */

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

// Handle CORS preflight
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(204);
    exit;
}

// Health check
if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    $dir = __DIR__ . '/triggers';
    $files = is_dir($dir) ? array_values(array_diff(scandir($dir), ['.', '..'])) : [];
    echo json_encode(['status' => 'alive', 'pending' => count($files)]);
    exit;
}

// Only POST allowed
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['status' => 'error', 'message' => 'Only POST allowed']);
    exit;
}

$input = file_get_contents('php://input');
$data = json_decode($input, true);

if (!$data || (!isset($data['pipeline_id']) && !isset($data['type']))) {
    http_response_code(400);
    echo json_encode(['status' => 'error', 'message' => 'Invalid JSON or missing pipeline_id']);
    exit;
}

$dir = __DIR__ . '/triggers';
if (!is_dir($dir)) {
    mkdir($dir, 0775, true);
}

$filename = 'trigger-' . time() . '-' . substr(md5(uniqid('', true)), 0, 8) . '.json';
$filepath = $dir . '/' . $filename;

$result = file_put_contents($filepath, $input);
if ($result === false) {
    http_response_code(500);
    echo json_encode(['status' => 'error', 'message' => 'Failed to write trigger file']);
    exit;
}

echo json_encode(['status' => 'ok', 'file' => $filename]);
