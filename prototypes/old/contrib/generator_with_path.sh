#!/bin/bash

if [ $# != 2 ]
then
    echo "Usage: ./generator_with_path.sh <PATH_TO_JSON> <PROJECT_NAME>"
    exit 1
fi

JSON_PATH=$1
PROJECT_NAME=$2

rm tests/runtime.json
cp $JSON_PATH tests/runtime.json
./generator.sh $PROJECT_NAME