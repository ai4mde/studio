#!/bin/bash

export SOURCE_PROJECT_NAME=$1
export TARGET_PROJECT_NAME=$2
export WORKDIR=/usr/src/prototypes/generated_prototypes

move_database() {
    rm -f "${WORKDIR}/${TARGET_PROJECT_NAME}/db.sqlite3"
    cp "${WORKDIR}/${SOURCE_PROJECT_NAME}/db.sqlite3" "${WORKDIR}/${TARGET_PROJECT_NAME}/db.sqlite3"
}

move_database
exit 0