#!/bin/bash

#This script intergrates a django project in the template-driven generation for prototype based on UML metadata
#it operates using files in the generation_script folder and with metadata from the tests folder
#A special case for projects with the name "latest" generates the project with a copy of the previous "latest" project 

# It generally does the following:
# 1. Run django-admin startproject project_name (provided parameter)
# 2. Retrieve app data from application component metadata (using: ./generate_table.py get_apps)
#       The next steps except 9 make use of the general function create_new_app()
# 3. Run django-admin startapp shared_models (specific app where models are definied)
# 4. Run generate_models.py for shared_models
#For each app in application component:
# 5.    run django-admin startapp application_name
# 6.    Link app url files to global url.py file
# 7.    generate_urls.py en generate_views.py en zet de output hiervan onder de juiste applications
# 8.    in case authentication is used: add generic authentication urls to global project urls.py
# 9. Makemigrations & migrate
#           NOTE: for steps 3,4,6,8 we use hard-coded app_name == "authentication" and != "shared_models" 
#           NOTE: if no auth, there is no homepage

PROJECT_NAME=$1
SAVE_IN_BETWEEN_RUNS=1 #this can be turned on to save copies off db in generated_projects/previous
VERBOSE=0
if [ $PROJECT_NAME == "latest" ] 
then
    echo "running in silent mode"
    VERBOSE=1
fi
PORT=8001

#This function does the general steps 5-8 NOTE: appname = "authentication" or "shared_models" (also does step 4. 
create_new_app () {
    local app="$1"
    if [ $VERBOSE == 0 ] 
    then
        echo "start application $app "
    fi
    django-admin startapp $app

    if [ $VERBOSE == 0 ] 
    then
        echo "Adding app $app to installed apps"
    fi
    cd $PROJECT_NAME
    touch settings.py
    echo "INSTALLED_APPS += ['$app']" >> settings.py

    if [ $app != "shared_models" ]
    then
        
        if [ $VERBOSE == 0 ] 
        then
            echo "Adding $app's URL's to global URL's"
        fi

        touch urls.py
        echo "urlpatterns += [path(\"$app/\", include(\"$app.urls\"))]" >> urls.py 
        if [ $app == "authentication" ]
        then
            echo "urlpatterns += [path(\"$app/\", include('django.contrib.auth.urls'))]" >> urls.py 
            echo "urlpatterns += [path('', include('authentication.urls')),]" >> urls.py #NOTE: if no auth, there is no homepage
        fi
    fi

    if [ $VERBOSE == 0 ] 
    then
        echo "Generating templates folder for app: $app"
    fi
    cd ../$app
    mkdir templates
    mkdir static
    cd templates
    mkdir $app
    cd ../../

    if [ $app != "shared_models" ]
    then
        if [ $app != "authentication" ]
        then
            local auth="false"
        else
            local auth="true"
        fi
            
        if [ $VERBOSE == 0 ] 
        then
            echo "Generating html templates, urls and views for $app using table"
        fi

        cd ../../generation_scripts
        python3 ./generate_all_using_table.py $PROJECT_NAME $app $auth $AUTH_IS_PRESENT
        cd ../generated_projects/$PROJECT_NAME
        
        if [ $VERBOSE == 0 ] 
        then
            echo "done with $app"
            echo 
        fi
    fi
}

if [ $# != 1 ]
then
    
    if [ $VERBOSE == 0 ] 
    then
        echo "Usage: ./newgenerator.sh <PROJECT_NAME>"
    fi

    exit 1
fi

if [ $VERBOSE == 0 ] 
then
    echo "Generating project: $PROJECT_NAME"
fi


#clean previous "latest"
if [ $PROJECT_NAME == "latest" ]
then
    cd generated_projects

    if test -d latest;
    then
        if [ $VERBOSE == 0 ] 
        then
            echo "project exists already, so save its database to: previous."
        fi

        if ! test -d previous;
        then
            mkdir previous
        fi

        if test -f previous/db.sqlite3;
        then
            #copy to backup name and replace newest
            cp -r --backup=t previous/db.sqlite3 previous/db.sqlite3old
            rm previous/db.sqlite3
        fi

        if test -f latest/db.sqlite3;
        then
            cp -r --backup=t latest/db.sqlite3 previous/db.sqlite3
        fi
        
        if [ $VERBOSE == 0 ] 
        then
            echo "search for old process(es) still running and kill them"
        fi

        PSOUT=$(ps aux | grep 'manage.py runserver' | tr -s ' ' )
        printf '%s\n' "$PSOUT" | while IFS= read -r line
        do
            if [[ $line == *"python3 manage.py runserver 127.0.0.1:8001"* ]]
            then
                foundPID=$( echo $line | cut  -d " " -f 2)

                if [ $VERBOSE == 0 ] 
                then
                    echo "found PID: $foundPID"
                fi

                kill $foundPID
                break
            fi
        done

        if [ $VERBOSE == 0 ] 
        then
            echo "removing old project files"
        fi

        rm -f -r latest
    fi

    cd ..
fi

cd generated_projects
django-admin startproject $PROJECT_NAME 
if [ $VERBOSE == 0 ] 
then
    echo "Generating applications using table for: $PROJECT_NAME"
fi

cd ../generation_scripts
applications=$(python3 ./generate_section_table.py get_apps | tr -d '[],'\')
models=$(python3 ./generate_section_table.py get_models | tr -d '[],'\')
cd ../generated_projects/$PROJECT_NAME

if [ $VERBOSE == 0 ] 
then
    echo "initialize global URL's and settings"
fi
cd $PROJECT_NAME
mv settings.py settings_global.py
touch settings.py
echo "from .settings_global import *" > settings.py

mv urls.py urls_global.py
touch urls.py
echo "from .urls_global import *" > urls.py
echo "from django.contrib import admin" >> urls.py 
echo "from django.urls import path, include" >> urls.py 

cd ../

create_new_app "shared_models"
if [ $VERBOSE == 0 ] 
then
    echo "Generating models for shared_models"
fi
cd ../../generation_scripts
python3 ./generate_models.py $PROJECT_NAME "shared_models"
cd ../generated_projects/$PROJECT_NAME

#write models to admin.py to edit as admin
if [ $VERBOSE == 0 ] 
then
    echo "register models in admin.py in shared_models"
fi
cd shared_models
addline="
from .models import "
for model in $models
do
    addline=$addline$model", "
done
echo ${addline::-2}>> admin.py

for model in $models
do
    echo "admin.site.register($model)" >> admin.py
done
cd ../

cd  ./$PROJECT_NAME
# sed -i'/.*\{.*django\.contrib\.auth\.password_.*\n.*\}\,.*/d' ./settings_global.py TODO for good database
# new one  |
#          V
# sed -i.bak '/django\.contrib\.auth\.password/d' ./settings_global.txt

echo "AUTH_USER_MODEL = \"shared_models.User\"" >> settings_global.py

cd ../
if [ $VERBOSE == 0 ] 
then
    echo "Done with globals"
    echo
fi

AUTH_IS_PRESENT="false"
for app in $applications
do
    if [ $app == "authentication" ]
    then
        AUTH_IS_PRESENT="true"
    fi
done

for app in $applications
do
    create_new_app $app
done

#load database of "previous"
if [ $PROJECT_NAME == "latest" ]
then
    if test -f ../previous/db.sqlite3;
    then
            
        if [ $VERBOSE == 0 ] 
        then
            echo "load previous database"
        fi
        cd ..
        #copy to backup name and replace newest
        cp previous/db.sqlite3 latest/db.sqlite3
        
        if [ $SAVE_IN_BETWEEN_RUNS == 1 ]
        then 
            rm previous/db.sqlite3 #this can be commented out for versioning 
        fi
        cd latest

    else
        #setup some things for new empty database
        if [ $VERBOSE == 0 ] 
        then
            echo "Running migrations for empty database of $PROJECT_NAME"
            echo
        fi
        python3 manage.py makemigrations
        python3 manage.py migrate

        #Create a superuser for managing database
        if [ $VERBOSE == 0 ] 
        then
            echo "creating superuser for $PROJECT_NAME"
        fi
        DJANGO_SUPERUSER_PASSWORD="admin" python3 manage.py createsuperuser --noinput --username admin --email admin@gmail.com

        #build standard database operations and execute them
        #maybe easier ways to do this
        cd ../../
        cd generation_scripts/
        
        if [ $VERBOSE == 0 ] 
        then
            echo "generating database operations: ./generate_database_operations.py $PROJECT_NAME"
        fi

        python3 ./generate_database_operations.py $PROJECT_NAME
        cd ../
        cd generated_projects/$PROJECT_NAME
        
        if [ $VERBOSE == 0 ] 
        then
            echo "running operations: database_operations.py"
        fi

        python3 manage.py shell -c "with open(\"database_operations.py\") as file: exec(file.read())"

    fi
fi


if [ $VERBOSE == 0 ] 
then
    echo "Running migrations for $PROJECT_NAME"
    echo
fi

python3 manage.py makemigrations
python3 manage.py migrate

echo "Running app $PROJECT_NAME"
python3 manage.py runserver 127.0.0.1:$PORT
