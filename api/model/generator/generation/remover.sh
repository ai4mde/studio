#!/bin/bash

export PROJECT_NAME=$1
export OUTDIR=/tmp/generated_projects
export ROOT=/tmp

remove_django_project() {
    rm -rf "${OUTDIR}/${PROJECT_NAME}"
}

remove_django_project
exit 0