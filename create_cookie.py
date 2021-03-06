import os
from cookiecutter.main import cookiecutter
from shutil import copyfile
import sys
import json
from pathlib import Path

def main(sourcepath, servicename):
        
    # the default file sent via email is named 'metadata.json'
    metadata_file = Path(sourcepath+"metadata.json")

    try:
        with metadata_file.open("r") as fp:
            metadata_dict = json.load(fp)
        if "inputs" in metadata_dict["serviceInterface"]:
            num_inputs = len(metadata_dict["serviceInterface"]["inputs"])
        else:
            num_inputs = 0

        if "outputs" in metadata_dict["serviceInterface"]:    
            num_outputs = len(metadata_dict["serviceInterface"]["outputs"])
        else:
            num_outputs = 0

    except:
        print("Could not open metadata file " + sourcepath + "metadata.json")
        return 3

    try:
        cookiecutter("https://github.com/ITISFoundation/cookiecutter-osparc-service", extra_context={
            "docker_base":"ubuntu:18.04",
            "number_of_inputs": num_inputs, 
            "author_affiliation": "IT'IS Foundation",
            "project_name": servicename,
            "author_name": "Katie Zhuang",
            "author_email": "zhuang@itis.swiss",
            "project_type": "computational",
            "docker_base": "custom:special-image",
            "number_of_outputs": num_outputs,
            "git_username": "KZzizzle"
        })
    except:
        print("Could not create the cookie")
        return 2

    dockerfiledir = [f.path for f in os.scandir(Path(servicename + "/docker")) if f.is_dir()]
    copyfile(dockerfiledir[0] + "/Dockerfile", dockerfiledir[0] + "/Dockerfile_copy")
    copyfile(servicename + "/service.cli/execute.sh", servicename + "/service.cli/execute_copy.sh")
    copyfile(servicename + "/metadata/metadata.yml", servicename + "/metadata/metadata_copy.yml")

    return 0

def usage():
    print("Usage: create_cookie.py <path> <str> ")
    print("  where <path> is the path to folder containing source code and  <str> is the name of the service you will create.")


if __name__ == "__main__":
    args = sys.argv
    args.pop(0)  # Script name.

    try:
        sourcepath = str(args.pop(0))
        servicename = str(args.pop(0))
    except ValueError:
        print("ValueError in inputs")
        usage()
        sys.exit(2)
    except IndexError:
        print("indexError in inputs")
        usage()
        sys.exit(2)

    rc = main(sourcepath, servicename)
    sys.exit(rc)