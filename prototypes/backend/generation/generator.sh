#!/bin/bash

export PROJECT_NAME=$1
export METADATA="$2"
export WORKDIR=/usr/src/prototypes/backend/generation
export OUTDIR=/usr/src/prototypes/generated_prototypes
export ROOT=/usr/src/prototypes/

# Global settings such as authentication go here
export AUTH_PRESENT=$(python "${WORKDIR}/generation_scripts/get_globals.py" get_auth "$METADATA")


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
    
    if [ "$AUTH_PRESENT" = "True" ]; then
        echo "AUTH_USER_MODEL = \"shared_models.User\"" >> settings.py
    fi
}

create_shared_models_app() {
    cd "${OUTDIR}/${PROJECT_NAME}"
    python -m django startapp "shared_models"
    python "${WORKDIR}/generation_scripts/generate_models.py" "$PROJECT_NAME" "$METADATA" "$AUTH_PRESENT"
    cd "${OUTDIR}/${PROJECT_NAME}/${PROJECT_NAME}"
	echo "INSTALLED_APPS += ['shared_models']" >> settings.py
}

create_authentication_app() {
    cd "${OUTDIR}/${PROJECT_NAME}"
    python -m django startapp "authentication"
    python "${WORKDIR}/generation_scripts/generate_authentication.py" "$PROJECT_NAME" "$METADATA"
    cd "${OUTDIR}/${PROJECT_NAME}/${PROJECT_NAME}"
	echo "INSTALLED_APPS += ['authentication']" >> settings.py
    echo "urlpatterns += [path(\"\", include(\"authentication.urls\"))]" >> urls.py

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
    python "${WORKDIR}/generation_scripts/generate_application.py" "$PROJECT_NAME" "$app" "$METADATA" "$AUTH_PRESENT"
    update_global_app_settings "$app"
}

create_django_apps() {
    applications=$(python "${WORKDIR}/generation_scripts/get_globals.py" get_apps "$METADATA")
    
    cd "${OUTDIR}/${PROJECT_NAME}"
    
    create_shared_models_app
    if [ "$AUTH_PRESENT" = "True" ]; then
        create_authentication_app
    fi
    for app in $applications; do
        create_new_django_app "$app"
    done
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
