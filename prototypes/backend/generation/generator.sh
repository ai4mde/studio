#!/bin/bash

export PROJECT_NAME=$1
export METADATA="$2"
export WORKDIR=/usr/src/prototypes/backend/generation
export OUTDIR=/usr/src/prototypes/generated_prototypes
export ROOT=/usr/src/prototypes/

create_outdir() {
    cd "${ROOT}"
    mkdir -p generated_prototypes
}

create_new_django_project() {
    cd "${OUTDIR}"
    if [ -d "$PROJECT_NAME" ]; then
        echo "Error: Directory with project name already exists."
        exit 1
    fi
    python -m django startproject "$PROJECT_NAME"
}

create_shared_models_app() {
    cd "${OUTDIR}/${PROJECT_NAME}"
    python -m django startapp "shared_models"
    python "${WORKDIR}/generation_scripts/generate_models.py" "$PROJECT_NAME" "$METADATA"
}

create_new_django_app() {
    local app="$1"
    if [ -d "$app" ]; then
        echo "Error: Directory with application component name already exists."
        exit 1
    fi
    python -m django startapp "$app"
    python "${WORKDIR}/generation_scripts/generate_application.py" "$PROJECT_NAME" "$app" "$METADATA"
}

create_django_apps() {
    applications=$(python "${WORKDIR}/generation_scripts/generate_section_table.py" get_apps "$METADATA")
    
    cd "${OUTDIR}/${PROJECT_NAME}"
    for app in $applications; do
        create_new_django_app "$app"
    done
    create_shared_models_app
}

generate_prototype() {
    create_outdir
    create_new_django_project
    create_django_apps
}

generate_prototype

exit 0
