#!/bin/bash
set -euxo pipefail

#=================================================================================
# To use: call the script with first argument being the path to source code and metadata, 
# second argument being the name of the project. 
# Example: . create_matlab_service.sh /home/zhuang/Downloads/myproject/ demo
#=================================================================================

export SRCDIR=$(echo $1 | sed 's![^/]$!&/!')
echo $SRCDIR

python3 -m venv .venv
source .venv/bin/activate
pip install cookiecutter
pip install PyYAML

#=================================================================================
# create a new service with added context
#=================================================================================
python3 create_cookie.py $SRCDIR $2

#=================================================================================
# compile the matlab code if needed
#=================================================================================
echo "Does this matlab code need to be compiled or is it already compiled with Matlab 2019b? "
select yn in "needs to be compiled" "already compiled"; do
    case $yn in

        "needs to be compiled" )
        # check that an entrypoint exists, default name main.m
        echo "searching for ${SRCDIR}main.m"
        if [[ -f "${SRCDIR}main.m" ]]
        then
            echo "You have a main.m - you can compile this code!"
        else
            echo "No main.m file in your source code - you cannot compile!"
            return 3
        fi
        # compile to the src dir of the cookie by default
        read -p "Where should the code be compiled to [$2/src/$2]: " BUILDDIR
        BUILDDIR=${BUILDDIR:-$2/src/$2}
        mkdir -p "$BUILDDIR"
        echo "compiling matlab code into $BUILDDIR"
        mcc -m ${SRCDIR}main -d "$BUILDDIR" -o $2
        export COMPILEDSH=run_$2.sh
        echo "shell script to run the matlab executable is: $COMPILEDSH"
        break;;

        "already compiled" ) 
        read -p "What is the name of the shell script? [run_$2.sh]: " COMPILEDSH
        COMPILEDSH=${COMPILEDSH:-run_$2.sh}
        echo "shell script to run the matlab executable is: $COMPILEDSH"
        cp -a $1/. $2/src/$2/
        break;; 

        *) 
        echo "Answer '1' or '2'" ;;
    esac
done

#=================================================================================
# in the new service directory, make the virtual environment and build the cookie
#=================================================================================
make -C $2 .venv
make -C $2 devenv
source $2/.venv/bin/activate
make -C $2 build

# copy submission data into the src directory
cp $SRCDIR* $2/src/$2


#=================================================================================
# edit files in docker and service.cli 
#=================================================================================
python3 customize_cookie.py $SRCDIR $2
chmod +x "$2/service.cli/execute.sh"

#=================================================================================
# build and run container
#=================================================================================
make -C $2 build
make -C $2 up

rm "$2/docker/ubuntu/Dockerfile_copy"
rm "$2/metadata/metadata_copy.yml"
rm "$2/service.cli/execute_copy.sh"

# run unit and integration tests
make -C $2 tests
deactivate

