#!/usr/bin/env bash
set -euo pipefail

here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
[[ ${GITHUB_RUN_ID:-} =~ ^[0-9]+$ && ${GITHUB_RUN_ATTEMPT:-} =~ ^[0-9]+$ ]] || { echo 'CI run identity required' >&2; exit 2; }
[[ ${GITHUB_SHA:-} =~ ^[a-f0-9]{40}$ ]] || { echo 'Commit SHA required' >&2; exit 2; }
bundle=${1:?Report bundle required}
project="juice-aspm-ci-${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}"
private=$(mktemp -d "${RUNNER_TEMP:-/tmp}/juice-aspm-private.XXXXXX")
mkdir -p "${GITHUB_WORKSPACE:-$PWD}/reports"
public=$(mktemp -d "${GITHUB_WORKSPACE:-$PWD}/reports/aspm-${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}.XXXXXX")
chmod 755 "$public"
printf 'report_dir=%s\n' "$public" >> "${GITHUB_OUTPUT:?GitHub output file required}"
compose() {
  docker compose --project-name "$project" --env-file "$private/private.env" -f "$here/compose.yaml" --profile dtrack --profile dojo "$@"
}
cleanup() {
  status=$?
  trap - EXIT
  if ! compose down --volumes --remove-orphans >> "$private/compose.log" 2>&1; then
    echo 'ASPM cleanup failed for the current CI project' >&2
    status=1
  fi
  case "$private" in "${RUNNER_TEMP:-/tmp}"/juice-aspm-private.*) rm -rf -- "$private";; *) status=1;; esac
  exit "$status"
}
trap cleanup EXIT
python3 "$here/manage.py" init --private-dir "$private"
compose pull dtrack-api dtrack-db dojo-db dojo-valkey dojo-initializer dojo-uwsgi dojo-celeryworker dojo-celerybeat dojo-nginx > "$private/compose.log" 2>&1
compose up -d dtrack-api >> "$private/compose.log" 2>&1
python3 "$here/manage.py" dtrack --private-dir "$private" --reports "$bundle" --output "$public" --sha "$GITHUB_SHA" --run "$GITHUB_RUN_ID"
# Release memory before starting Django/Celery on the standard runner.
compose stop dtrack-api dtrack-db >> "$private/compose.log" 2>&1
compose up -d dojo-nginx dojo-celeryworker dojo-celerybeat >> "$private/compose.log" 2>&1
python3 "$here/manage.py" dojo --private-dir "$private" --reports "$bundle" --output "$public" --sha "$GITHUB_SHA" --run "$GITHUB_RUN_ID"
