#!/bin/bash

export PROJECT_ID=$1
export PROJECT_SYSTEM=$2
export PROJECT_NAME=$3
export METADATA_ARG="$4"
export WORKDIR=/usr/src/prototypes/backend/generation
export OUTDIR=/usr/src/prototypes/generated_prototypes
export ROOT=/usr/src/prototypes/
export PYTHON_BIN=/usr/src/.venv/bin/python

export PYTHONPATH="${WORKDIR}/generation_scripts"

# Global settings such as authentication go here
export AUTH_PRESENT=$(${PYTHON_BIN} "${WORKDIR}/generation_scripts/get_globals.py" get_auth "$METADATA_ARG")


create_outdir() {
    cd "${ROOT}"
    mkdir -p generated_prototypes
    cd generated_prototypes
    mkdir -p "${PROJECT_SYSTEM}"
}

create_new_django_project() {
    cd "${OUTDIR}/${PROJECT_SYSTEM}"
    if [ -d "$PROJECT_NAME" ]; then
        echo "Warning: Directory with project name already exists. Removing old version."
        rm -rf "$PROJECT_NAME"
    fi
    ${PYTHON_BIN} -m django startproject "$PROJECT_NAME"
}

update_django_project_settings() {
    cd "${OUTDIR}/${PROJECT_SYSTEM}/${PROJECT_NAME}/${PROJECT_NAME}"
    echo "ALLOWED_HOSTS += ['*']" >> settings.py
    echo "from django.urls import include" >> urls.py
    
    if [ "$AUTH_PRESENT" = "True" ]; then
        echo "AUTH_USER_MODEL = \"shared_models.User\"" >> settings.py
    fi
}

create_shared_models_app() {
    cd "${OUTDIR}/${PROJECT_SYSTEM}/${PROJECT_NAME}"
    ${PYTHON_BIN} -m django startapp "shared_models"
    ${PYTHON_BIN} "${WORKDIR}/generation_scripts/generate_models.py" "$PROJECT_NAME" "$METADATA_ARG" "$AUTH_PRESENT" "$PROJECT_SYSTEM"
    cd "${OUTDIR}/${PROJECT_SYSTEM}/${PROJECT_NAME}/${PROJECT_NAME}"
	echo "INSTALLED_APPS += ['shared_models']" >> settings.py
}

create_workflow_engine_app() {
    cd "${OUTDIR}/${PROJECT_SYSTEM}/${PROJECT_NAME}"
    ${PYTHON_BIN} -m django startapp "workflow_engine"
    ${PYTHON_BIN} "${WORKDIR}/generation_scripts/generate_workflow_engine.py" "$PROJECT_NAME" "$METADATA_ARG" "$PROJECT_SYSTEM" "$AUTH_PRESENT"
    cp "${WORKDIR}/workflow_engine/urls.py" "${OUTDIR}/${PROJECT_SYSTEM}/${PROJECT_NAME}/workflow_engine/"
    cd "${OUTDIR}/${PROJECT_SYSTEM}/${PROJECT_NAME}/${PROJECT_NAME}"
    echo "INSTALLED_APPS += ['workflow_engine', 'django_crontab']" >> settings.py
    echo "urlpatterns += [path('workflow_engine', include('workflow_engine.urls', namespace='workflow_engine'))]" >> urls.py
}   

create_authentication_app() {
    cd "${OUTDIR}/${PROJECT_SYSTEM}/${PROJECT_NAME}"
    ${PYTHON_BIN} -m django startapp "authentication"
    ${PYTHON_BIN} "${WORKDIR}/generation_scripts/generate_authentication.py" "$PROJECT_NAME" "$METADATA_ARG" "$PROJECT_SYSTEM"
    cd "${OUTDIR}/${PROJECT_SYSTEM}/${PROJECT_NAME}/${PROJECT_NAME}"
	echo "INSTALLED_APPS += ['authentication']" >> settings.py
    echo "LOGIN_URL = '/'" >> settings.py
    echo "urlpatterns += [path(\"\", include(\"authentication.urls\"))]" >> urls.py

}

create_noauth_home_app() {
    cd "${OUTDIR}/${PROJECT_SYSTEM}/${PROJECT_NAME}"
    ${PYTHON_BIN} -m django startapp "noauth_home"
    ${PYTHON_BIN} "${WORKDIR}/generation_scripts/generate_noauth_home.py" "$PROJECT_NAME" "$METADATA_ARG" "$PROJECT_SYSTEM"
    cd "${OUTDIR}/${PROJECT_SYSTEM}/${PROJECT_NAME}/${PROJECT_NAME}"
	echo "INSTALLED_APPS += ['noauth_home']" >> settings.py
    echo "urlpatterns += [path(\"\", include(\"noauth_home.urls\"))]" >> urls.py
}


update_global_app_settings() {
    local app="$1"
    cd "${OUTDIR}/${PROJECT_SYSTEM}/${PROJECT_NAME}/${PROJECT_NAME}"
    echo "urlpatterns += [path(\"$app/\", include(\"$app.urls\"))]" >> urls.py
	echo "INSTALLED_APPS += ['$app']" >> settings.py
}

create_new_django_app() {
    local app="$1"
    cd "${OUTDIR}/${PROJECT_SYSTEM}/${PROJECT_NAME}"
    if [ -d "$app" ]; then
        echo "Error: Directory with application component name already exists."
        exit 1
    fi
    ${PYTHON_BIN} -m django startapp "$app"
    ${PYTHON_BIN} "${WORKDIR}/generation_scripts/generate_application.py" "$PROJECT_NAME" "$app" "$METADATA_ARG" "$AUTH_PRESENT" "$PROJECT_SYSTEM"
    update_global_app_settings "$app"
}

create_django_apps() {
    applications=$(${PYTHON_BIN} "${WORKDIR}/generation_scripts/get_globals.py" get_apps "$METADATA_ARG")
    
    cd "${OUTDIR}/${PROJECT_SYSTEM}/${PROJECT_NAME}"
    
    create_shared_models_app
    create_workflow_engine_app
    if [ "$AUTH_PRESENT" = "True" ]; then
        create_authentication_app
    else
        create_noauth_home_app
    fi
    for app in $applications; do
        create_new_django_app "$app"
    done
}

run_migrations() {
    cd "${OUTDIR}/${PROJECT_SYSTEM}/${PROJECT_NAME}"
    ${PYTHON_BIN} "manage.py" "makemigrations"
    cp "${WORKDIR}/workflow_engine/0002_populate_workflow_engine.py" "${OUTDIR}/${PROJECT_SYSTEM}/${PROJECT_NAME}/workflow_engine/migrations"
    ${PYTHON_BIN} "manage.py" "migrate"
}

add_cron_jobs() {
    cd "${OUTDIR}/${PROJECT_SYSTEM}/${PROJECT_NAME}"
    ${PYTHON_BIN} "manage.py" crontab remove 2>/dev/null || true
    ${PYTHON_BIN} "manage.py" crontab add
}

generate_prototype() {
    create_outdir
    create_new_django_project
    update_django_project_settings
    create_django_apps
    run_migrations
    add_cron_jobs
}

generate_prototype

exit 0