#!/bin/bash

DIR="$(cd "$(dirname "$0")" && pwd -P)"
VARS_FILE=${DIR}/vars.sh
VARS_LOCAL_FILE=${DIR}/vars.local.sh
HOOKS_JSON_GEN=${DIR}/generate_hooks_json.py
HOOKS_SRC=${DIR}/hooks
HOOKS_JSON_DEST=${DIR}/container_data/hooks.json

[ ! -r "${VARS_FILE}" ] && echo "missing vars file: ${VARS_FILE}" && exit 1

# shellcheck source=vars.sh
source $VARS_FILE
# shellcheck source=vars.local.sh
[ -r "${VARS_LOCAL_FILE}" ] && source $VARS_LOCAL_FILE

[ ! "$IMAGE" ] && echo "missing variable IMAGE" && exit 1
[ ! "$CONTAINER" ] && echo "missing variable CONTAINER" && exit 1
[ ! "$INTERFACE" ] && echo "missing variable INTERFACE" && exit 1
[ ! "$PORT" ] && echo "missing variable PORT" && exit 1
[ ! -x "$HOOKS_JSON_GEN" ] && echo "script to generate hooks.json not executable at $HOOKS_JSON_GEN" && exit 1

$HOOKS_JSON_GEN $HOOKS_SRC $HOOKS_JSON_DEST
[ ! $? -eq 0 ] && echo "error while generating hooks.json" && exit 1

# kill eventually running containers with same name
docker ps \
    --filter name=^/${CONTAINER}\$ \
    --all \
    --no-trunc \
    --format "{{.ID}}" | xargs --no-run-if-empty docker rm --force

docker run \
    --detach \
    --restart always \
    --publish "${INTERFACE}:${PORT}:9000" \
    --volume /dir/to/hooks/on/host:/etc/webhook \
    --user "$(id -u):$(id -g)" \
    --name="${CONTAINER}" \
    almir/webhook \
        -verbose \
        -hooks=/etc/webhook/hooks.json \
        -hotreload
