#!/bin/bash
set -o pipefail
# To use: call the script with first argument being the path to source code and metadata, second argument being the name of the project. 
# Example: . create_opencor_service.sh /home/zhuang/Downloads/myproject/ demo

# open model and make sure that works
python3 -m venv .venv
source .venv/bin/activate
pip install cookiecutter
pip install PyYAML

# create a new service with added context
python3 create_cookie.py $1 $2

# in the new service directory, make the virtual environment and build the cookie
make -C $2 .venv
make -C $2 devenv
source "$2/.venv/bin/activate"
make -C $2 build

# copy the model and the python script to run the model into src directory
cp -R $1 "$2/src/$2/"
# cp run_model.py "$2/src/$2/"

# # edit files in docker and service.cli 
# python3 customize_cookie.py "${1##*/}" $2
# chmod +x "$2/service.cli/execute.sh"

# build and run container, copy validation output to validation folder
# make -C $2 build
# make -C $2 up
# cp "$2/.tmp/output/outputs.csv" "$2/validation/output/"
# rm "$2/validation/output/outputs.json"
# rm "$2/docker/ubuntu/Dockerfile_copy"
# rm "$2/metadata/metadata_copy.yml"
# rm "$2/service.cli/execute_copy.sh"

# # run unit and integration tests
# make -C $2 tests
# deactivate


# # # #=============================== ready to push? takes care of CI =======================================


# read -p "Where is the osparc-services directory cloned locally [../osparc-services/]: " SERVICES_DIR
# SERVICES_DIR=${SERVICES_DIR:-../osparc-services}
# echo $SERVICES_DIR
# read -p "What name should this folder have on the github repository [oc-guytonmodel]: " FOLDER_NAME
# FOLDER_NAME=${FOLDER_NAME:-oc-guytonmodel}
# echo $FOLDER_NAME

# echo "About to create new version of your service! Are you sure you want this? "
# select yn in "yes" "no"; do
#     case $yn in
#         yes )
#         source "$2/.venv/bin/activate"
#         pip install bump2version
#         make -C $2 version-service-major
#         make -C $2 build
#         make -C $2 up
#         deactivate
#         break;;
#         no ) 
#         return;; 
#         *) 
#         echo "Answer '1' or '2'" ;;
#     esac
# done


# cp "$2/.github/workflows/github-ci.yml" "$2/.github/workflows/github-ci_copy.yml" 
# python3 edit_ciyaml.py $2 ${FOLDER_NAME}
# rm "$2/.github/workflows/github-ci_copy.yml" 

# cp -R "$2/." "$SERVICES_DIR/services/$FOLDER_NAME"
# mv "$SERVICES_DIR/services/$FOLDER_NAME/.github/workflows/github-ci.yml" "$SERVICES_DIR/.github/workflows/$FOLDER_NAME.yml"
