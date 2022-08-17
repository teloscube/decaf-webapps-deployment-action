#!/usr/bin/env bash

# Fail on errors:
set -e
set -x

eval "$(ssh-agent -s)"
echo "$INPUT_REMOTE_KEY" | tr -d '\r' | ssh-add -

_args=(
    "-H" "${INPUT_REMOTE_HOST}"
    "-U" "${INPUT_REMOTE_USER}"
    "-P" "${INPUT_REMOTE_PORT}"
    "-n" "${INPUT_APP_NAME}"
)

if [ -n "$INPUT_PRODUCTION" ]; then
    _args=("${_args[@]}" "--segment" "production")
fi
if [ -n "$INPUT_STAGING" ]; then
    _args=("${_args[@]}" "--segment" "staging")
fi
if [ -n "$INPUT_PREVIEW" ]; then
    _pr_number="$(echo "${GITHUB_REF}" | awk 'BEGIN { FS = "/" } ; { print $3 }')"
    _args=("${_args[@]}" "--segment" "preview-${_pr_number}")
fi
if [ -n "$INPUT_VERSION" ]; then
    _args=("${_args[@]}" "--segment" "${INPUT_VERSION}")
fi
if [ -n "$INPUT_SENTRY_TOKEN" ] && [ -n "$INPUT_UPLOAD_TO_SENTRY" ]; then
    _args=("${_args[@]}" "--upload-to-sentry" "--sentry-token" "${INPUT_SENTRY_TOKEN}")
fi

exec "${GITHUB_ACTION_PATH}/build-and-deploy.py" "${_args[@]}"
