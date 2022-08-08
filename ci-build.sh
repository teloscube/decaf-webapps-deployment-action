#!/usr/bin/env sh

## Fail on errors:
set -e
set -x

## Where are we:
_segment=""

_is_tag () {
    case "${1}" in
        "refs/tags/"*) return 0 ;;
        *)  return 1 ;;
    esac
}

# reference: https://docs.github.com/en/actions/learn-github-actions/environment-variables

if [ -z "${GITHUB_REF}" ]; then
    echo "We are not under GitHub actions. Exiting..." 2>&1
    exit 1
elif [ ! -z "${GITHUB_HEAD_REF}" ]; then
    _pr_number="$(echo "${GITHUB_REF}" | awk 'BEGIN { FS = "/" } ; { print $3 }')"
    _segment="preview-${_pr_number}"
elif [ "${GITHUB_REF}" = "refs/heads/main" ]; then
    _segment="staging"
elif [ "${GITHUB_REF}" = "refs/tags/testing" ]; then
    _segment="testing"
elif _is_tag "${GITHUB_REF}"; then
    if [ "$GITHUB_EVENT_NAME" = "release" ]; then
        _segment="production"
    else
        _tag="$(echo "${GITHUB_REF}" | awk 'BEGIN { FS = "/" } ; { print $3 }')"
        _segment="v${_tag}"
    fi
else
    echo "Unknown REF: ${GITHUB_REF}. Exiting..." 2>&1
    exit 2
fi

## Set URL path:
_urlpath="/webapps/waitress/${_segment}"

## Set output path:
_outpath="dist${_urlpath}/"

## Set environment variables:
export PUBLIC_URL="${_urlpath}"

## Start building:
yarn build && mkdir -p "${_outpath}" && mv build/** "${_outpath}"

## Set outputs:
echo ::set-output name=segment::"${_segment}"
echo ::set-output name=urlpath::"${_urlpath}"
echo ::set-output name=outpath::"${_outpath}"

