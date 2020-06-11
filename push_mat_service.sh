

# # #=============================== ready to push? takes care of CI =======================================
# To use: call the script with first argument being the cellML or sedML path, second argument being the name of the project. 
# Example: . push_opencor_service.sh /home/zhuang/Downloads/guyton_antidiuretic_hormone_2008.cellml demo

read -p "Where is the osparc-services directory cloned locally [../osparc-services/]: " SERVICES_DIR
SERVICES_DIR=${SERVICES_DIR:-../osparc-services}
echo $SERVICES_DIR
read -p "What name should this folder have on the github repository [oc-guytonmodel]: " FOLDER_NAME
FOLDER_NAME=${FOLDER_NAME:-oc-guytonmodel}
echo $FOLDER_NAME


echo "About to create new version of your service! The repo must also be CLEAN! Are you sure you want this? "
select yn in "yes" "no"; do
    case $yn in
        yes )
        if [[ `git status --porcelain` ]]; then
            echo "uncommitted changes detected - should not try to bump version because it will fail."
            return
        else
            echo "no uncommitted changes - ok to proceed"
        fi
        source "$2/.venv/bin/activate"
        pip install bump2version
        make -C $2 version-service-major
        make -C $2 build
        make -C $2 up
        deactivate
        break;;
        no ) 
        return;; 
        *) 
        echo "Answer '1' or '2'" ;;
    esac
done


cp "$2/.github/workflows/github-ci.yml" "$2/.github/workflows/github-ci_copy.yml" 
python3 edit_ciyaml.py $2 ${FOLDER_NAME}
rm "$2/.github/workflows/github-ci_copy.yml" 

cp -R "$2/." "$SERVICES_DIR/services/$FOLDER_NAME"
mv "$SERVICES_DIR/services/$FOLDER_NAME/.github/workflows/github-ci.yml" "$SERVICES_DIR/.github/workflows/$FOLDER_NAME.yml"
