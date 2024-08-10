#!/bin/bash

export PROJECT_NAME=$1
export OUTDIR=/usr/src/prototypes/generated_prototypes
export ROOT=/usr/src/prototypes/


remove_django_project() {
    rm -rf "${OUTDIR}/${PROJECT_NAME}"
}

remove_django_project
exit 0