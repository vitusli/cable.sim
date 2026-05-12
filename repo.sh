#!/bin/bash
set -e

export OMNI_REPO_ROOT="$( cd "$(dirname "$0")" ; pwd -P )"

if [[ -f "${OMNI_REPO_ROOT}/repo-cache.json" ]]; then
    PM_PACKAGES_ROOT=$(grep '"PM_PACKAGES_ROOT"' "${OMNI_REPO_ROOT}/repo-cache.json" | sed 's/.*"PM_PACKAGES_ROOT": "\(.*\)".*/\1/')

    if [[ -n "${PM_PACKAGES_ROOT}" ]]; then
        RESOLVED_PACKAGES_ROOT=$(eval echo "$PM_PACKAGES_ROOT")

        if [[ "${RESOLVED_PACKAGES_ROOT}" != /* ]]; then
            PM_PACKAGES_ROOT="${OMNI_REPO_ROOT}/${RESOLVED_PACKAGES_ROOT}"
        else
            PM_PACKAGES_ROOT=${RESOLVED_PACKAGES_ROOT}
        fi
        export PM_PACKAGES_ROOT
    fi
fi

exec "${OMNI_REPO_ROOT}/tools/packman/python.sh" "${OMNI_REPO_ROOT}/tools/repoman/repoman.py" "$@"
