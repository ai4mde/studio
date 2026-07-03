#!/bin/bash

export PROJECT_ID=$1
export PROJECT_NAME=$2
export PROJECT_SYSTEM=$3
export OUTDIR=/usr/src/prototypes/generated_prototypes
export ROOT=/usr/src/prototypes/


remove_django_project() {
    rm -rf "${OUTDIR}/${PROJECT_SYSTEM}/${PROJECT_NAME}"
    
    cd "${OUTDIR}/${PROJECT_SYSTEM}"
    if [ ! "$(ls -A .)" ]; then # Delete system directory if it contains no prototypes
        cd "${OUTDIR}"
        rmdir "${OUTDIR}/${PROJECT_SYSTEM}"
    fi
}

remove_django_project
exit 0