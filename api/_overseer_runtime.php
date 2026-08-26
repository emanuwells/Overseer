<?php
declare(strict_types=1);

/**
 * Bootstrap comum das APIs públicas.
 *
 * Este ficheiro mantém regras transversais de produção num único ponto:
 * codificação UTF-8, erros sem exposição ao cliente, CORS configurável e
 * respostas JSON de erro previsíveis. Não deve ser chamado diretamente por HTTP.
 */

if (basename((string)($_SERVER['SCRIPT_NAME'] ?? '')) === basename(__FILE__)) {
    http_response_code(404);
    exit;
}

const WELLS_API_VERSION = '1.13.0';

ini_set('default_charset', 'UTF-8');
ini_set('display_errors', '0');
ini_set('log_errors', '1');
error_reporting(E_ALL);

function wells_api_load_service_env_file(string $path): void
{
    if (!is_readable($path)) {
        return;
    }

    $lines = file($path, FILE_IGNORE_NEW_LINES);
    if ($lines === false) {
        return;
    }

    foreach ($lines as $line) {
        $line = trim($line);
        if ($line === '' || $line[0] === '#' || strpos($line, '=') === false) {
            continue;
        }

        [$key, $value] = explode('=', $line, 2);
        $key = trim($key);
        $value = trim($value, " \t\"'");
        if ($key === '' || getenv($key) !== false) {
            continue;
        }

        putenv($key . '=' . $value);
        $_ENV[$key] = $value;
    }
}

foreach (['/home/eferreira/Dev/secrets/wells-service.env'] as $serviceEnvPath) {
    wells_api_load_service_env_file($serviceEnvPath);
}

function wells_api_env(string $key, ?string $default = null): ?string
{
    $value = getenv($key);
    if ($value === false) {
        return $default;
    }

    $trimmed = trim((string)$value);
    return $trimmed === '' ? $default : $trimmed;
}

function wells_api_csv_env(string $key, array $default): array
{
    $raw = wells_api_env($key);
    if ($raw === null) {
        return $default;
    }

    $items = array_values(array_filter(array_map(
        static fn (string $item): string => trim($item),
        explode(',', $raw)
    )));

    return $items === [] ? $default : $items;
}

function wells_api_config_path(): ?string
{
    $envPath = wells_api_env('WELLS_API_CONFIG');
    if ($envPath !== null) {
        return $envPath;
    }

    $candidates = [
        '/home/eferreira/Dev/secrets/api.config.json',
        '/etc/wells-api/api.config.json',
        dirname(__DIR__) . '/config/api.config.json',
        dirname(__DIR__) . '/config/api.config.example.json',
    ];

    foreach ($candidates as $candidate) {
        if (is_file($candidate)) {
            return $candidate;
        }
    }

    return null;
}

function wells_api_config(): array
{
    static $config = null;
    if (is_array($config)) {
        return $config;
    }

    $path = wells_api_config_path();
    if ($path === null) {
        $config = [];
        return $config;
    }

    $raw = file_get_contents($path);
    if ($raw === false) {
        $config = [];
        return $config;
    }

    // Alguns servidores ou scripts Windows podem gravar JSON com BOM UTF-8.
    // Removemos essa marca antes do decode para manter a configuração portátil.
    $raw = preg_replace('/^\xEF\xBB\xBF/', '', $raw) ?? $raw;
    $decoded = json_decode($raw, true);
    $config = is_array($decoded) ? $decoded : [];
    return $config;
}

function wells_api_profile_name(): string
{
    $config = wells_api_config();
    return wells_api_env('WELLS_API_PROFILE', (string)($config['default_profile'] ?? 'local')) ?? 'local';
}

function wells_api_profile_config(): array
{
    $config = wells_api_config();
    $profileName = wells_api_profile_name();
    $profiles = isset($config['profiles']) && is_array($config['profiles']) ? $config['profiles'] : [];
    $profile = $profiles[$profileName] ?? [];
    return is_array($profile) ? $profile : [];
}

function wells_api_api_config(string $apiName): array
{
    $config = wells_api_config();
    $apis = isset($config['apis']) && is_array($config['apis']) ? $config['apis'] : [];
    $api = $apis[$apiName] ?? [];
    return is_array($api) ? $api : [];
}

function wells_api_config_value(array $config, string $path, $default = null)
{
    $current = $config;
    foreach (explode('.', $path) as $segment) {
        if (!is_array($current) || !array_key_exists($segment, $current)) {
            return $default;
        }
        $current = $current[$segment];
    }

    return $current;
}

function wells_api_sql_identifier(string $identifier): string
{
    $parts = array_values(array_filter(array_map('trim', explode('.', $identifier))));
    if ($parts === []) {
        throw new InvalidArgumentException('Identificador SQL vazio.');
    }

    foreach ($parts as $part) {
        if (!preg_match('/^[A-Za-z0-9_]+$/', $part)) {
            throw new InvalidArgumentException('Identificador SQL inválido.');
        }
    }

    return implode('.', array_map(static fn (string $part): string => '`' . $part . '`', $parts));
}

function wells_api_load_credentials_file(string $path): array
{
    if (!is_file($path)) {
        return [];
    }

    $extension = strtolower(pathinfo($path, PATHINFO_EXTENSION));
    if ($extension === 'json') {
        $raw = file_get_contents($path);
        if ($raw === false) {
            return [];
        }
        $raw = preg_replace('/^\xEF\xBB\xBF/', '', $raw) ?? $raw;
        $decoded = json_decode($raw, true);
        return is_array($decoded) ? $decoded : [];
    }

    $loaded = include $path;
    return is_array($loaded) ? $loaded : [];
}

function wells_api_origin_allowed(string $origin, array $allowedOrigins): bool
{
    return in_array('*', $allowedOrigins, true) || in_array($origin, $allowedOrigins, true);
}

function wells_api_apply_cors(array $defaultAllowedOrigins, array $methods): void
{
    $allowedOrigins = wells_api_csv_env('WELLS_API_ALLOWED_ORIGINS', $defaultAllowedOrigins);
    $origin = isset($_SERVER['HTTP_ORIGIN']) ? trim((string)$_SERVER['HTTP_ORIGIN']) : '';

    header('Vary: Origin');
    header('Access-Control-Allow-Methods: ' . implode(', ', $methods));

    if ($origin !== '' && wells_api_origin_allowed($origin, $allowedOrigins)) {
        header('Access-Control-Allow-Origin: ' . (in_array('*', $allowedOrigins, true) ? '*' : $origin));
        header('Access-Control-Max-Age: 86400');
    } elseif ($origin === '' && in_array('*', $allowedOrigins, true)) {
        header('Access-Control-Allow-Origin: *');
    }

    if (($_SERVER['REQUEST_METHOD'] ?? 'GET') === 'OPTIONS') {
        if ($origin !== '' && !wells_api_origin_allowed($origin, $allowedOrigins)) {
            wells_api_send_json_error(403, 'Origem não permitida.');
        }

        header('Access-Control-Allow-Headers: Authorization, Content-Type, X-Requested-With');
        http_response_code(204);
        exit;
    }
}

function wells_api_send_json(array $payload, int $status = 200): void
{
    http_response_code($status);
    header('Content-Type: application/json; charset=utf-8');
    header('X-Content-Type-Options: nosniff');
    echo json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

function wells_api_send_json_error(int $status, string $message): void
{
    wells_api_send_json([
        'ok' => false,
        'error' => $message,
    ], $status);
}

function wells_api_json_error(int $status, string $message): void
{
    wells_api_send_json_error($status, $message);
}
