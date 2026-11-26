#!/usr/bin/env bash
# Run from the repository root. Only reports/dast is published, never ZAP sessions.
set -euo pipefail
export JUICE_SHOP_IMAGE="${1:?Usage: bash .zap/scan.sh juice-shop:SHA [true|false]}"
extended="${2:-false}"
if [[ "$extended" != true && "$extended" != false ]]; then
  echo 'extended must be true or false' >&2
  exit 2
fi
zap_image=$(tr -d '\r\n' < .zap/image.txt)
project="juice-shop-dast-${GITHUB_RUN_ID:-local}"
network="${project}_default"
scanner="zap-${project}"
compose=(docker compose -p "$project" -f infra/compose.yaml -f infra/compose.dast.yaml)
mkdir -p reports/dast
run_id="${GITHUB_RUN_ID:-local-$(date -u +%Y%m%dT%H%M%SZ)-$$}"
attempt="${GITHUB_RUN_ATTEMPT:-1}"
[[ "$run_id-$attempt" =~ ^[A-Za-z0-9_-]+$ ]]
report_dir=$(mktemp -d "reports/dast/${run_id}-${attempt}-XXXXXX")
chmod 0755 "$report_dir"
if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
  printf 'report_dir=%s\n' "$report_dir" >> "$GITHUB_OUTPUT"
fi
printf 'Reports for this run: %s\n' "$report_dir"
docker pull "$zap_image"
docker image inspect "$JUICE_SHOP_IMAGE" > "$report_dir/image.json"
# Grant the scanner ownership of this new public-output directory only.
docker run --rm --network none --user 0 --volume "$PWD/$report_dir:/zap/wrk:rw" \
  --entrypoint chown "$zap_image" 1000:1000 /zap/wrk
cleanup() {
  status=$?
  if docker container inspect "$scanner" > /dev/null 2>&1; then
    docker rm -f "$scanner"
  fi
  "${compose[@]}" down --remove-orphans
  exit "$status"
}
trap cleanup EXIT
modes=(baseline authenticated)
if [[ "$extended" == true ]]; then
  modes+=(full api)
fi
result=0
for mode in "${modes[@]}"; do
  "${compose[@]}" down --remove-orphans
  "${compose[@]}" up --no-build --wait --wait-timeout 240
  [[ "$(docker network inspect "$network" --format '{{.Internal}}')" == true ]]
  container=$("${compose[@]}" ps -q juice-shop)
  [[ "$(docker inspect "$container" --format '{{.Image}}')" == "$(docker image inspect "$JUICE_SHOP_IMAGE" --format '{{.Id}}')" ]]
  if docker run --rm --name "$scanner" --network "$network" --volume "$PWD:/src:ro" \
      --volume "$PWD/$report_dir:/zap/wrk:rw" --entrypoint python3 "$zap_image" \
      /src/.zap/run.py --mode "$mode" --output "/zap/wrk/$mode"; then
    echo "$mode completed successfully"
  else
    echo "$mode failed; sanitized evidence retained" >&2
    result=1
  fi
done
exit "$result"
