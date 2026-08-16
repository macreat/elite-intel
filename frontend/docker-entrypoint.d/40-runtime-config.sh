#!/bin/sh
set -eu

runtime_config_path=/usr/share/nginx/html/runtime-config.js
escaped_api_base_url=$(printf '%s' "${VITE_API_BASE_URL:-}" | sed 's/[\\\"]/[\\&]/g')
printf 'window.__ELITE_CONFIG__ = { apiBaseUrl: "%s" };\n' "$escaped_api_base_url" > "$runtime_config_path"
