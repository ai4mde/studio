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

update_django_project_settings() {
    cd "${OUTDIR}/${PROJECT_NAME}/${PROJECT_NAME}"
    echo "ALLOWED_HOSTS += ['*']" >> settings.py
    echo "from django.urls import include" >> urls.py
}

create_shared_models_app() {
    cd "${OUTDIR}/${PROJECT_NAME}"
    python -m django startapp "shared_models"
    python "${WORKDIR}/generation_scripts/generate_models.py" "$PROJECT_NAME" "$METADATA"
    cd "${OUTDIR}/${PROJECT_NAME}/${PROJECT_NAME}"
	echo "INSTALLED_APPS += ['shared_models']" >> settings.py
}

update_global_app_settings() {
    local app="$1"
    cd "${OUTDIR}/${PROJECT_NAME}/${PROJECT_NAME}"
    echo "urlpatterns += [path(\"$app/\", include(\"$app.urls\"))]" >> urls.py
	echo "INSTALLED_APPS += ['$app']" >> settings.py
}

create_new_django_app() {
    local app="$1"
    cd "${OUTDIR}/${PROJECT_NAME}"
    if [ -d "$app" ]; then
        echo "Error: Directory with application component name already exists."
        exit 1
    fi
    python -m django startapp "$app"
    python "${WORKDIR}/generation_scripts/generate_application.py" "$PROJECT_NAME" "$app" "$METADATA"
    update_global_app_settings "$app"
}

create_django_apps() {
    applications=$(python "${WORKDIR}/generation_scripts/generate_section_table.py" get_apps "$METADATA")
    
    cd "${OUTDIR}/${PROJECT_NAME}"
    for app in $applications; do
        create_new_django_app "$app"
    done
    create_shared_models_app
}

run_migrations() {
    cd "${OUTDIR}/${PROJECT_NAME}"
    python "manage.py" "makemigrations"
    python "manage.py" "migrate"
}

generate_prototype() {
    create_outdir
    create_new_django_project
    update_django_project_settings
    create_django_apps
    run_migrations
}

generate_prototype

exit 0
