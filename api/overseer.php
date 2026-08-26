<?php
declare(strict_types=1);

require_once __DIR__ . '/_overseer_runtime.php';

/**
 * Read-only Overseer monitoring summary for external dashboards.
 * Does not expose credentials, DB hosts, or internal paths.
 */

$apiCfg = wells_api_api_config('overseer');
$allowedOrigins = wells_api_config_value($apiCfg, 'cors.allowed_origins', ['*']);
if (!is_array($allowedOrigins)) {
    $allowedOrigins = ['*'];
}
wells_api_apply_cors($allowedOrigins, ['GET', 'OPTIONS']);

$method = strtoupper((string)($_SERVER['REQUEST_METHOD'] ?? 'GET'));
if ($method === 'OPTIONS') {
    http_response_code(204);
    exit;
}
if ($method !== 'GET') {
    wells_api_send_json_error(405, 'Método não permitido.');
}

function overseer_public_url(): string
{
    $host = $_SERVER['HTTP_HOST'] ?? null;
    $path = trim((string)($_SERVER['SCRIPT_NAME'] ?? ''));
    if (is_string($host) && $host !== '' && $path !== '') {
        $scheme = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') ? 'https' : 'http';
        return $scheme . '://' . $host . $path;
    }

    return $path !== '' ? $path : '/api/overseer.php';
}

function overseer_build_help_response(): array
{
    $baseUrl = overseer_public_url();

    return [
        'api' => 'Overseer',
        'version' => wells_api_env('WELLS_API_VERSION', WELLS_API_VERSION),
        'summary' => 'Proxy read-only para resumo Overseer, runs por pipeline e detalhe/logs de uma run.',
        'self' => $baseUrl . '?help=1',
        'parameters' => [
            ['group' => 'Geral', 'name' => 'help', 'values' => '1', 'description' => 'Este guia — não consulta a API Overseer.'],
            ['group' => 'Filtros', 'name' => 'pipeline_id', 'values' => 'id', 'description' => 'Lista runs recentes desse pipeline.'],
            ['group' => 'Filtros', 'name' => 'host_id', 'values' => 'id', 'description' => 'Opcional com pipeline_id.'],
            ['group' => 'Filtros', 'name' => 'run_id', 'values' => 'id', 'description' => 'Detalhe da run + módulos + logs.'],
            ['group' => 'Filtros', 'name' => 'limit', 'values' => '1-100', 'description' => 'Máximo de runs (default 40).'],
            ['group' => 'Filtros', 'name' => 'window', 'values' => '1h|24h|7d|all', 'description' => 'Janela para window_stats e filtro de runs.'],
            ['group' => 'Filtros', 'name' => 'since', 'values' => 'ISO-8601', 'description' => 'Início explícito (alternativa a window).'],
        ],
        'examples' => [
            ['label' => 'Resumo', 'url' => $baseUrl],
            ['label' => 'Runs 24h', 'url' => $baseUrl . '?window=24h&limit=100'],
            ['label' => 'Runs do pipeline', 'url' => $baseUrl . '?pipeline_id=traffic_flow'],
            ['label' => 'Detalhe + logs', 'url' => $baseUrl . '?run_id=run-…'],
        ],
        'limits' => [
            'Apenas GET.',
            'Depende de OVERSEER_API_URL e OVERSEER_API_TOKEN no ambiente.',
            'Logs sanitizados: sem metadata interna nem caminhos sensíveis.',
        ],
    ];
}

$helpRaw = filter_input(INPUT_GET, 'help', FILTER_UNSAFE_RAW);
if (in_array(strtolower((string)($helpRaw ?? '')), ['1', 'true', 'yes'], true)) {
    wells_api_send_json(overseer_build_help_response());
}

$baseUrl = rtrim((string)wells_api_config_value($apiCfg, 'api_url', wells_api_env('OVERSEER_API_URL', 'http://127.0.0.1:8090')), '/');
$tokenEnv = (string)wells_api_config_value($apiCfg, 'service_token_env', 'OVERSEER_API_TOKEN');
$token = trim((string)wells_api_env($tokenEnv, ''));

/**
 * @return string|null
 */
function wells_overseer_valid_id($value)
{
    if (!is_string($value)) {
        return null;
    }
    $value = trim($value);
    if ($value === '' || strlen($value) > 128) {
        return null;
    }
    if (!preg_match('/^[A-Za-z0-9_.:-]+$/', $value)) {
        return null;
    }

    return $value;
}

function overseer_upstream_host(string $apiUrl): string
{
    $parts = parse_url($apiUrl);
    if (!is_array($parts)) {
        return '';
    }
    $host = (string)($parts['host'] ?? '');
    if ($host === '') {
        return '';
    }
    $port = isset($parts['port']) ? (int)$parts['port'] : null;
    if ($port !== null && $port > 0) {
        return $host . ':' . $port;
    }

    return $host;
}

/**
 * @return string|null
 */
function wells_overseer_parse_window($raw)
{
    $value = strtolower(trim((string)$raw));
    if (in_array($value, ['1h', '24h', '7d', 'all'], true)) {
        return $value;
    }

    return null;
}

/**
 * @return string|null ISO UTC
 */
function wells_overseer_since_for_window($window)
{
    if ($window === null || $window === 'all') {
        return null;
    }
    $seconds = 86400;
    if ($window === '1h') {
        $seconds = 3600;
    } elseif ($window === '7d') {
        $seconds = 7 * 86400;
    }

    return gmdate('c', time() - $seconds);
}

/**
 * @param mixed $value
 */
function wells_overseer_run_time_ms($value): ?int
{
    if (is_int($value) || is_float($value)) {
        $n = (float)$value;
        if ($n <= 0) {
            return null;
        }

        return (int)($n < 1000000000000 ? $n * 1000 : $n);
    }
    if (!is_string($value) || trim($value) === '') {
        return null;
    }
    $ts = strtotime($value);
    if ($ts === false) {
        return null;
    }

    return $ts * 1000;
}

/**
 * @param list $runs
 * @return array{total:int,ok:int,failed:int}
 */
function wells_overseer_count_run_statuses(array $runs): array
{
    $ok = 0;
    $failed = 0;
    foreach ($runs as $run) {
        if (!is_array($run)) {
            continue;
        }
        $status = strtolower((string)($run['status'] ?? $run['result'] ?? ''));
        if ($status === '') {
            continue;
        }
        if (strpos($status, 'fail') !== false || strpos($status, 'error') !== false || strpos($status, 'nok') !== false || strpos($status, 'crash') !== false) {
            $failed++;
        } elseif (strpos($status, 'ok') !== false || strpos($status, 'success') !== false || strpos($status, 'complet') !== false) {
            $ok++;
        }
    }

    return ['total' => count($runs), 'ok' => $ok, 'failed' => $failed];
}

/**
 * @param list $runs
 * @return list
 */
function wells_overseer_filter_runs_since(array $runs, $sinceIso)
{
    if ($sinceIso === null || $sinceIso === '') {
        return $runs;
    }
    $cutoff = wells_overseer_run_time_ms($sinceIso);
    if ($cutoff === null) {
        return $runs;
    }
    $out = [];
    foreach ($runs as $run) {
        if (!is_array($run)) {
            continue;
        }
        $t = wells_overseer_run_time_ms($run['started_at'] ?? null);
        if ($t === null) {
            $t = wells_overseer_run_time_ms($run['ended_at'] ?? null);
        }
        if ($t === null || $t < $cutoff) {
            continue;
        }
        $out[] = $run;
    }

    return $out;
}

/**
 * @param array $payload
 */
function wells_overseer_payload_total(array $payload): ?int
{
    foreach (['total', 'total_count', 'count', 'totalRuns', 'total_runs'] as $key) {
        if (isset($payload[$key]) && is_numeric($payload[$key])) {
            return max(0, (int)$payload[$key]);
        }
    }
    if (isset($payload['meta']) && is_array($payload['meta'])) {
        foreach (['total', 'total_count', 'count'] as $key) {
            if (isset($payload['meta'][$key]) && is_numeric($payload['meta'][$key])) {
                return max(0, (int)$payload['meta'][$key]);
            }
        }
    }
    if (isset($payload['pagination']) && is_array($payload['pagination'])) {
        foreach (['total', 'total_count', 'count'] as $key) {
            if (isset($payload['pagination'][$key]) && is_numeric($payload['pagination'][$key])) {
                return max(0, (int)$payload['pagination'][$key]);
            }
        }
    }

    return null;
}

/**
 * Busca runs com filtro temporal upstream (tenta since / started_after / from).
 * `$scanLimit` (até 1000) serve para contagens; `$displayLimit` corta a amostra da UI.
 *
 * @return array{payload: array, items: list, scanned: list, date_param: string|null, scan_limit: int}
 */
function wells_overseer_fetch_runs_window(string $baseUrl, string $token, int $displayLimit, $sinceIso, $pipelineId, $hostId, int $scanLimit = 1000): array
{
    $displayLimit = max(1, min($displayLimit, 100));
    $scanLimit = max($displayLimit, min($scanLimit, 1000));
    $baseQuery = 'limit=' . (int)$scanLimit;
    if (is_string($pipelineId) && $pipelineId !== '') {
        $baseQuery .= '&pipeline_id=' . rawurlencode($pipelineId);
    }
    if (is_string($hostId) && $hostId !== '') {
        $baseQuery .= '&host_id=' . rawurlencode($hostId);
    }

    $baseline = wells_overseer_fetch($baseUrl, '/v1/read/runs?' . $baseQuery, $token);
    $baselineItems = wells_overseer_public_runs($baseline['items'] ?? null, $scanLimit);
    $chosenPayload = $baseline;
    $chosenItems = $baselineItems;
    $dateParam = null;

    if ($sinceIso !== null && $sinceIso !== '') {
        foreach (['since', 'started_after', 'from'] as $param) {
            $payload = wells_overseer_fetch(
                $baseUrl,
                '/v1/read/runs?' . $baseQuery . '&' . $param . '=' . rawurlencode($sinceIso),
                $token
            );
            if (!($payload['ok'] ?? true) && isset($payload['error'])) {
                continue;
            }
            if (isset($payload['detail']) && !isset($payload['items'])) {
                continue;
            }
            $items = wells_overseer_public_runs($payload['items'] ?? null, $scanLimit);
            if (!is_array($payload['items'] ?? null) && count($items) === 0) {
                continue;
            }
            $filtered = wells_overseer_filter_runs_since($items, $sinceIso);
            // Preferir o primeiro parâmetro aceite que devolve items.
            $chosenPayload = $payload;
            $chosenItems = $filtered;
            $dateParam = $param;
            break;
        }
        if ($dateParam === null) {
            $chosenItems = wells_overseer_filter_runs_since($baselineItems, $sinceIso);
        }
    }

    $displayItems = array_slice($chosenItems, 0, $displayLimit);

    return [
        'payload' => $chosenPayload,
        'items' => $displayItems,
        'scanned' => $chosenItems,
        'date_param' => $dateParam,
        'scan_limit' => $scanLimit,
        'raw_count' => is_array($chosenPayload['items'] ?? null) ? count($chosenPayload['items']) : count($chosenItems),
    ];
}

/**
 * Scan completo se a página não encheu o teto ou o item mais antigo já saiu da janela.
 *
 * @param list $rawItems
 */
function wells_overseer_scan_complete(array $rawItems, $sinceIso, int $scanLimit): bool
{
    if (count($rawItems) < $scanLimit) {
        return true;
    }
    if ($sinceIso === null || $sinceIso === '') {
        return false;
    }
    $cutoff = wells_overseer_run_time_ms($sinceIso);
    if ($cutoff === null || count($rawItems) === 0) {
        return false;
    }
    $oldest = $rawItems[count($rawItems) - 1];
    $t = wells_overseer_run_time_ms(is_array($oldest) ? ($oldest['started_at'] ?? $oldest['ended_at'] ?? null) : null);

    return $t !== null && $t < $cutoff;
}

/**
 * Conta runs dum pipeline na janela; se necessário, fatia por dia (tetos 1000 do upstream).
 *
 * @return array{total:int,ok:int,failed:int,exact:bool}
 */
function wells_overseer_count_pipeline_days(string $baseUrl, string $token, $pipelineId, $hostId, $sinceIso, $dateParam, int $days): array
{
    $dateParam = is_string($dateParam) && $dateParam !== '' ? $dateParam : 'since';
    $total = 0;
    $ok = 0;
    $failed = 0;
    $exact = true;
    $now = time();

    for ($i = 0; $i < $days; $i++) {
        $endTs = $now - ($i * 86400);
        $startTs = $now - (($i + 1) * 86400);
        $startIso = gmdate('c', $startTs);
        $query = 'limit=1000&' . $dateParam . '=' . rawurlencode($startIso);
        if (is_string($pipelineId) && $pipelineId !== '') {
            $query .= '&pipeline_id=' . rawurlencode($pipelineId);
        }
        if (is_string($hostId) && $hostId !== '') {
            $query .= '&host_id=' . rawurlencode($hostId);
        }
        $payload = wells_overseer_fetch($baseUrl, '/v1/read/runs?' . $query, $token);
        $raw = wells_overseer_public_runs($payload['items'] ?? null, 1000);
        if (count($raw) >= 1000) {
            $oldest = $raw[count($raw) - 1];
            $oldestMs = wells_overseer_run_time_ms($oldest['started_at'] ?? $oldest['ended_at'] ?? null);
            if ($oldestMs === null || $oldestMs >= ($startTs * 1000)) {
                $exact = false;
            }
        }
        foreach ($raw as $run) {
            if (!is_array($run)) {
                continue;
            }
            $t = wells_overseer_run_time_ms($run['started_at'] ?? null);
            if ($t === null) {
                $t = wells_overseer_run_time_ms($run['ended_at'] ?? null);
            }
            if ($t === null || $t < ($startTs * 1000) || $t >= ($endTs * 1000)) {
                continue;
            }
            $total++;
            $status = strtolower((string)($run['status'] ?? $run['result'] ?? ''));
            if ($status === '') {
                continue;
            }
            if (strpos($status, 'fail') !== false || strpos($status, 'error') !== false || strpos($status, 'nok') !== false || strpos($status, 'crash') !== false) {
                $failed++;
            } elseif (strpos($status, 'ok') !== false || strpos($status, 'success') !== false || strpos($status, 'complet') !== false) {
                $ok++;
            }
        }
    }

    return ['total' => $total, 'ok' => $ok, 'failed' => $failed, 'exact' => $exact];
}

/**
 * Contagem exacta 7d: por pipeline (e fatias diárias só quando o teto 1000 é atingido).
 *
 * @param list $pipelines
 * @return array{total:int,ok:int,failed:int,exact:bool}
 */
function wells_overseer_count_window_by_pipelines(string $baseUrl, string $token, array $pipelines, $sinceIso, $dateParam): array
{
    $dateParam = is_string($dateParam) && $dateParam !== '' ? $dateParam : 'since';
    $total = 0;
    $ok = 0;
    $failed = 0;
    $exact = true;

    foreach ($pipelines as $pipeline) {
        if (!is_array($pipeline)) {
            continue;
        }
        $pid = is_string($pipeline['pipeline_id'] ?? null) ? $pipeline['pipeline_id'] : null;
        $hid = is_string($pipeline['host_id'] ?? null) ? $pipeline['host_id'] : null;
        if ($pid === null || $pid === '') {
            continue;
        }
        $query = 'limit=1000&' . $dateParam . '=' . rawurlencode((string)$sinceIso);
        $query .= '&pipeline_id=' . rawurlencode($pid);
        if ($hid !== null && $hid !== '') {
            $query .= '&host_id=' . rawurlencode($hid);
        }
        $payload = wells_overseer_fetch($baseUrl, '/v1/read/runs?' . $query, $token);
        $raw = wells_overseer_public_runs($payload['items'] ?? null, 1000);
        $filtered = wells_overseer_filter_runs_since($raw, $sinceIso);
        if (!wells_overseer_scan_complete($raw, $sinceIso, 1000)) {
            $dayStats = wells_overseer_count_pipeline_days($baseUrl, $token, $pid, $hid, $sinceIso, $dateParam, 7);
            $total += $dayStats['total'];
            $ok += $dayStats['ok'];
            $failed += $dayStats['failed'];
            if (!$dayStats['exact']) {
                $exact = false;
            }
            continue;
        }
        $counts = wells_overseer_count_run_statuses($filtered);
        $total += $counts['total'];
        $ok += $counts['ok'];
        $failed += $counts['failed'];
    }

    return ['total' => $total, 'ok' => $ok, 'failed' => $failed, 'exact' => $exact];
}

/**
 * Cache curto em ficheiro para contagens caras (7d).
 *
 * @return array|null
 */
function wells_overseer_stats_cache_get($key, $ttlSeconds = 45)
{
    $path = rtrim(sys_get_temp_dir(), DIRECTORY_SEPARATOR) . DIRECTORY_SEPARATOR . 'wells_ov_ws_' . sha1((string)$key) . '.json';
    if (!is_file($path)) {
        return null;
    }
    if ((time() - (int)filemtime($path)) > $ttlSeconds) {
        return null;
    }
    $raw = @file_get_contents($path);
    if (!is_string($raw) || $raw === '') {
        return null;
    }
    $decoded = json_decode($raw, true);

    return is_array($decoded) ? $decoded : null;
}

/**
 * @param array $stats
 */
function wells_overseer_stats_cache_set($key, array $stats)
{
    $path = rtrim(sys_get_temp_dir(), DIRECTORY_SEPARATOR) . DIRECTORY_SEPARATOR . 'wells_ov_ws_' . sha1((string)$key) . '.json';
    @file_put_contents($path, json_encode($stats), LOCK_EX);
}

function wells_overseer_fetch(string $baseUrl, string $path, string $token): array
{
    $url = $baseUrl . $path;
    $headers = "Accept: application/json\r\n";
    if ($token !== '') {
        $headers .= 'Authorization: Bearer ' . $token . "\r\n";
    }
    $ctx = stream_context_create([
        'http' => [
            'method' => 'GET',
            'header' => $headers,
            'timeout' => 15,
            'ignore_errors' => true,
        ],
    ]);
    $raw = @file_get_contents($url, false, $ctx);
    if (!is_string($raw) || trim($raw) === '') {
        return ['ok' => false, 'error' => 'Overseer API unreachable'];
    }
    $decoded = json_decode($raw, true);
    if (!is_array($decoded)) {
        return ['ok' => false, 'error' => 'Invalid JSON'];
    }
    if (isset($decoded['detail']) && !isset($decoded['ok'])) {
        $detail = $decoded['detail'];
        $message = is_string($detail) ? $detail : 'Overseer API error';
        return ['ok' => false, 'error' => $message];
    }

    return $decoded;
}

/**
 * @param array $source
 * @param array $keys
 * @return mixed
 */
function wells_overseer_pick(array $source, array $keys)
{
    foreach ($keys as $key) {
        if (array_key_exists($key, $source)) {
            return $source[$key];
        }
    }

    return null;
}

/**
 * @param mixed $rows
 * @return list
 */
function wells_overseer_public_pipelines($rows): array
{
    if (!is_array($rows)) {
        return [];
    }
    $out = [];
    foreach (array_slice($rows, 0, 120) as $row) {
        if (!is_array($row)) {
            continue;
        }
        $pipelineId = wells_overseer_pick($row, ['pipeline_id', 'pipelineId']);
        if (!is_string($pipelineId) || trim($pipelineId) === '') {
            continue;
        }
        $out[] = [
            'pipeline_id' => $pipelineId,
            'host_id' => wells_overseer_pick($row, ['host_id', 'hostId']),
            'name' => wells_overseer_pick($row, ['name', 'pipeline_name', 'pipelineName']) ?? $pipelineId,
            'owner' => wells_overseer_pick($row, ['owner']),
            'schedule' => wells_overseer_pick($row, ['schedule']),
            'criticality' => wells_overseer_pick($row, ['criticality']),
            'active' => (bool)($row['active'] ?? true),
            'last_status' => wells_overseer_pick($row, ['last_status', 'lastStatus', 'status']),
            'last_ended_at' => wells_overseer_pick($row, ['last_ended_at', 'lastEndedAt', 'ended_at', 'endedAt']),
        ];
    }

    return $out;
}

/**
 * @param mixed $rows
 * @param int $max
 * @return list
 */
function wells_overseer_public_runs($rows, $max = 40): array
{
    if (!is_array($rows)) {
        return [];
    }
    $out = [];
    foreach (array_slice($rows, 0, max(1, (int)$max)) as $row) {
        if (!is_array($row)) {
            continue;
        }
        $runId = wells_overseer_pick($row, ['run_id', 'runId', 'id']);
        if (!is_string($runId) && !is_int($runId)) {
            continue;
        }
        $out[] = [
            'run_id' => (string)$runId,
            'pipeline_id' => wells_overseer_pick($row, ['pipeline_id', 'pipelineId']),
            'pipeline_name' => wells_overseer_pick($row, ['pipeline_name', 'pipelineName', 'name']),
            'host_id' => wells_overseer_pick($row, ['host_id', 'hostId']),
            'status' => wells_overseer_pick($row, ['status', 'result']),
            'started_at' => wells_overseer_pick($row, ['started_at', 'startedAt', 'created_at']),
            'ended_at' => wells_overseer_pick($row, ['ended_at', 'endedAt']),
            'duration_sec' => wells_overseer_pick($row, ['duration_sec', 'durationSec', 'duration_ms']),
        ];
    }

    return $out;
}

/**
 * @param mixed $rows
 * @return list
 */
function wells_overseer_public_modules($rows): array
{
    if (!is_array($rows)) {
        return [];
    }
    $out = [];
    foreach (array_slice($rows, 0, 80) as $row) {
        if (!is_array($row)) {
            continue;
        }
        $out[] = [
            'module_id' => wells_overseer_pick($row, ['module_id', 'moduleId', 'id']),
            'name' => wells_overseer_pick($row, ['name', 'module_name', 'moduleName']),
            'status' => wells_overseer_pick($row, ['status', 'result']),
            'started_at' => wells_overseer_pick($row, ['started_at', 'startedAt']),
            'ended_at' => wells_overseer_pick($row, ['ended_at', 'endedAt']),
            'duration_sec' => wells_overseer_pick($row, ['duration_sec', 'durationSec']),
            'error_message' => wells_overseer_pick($row, ['error_message', 'errorMessage']),
        ];
    }

    return $out;
}

/**
 * @param mixed $rows
 * @return list
 */
function wells_overseer_public_logs($rows): array
{
    if (!is_array($rows)) {
        return [];
    }
    $out = [];
    foreach (array_slice($rows, 0, 200) as $row) {
        if (!is_array($row)) {
            continue;
        }
        $message = wells_overseer_pick($row, ['message']);
        if (!is_string($message)) {
            $message = '';
        }
        if (strlen($message) > 4000) {
            $message = substr($message, 0, 4000) . '…';
        }
        $out[] = [
            'log_id' => wells_overseer_pick($row, ['log_id', 'logId', 'id']),
            'run_id' => wells_overseer_pick($row, ['run_id', 'runId']),
            'pipeline_id' => wells_overseer_pick($row, ['pipeline_id', 'pipelineId']),
            'host_id' => wells_overseer_pick($row, ['host_id', 'hostId']),
            'module_id' => wells_overseer_pick($row, ['module_id', 'moduleId']),
            'level' => wells_overseer_pick($row, ['level']),
            'event_type' => wells_overseer_pick($row, ['event_type', 'eventType']),
            'message' => $message,
            'created_at' => wells_overseer_pick($row, ['created_at', 'createdAt', 'timestamp']),
        ];
    }

    return $out;
}

$pipelineId = wells_overseer_valid_id((string)(filter_input(INPUT_GET, 'pipeline_id', FILTER_UNSAFE_RAW) ?? ''));
$hostId = wells_overseer_valid_id((string)(filter_input(INPUT_GET, 'host_id', FILTER_UNSAFE_RAW) ?? ''));
$runId = wells_overseer_valid_id((string)(filter_input(INPUT_GET, 'run_id', FILTER_UNSAFE_RAW) ?? ''));
$limitRaw = filter_input(INPUT_GET, 'limit', FILTER_VALIDATE_INT);
$limit = ($limitRaw !== false && $limitRaw !== null) ? max(1, min((int)$limitRaw, 100)) : 40;
$windowRaw = (string)(filter_input(INPUT_GET, 'window', FILTER_UNSAFE_RAW) ?? '');
$window = wells_overseer_parse_window($windowRaw);
if ($windowRaw !== '' && $window === null) {
    wells_api_send_json_error(400, 'Parâmetros de consulta inválidos.');
}
$sinceRaw = trim((string)(filter_input(INPUT_GET, 'since', FILTER_UNSAFE_RAW) ?? ''));
$sinceIso = null;
if ($sinceRaw !== '') {
    $sinceTs = strtotime($sinceRaw);
    if ($sinceTs === false) {
        wells_api_send_json_error(400, 'Parâmetros de consulta inválidos.');
    }
    $sinceIso = gmdate('c', $sinceTs);
    if ($window === null) {
        $window = 'custom';
    }
}
if ($sinceIso === null && $window !== null && $window !== 'all') {
    $sinceIso = wells_overseer_since_for_window($window);
}
if ($window === null) {
    $window = 'all';
}

if (($pipelineId === null && filter_input(INPUT_GET, 'pipeline_id', FILTER_UNSAFE_RAW) !== null && (string)filter_input(INPUT_GET, 'pipeline_id', FILTER_UNSAFE_RAW) !== '')
    || ($runId === null && filter_input(INPUT_GET, 'run_id', FILTER_UNSAFE_RAW) !== null && (string)filter_input(INPUT_GET, 'run_id', FILTER_UNSAFE_RAW) !== '')
    || ($hostId === null && filter_input(INPUT_GET, 'host_id', FILTER_UNSAFE_RAW) !== null && (string)filter_input(INPUT_GET, 'host_id', FILTER_UNSAFE_RAW) !== '')) {
    wells_api_send_json_error(400, 'Parâmetros de consulta inválidos.');
}

$health = wells_overseer_fetch($baseUrl, '/v1/health', $token);

// Detalhe de uma run (inclui logs).
if ($runId !== null) {
    $detail = wells_overseer_fetch($baseUrl, '/v1/read/runs/' . rawurlencode($runId), $token);
    $run = is_array($detail['run'] ?? null) ? $detail['run'] : null;
    $publicRun = $run !== null ? (wells_overseer_public_runs([$run], 1)[0] ?? null) : null;
    wells_api_send_json([
        'ok' => (bool)($health['ok'] ?? false) && (bool)($detail['ok'] ?? false) && $publicRun !== null,
        'service' => 'WELLS_API',
        'module' => 'overseer',
        'version' => wells_api_env('WELLS_API_VERSION', WELLS_API_VERSION),
        'overseer' => [
            'api_reachable' => (bool)($health['ok'] ?? false),
            'upstream_host' => overseer_upstream_host($baseUrl),
            'profile' => wells_api_profile_name(),
            'view' => 'run',
            'run' => $publicRun,
            'modules' => wells_overseer_public_modules($detail['modules'] ?? null),
            'logs' => wells_overseer_public_logs($detail['logs'] ?? null),
        ],
        'timestamp' => gmdate('c'),
    ]);
}

$overview = wells_overseer_fetch($baseUrl, '/v1/read/overview', $token);

$data = is_array($overview['data'] ?? null) ? $overview['data'] : $overview;
$summary = is_array($data['summary'] ?? null) ? $data['summary'] : [];
$signals = is_array($data['operationalSignals'] ?? null)
    ? $data['operationalSignals']
    : (is_array($overview['overview']['operationalSignals'] ?? null) ? $overview['overview']['operationalSignals'] : []);

$opsOk = (bool)($overview['ok'] ?? false);
$opsError = null;
if (!$opsOk) {
    $candidate = wells_overseer_pick($overview, ['error', 'detail']);
    $opsError = is_string($candidate) ? $candidate : 'Overview unavailable';
}

$pipelines = wells_overseer_public_pipelines($data['pipelines'] ?? null);
$recentRuns = wells_overseer_public_runs($data['recent_runs'] ?? $data['recentRuns'] ?? null, $limit);
$runsPayload = null;
$dateParamUsed = null;

// Runs com janela temporal (e/ou pipeline) via upstream + filtro local.
$windowFetch = wells_overseer_fetch_runs_window(
    $baseUrl,
    $token,
    $limit,
    $window === 'all' ? null : $sinceIso,
    $pipelineId,
    $hostId
);
$runsPayload = $windowFetch['payload'];
$fromList = $windowFetch['items'];
$scannedRuns = is_array($windowFetch['scanned'] ?? null) ? $windowFetch['scanned'] : $fromList;
$dateParamUsed = $windowFetch['date_param'];
$scanLimitUsed = (int)($windowFetch['scan_limit'] ?? 1000);
if (count($fromList) > 0 || $pipelineId !== null || $window !== 'all') {
    $recentRuns = $fromList;
} elseif (count($recentRuns) < $limit && count($fromList) > count($recentRuns)) {
    $recentRuns = $fromList;
}

if ($pipelineId !== null) {
    $pipelines = array_values(array_filter($pipelines, static function ($pipeline) use ($pipelineId, $hostId) {
        if (($pipeline['pipeline_id'] ?? null) !== $pipelineId) {
            return false;
        }
        if ($hostId !== null && ($pipeline['host_id'] ?? null) !== $hostId) {
            return false;
        }

        return true;
    }));
}

$counts = wells_overseer_count_run_statuses($scannedRuns);
$metaTotal = is_array($runsPayload) ? wells_overseer_payload_total($runsPayload) : null;
$rawScanCount = (int)($windowFetch['raw_count'] ?? count($scannedRuns));
$windowExact = true;
$windowTotal = $counts['total'];
$windowOk = $counts['ok'];
$windowFailed = $counts['failed'];
$summaryTotal = wells_overseer_pick($summary, ['totalRuns', 'total_runs', 'runs']);
$summaryOk = wells_overseer_pick($summary, ['ok', 'ok_runs']);
$summaryFailed = wells_overseer_pick($summary, ['failed', 'nok_runs']);
$summaryRuns24h = wells_overseer_pick($summary, ['runs_24h', 'runs24h']);
if ($summaryRuns24h === null && isset($summary['volume']) && is_array($summary['volume'])) {
    $summaryRuns24h = wells_overseer_pick($summary['volume'], ['runs24h', 'runs_24h']);
}
$summaryFailed7d = wells_overseer_pick($summary, ['failed_7d', 'failed7d']);
$scanComplete = wells_overseer_scan_complete(
    is_array($runsPayload['items'] ?? null) ? wells_overseer_public_runs($runsPayload['items'], $scanLimitUsed) : $scannedRuns,
    $window === 'all' ? null : $sinceIso,
    $scanLimitUsed
);

if ($window === 'all' && $pipelineId === null) {
    if (is_numeric($summaryTotal)) {
        $windowTotal = max(0, (int)$summaryTotal);
        $windowOk = is_numeric($summaryOk) ? max(0, (int)$summaryOk) : $windowOk;
        $windowFailed = is_numeric($summaryFailed) ? max(0, (int)$summaryFailed) : $windowFailed;
        $windowExact = true;
    } elseif ($metaTotal !== null) {
        $windowTotal = $metaTotal;
        $windowExact = true;
    } elseif (!$scanComplete) {
        $windowTotal = $scanLimitUsed;
        $windowExact = false;
    }
} elseif ($window === '24h' && $pipelineId === null && is_numeric($summaryRuns24h)) {
    $windowTotal = max(0, (int)$summaryRuns24h);
    $windowExact = true;
    $windowOk = $counts['ok'];
    $windowFailed = $counts['failed'];
} elseif ($metaTotal !== null) {
    $windowTotal = $metaTotal;
    $windowExact = true;
} elseif ($scanComplete) {
    $windowTotal = $counts['total'];
    $windowExact = true;
    if ($window === '7d' && $pipelineId === null && is_numeric($summaryFailed7d)) {
        $windowFailed = max(0, (int)$summaryFailed7d);
    }
} elseif ($window === '7d' && $pipelineId === null) {
    $cacheKey = '7d|' . (string)$sinceIso . '|' . (string)$dateParamUsed . '|' . count($pipelines);
    $cached = wells_overseer_stats_cache_get($cacheKey, 45);
    if (is_array($cached) && isset($cached['total'])) {
        $windowTotal = (int)$cached['total'];
        $windowOk = (int)($cached['ok'] ?? 0);
        $windowFailed = (int)($cached['failed'] ?? 0);
        $windowExact = (bool)($cached['exact'] ?? false);
    } else {
        $agg = wells_overseer_count_window_by_pipelines($baseUrl, $token, $pipelines, $sinceIso, $dateParamUsed);
        $windowTotal = $agg['total'];
        $windowOk = $agg['ok'];
        $windowFailed = $agg['failed'];
        $windowExact = $agg['exact'];
        if (is_numeric($summaryFailed7d)) {
            $windowFailed = max(0, (int)$summaryFailed7d);
        }
        wells_overseer_stats_cache_set($cacheKey, [
            'total' => $windowTotal,
            'ok' => $windowOk,
            'failed' => $windowFailed,
            'exact' => $windowExact,
        ]);
    }
} else {
    $windowTotal = max($counts['total'], $rawScanCount > 0 ? min($rawScanCount, $scanLimitUsed) : $counts['total']);
    $windowExact = false;
}

$windowStats = [
    'window' => $window,
    'total' => $windowTotal,
    'ok' => $windowOk,
    'failed' => $windowFailed,
    'exact' => $windowExact,
    'since' => $sinceIso,
    'date_param' => $dateParamUsed,
    'scanned' => count($scannedRuns),
];

// Enriquecer pipelines com último run quando o overview não traz last_status.
$latestByPipeline = [];
foreach ($recentRuns as $run) {
    $pid = is_string($run['pipeline_id'] ?? null) ? $run['pipeline_id'] : null;
    if ($pid === null || $pid === '' || isset($latestByPipeline[$pid])) {
        continue;
    }
    $latestByPipeline[$pid] = $run;
}
foreach ($pipelines as $index => $pipeline) {
    $pid = is_string($pipeline['pipeline_id'] ?? null) ? $pipeline['pipeline_id'] : null;
    if ($pid === null || !isset($latestByPipeline[$pid])) {
        continue;
    }
    $run = $latestByPipeline[$pid];
    if (($pipeline['last_status'] ?? null) === null) {
        $pipelines[$index]['last_status'] = $run['status'] ?? null;
    }
    if (($pipeline['last_ended_at'] ?? null) === null) {
        $pipelines[$index]['last_ended_at'] = $run['ended_at'] ?? $run['started_at'] ?? null;
    }
}

wells_api_send_json([
    'ok' => (bool)($health['ok'] ?? false),
    'service' => 'WELLS_API',
    'module' => 'overseer',
    'version' => wells_api_env('WELLS_API_VERSION', WELLS_API_VERSION),
    'overseer' => [
        'api_reachable' => (bool)($health['ok'] ?? false),
        'upstream_host' => overseer_upstream_host($baseUrl),
        'profile' => wells_api_profile_name(),
        'ops_ok' => $opsOk,
        'ops_error' => $opsError,
        'view' => $pipelineId !== null ? 'pipeline' : 'overview',
        'filter' => [
            'pipeline_id' => $pipelineId,
            'host_id' => $hostId,
            'limit' => $limit,
            'window' => $window,
            'since' => $sinceIso,
        ],
        'generated_at' => wells_overseer_pick($data, ['generated_at', 'generatedAt'])
            ?? wells_overseer_pick($overview, ['generated_at', 'generatedAt']),
        'summary' => [
            'totalRuns' => wells_overseer_pick($summary, ['totalRuns', 'total_runs', 'runs']),
            'ok' => wells_overseer_pick($summary, ['ok', 'ok_runs']),
            'failed' => wells_overseer_pick($summary, ['failed', 'nok_runs']),
            'runs_24h' => is_numeric($summaryRuns24h) ? (int)$summaryRuns24h : null,
            'failed_7d' => is_numeric($summaryFailed7d) ? (int)$summaryFailed7d : null,
            'pipelines' => count($pipelines),
        ],
        'window_stats' => $windowStats,
        'signals' => [
            'atRisk' => wells_overseer_pick($signals, ['atRisk', 'at_risk'])
                ?? wells_overseer_pick($summary, ['at_risk', 'atRisk']),
            'stale' => wells_overseer_pick($signals, ['stale'])
                ?? wells_overseer_pick($summary, ['stale']),
            'regressions' => wells_overseer_pick($signals, ['regressions'])
                ?? wells_overseer_pick($summary, ['regressions']),
        ],
        'pipelines' => $pipelines,
        'recent_runs' => $recentRuns,
    ],
    'timestamp' => gmdate('c'),
]);
