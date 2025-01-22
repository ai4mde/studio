#!/bin/bash

export SOURCE_PROJECT_NAME=$1
export TARGET_PROJECT_NAME=$2
export SYSTEM_ID=$3
export WORKDIR=/usr/src/prototypes/generated_prototypes

move_database() {
    rm -f "${WORKDIR}/${SYSTEM_ID}/${TARGET_PROJECT_NAME}/db.sqlite3"
    cp "${WORKDIR}/${SYSTEM_ID}/${SOURCE_PROJECT_NAME}/db.sqlite3" "${WORKDIR}/${SYSTEM_ID}/${TARGET_PROJECT_NAME}/db.sqlite3"
}

move_database
exit 0