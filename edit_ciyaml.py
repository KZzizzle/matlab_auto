import yaml
import sys
from pathlib import Path

project_name = str(sys.argv[1])
folder_name = str(sys.argv[2])

ci_file = Path(project_name + "/.github/workflows/github-ci_copy.yml")
ci_file_edited = Path(project_name + "/.github/workflows/github-ci.yml")

workingdir_text = "        working-directory: services/" + folder_name
paths_text = """     paths:
      - \"services/""" + folder_name + """/**\"
      - \"!**.md\""""

with ci_file.open("r") as c_file:
    ci_buf = c_file.readlines()

with ci_file_edited.open("w") as cout_file:
    for line in ci_buf:
        if ((line .__contains__("name: set dev environs") or line .__contains__("name: get current image") or
         line .__contains__("name: build") or line .__contains__("name: test") or line .__contains__("name: deploy")) 
         and "name: building" not in line):
            line = line + workingdir_text + "\n"
        elif (line .__contains__("push:") or line .__contains__("pull_request:")):
            line = line + paths_text + "\n"
        dummyvar = cout_file.write(line)
