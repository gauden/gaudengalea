#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
CONFIG_PATH="${1:-${PROJECT_DIR}/goaccess-sites.yaml}"
COMPOSE_PATH="${PROJECT_DIR}/compose.yaml"
CADDY_SNIPPET_PATH="${PROJECT_DIR}/caddy/webstats.caddy.snippet"

"${SCRIPT_DIR}/validate-sites.sh" "${CONFIG_PATH}"

tmp_compose="$(mktemp)"
tmp_caddy="$(mktemp)"
trap 'rm -f "${tmp_compose}" "${tmp_caddy}"' EXIT

python3 "${SCRIPT_DIR}/lib_sites.py" render-compose "${CONFIG_PATH}" "${tmp_compose}" >/dev/null
python3 "${SCRIPT_DIR}/lib_sites.py" render-caddy "${CONFIG_PATH}" "${tmp_caddy}" >/dev/null

if [[ -f "${COMPOSE_PATH}" ]] && cmp -s "${tmp_compose}" "${COMPOSE_PATH}"; then
  echo "compose.yaml unchanged"
else
  mv "${tmp_compose}" "${COMPOSE_PATH}"
  echo "compose.yaml updated"
fi

if [[ -f "${CADDY_SNIPPET_PATH}" ]] && cmp -s "${tmp_caddy}" "${CADDY_SNIPPET_PATH}"; then
  echo "caddy snippet unchanged"
else
  mv "${tmp_caddy}" "${CADDY_SNIPPET_PATH}"
  echo "caddy snippet updated"
fi

enabled_sites="$(python3 "${SCRIPT_DIR}/lib_sites.py" list-enabled "${CONFIG_PATH}")"

if [[ -z "${enabled_sites}" ]]; then
  echo "No enabled sites found; bringing stack down"
  docker compose -f "${COMPOSE_PATH}" down --remove-orphans
  exit 0
fi

while IFS=$'\t' read -r site_id _container_name _internal_port; do
  [[ -z "${site_id}" ]] && continue
  mkdir -p "/home/ubuntu/apps/caddy/data/goaccess/${site_id}"
done <<< "${enabled_sites}"

docker compose -f "${COMPOSE_PATH}" up -d --remove-orphans

while IFS=$'\t' read -r site_id container_name internal_port; do
  [[ -z "${site_id}" ]] && continue

  running_state="$(docker inspect -f '{{.State.Running}}' "${container_name}" 2>/dev/null || true)"
  if [[ "${running_state}" != "true" ]]; then
    echo "ERROR: container is not running: ${container_name}" >&2
    exit 1
  fi

  on_network="$(docker inspect -f '{{if index .NetworkSettings.Networks "caddy_default"}}yes{{end}}' "${container_name}" 2>/dev/null || true)"
  if [[ "${on_network}" != "yes" ]]; then
    echo "ERROR: container is not attached to caddy_default: ${container_name}" >&2
    exit 1
  fi

  echo "healthy: ${site_id} (${container_name}:${internal_port})"
done <<< "${enabled_sites}"

echo "Reconcile complete"
