import yaml
import sys
import json
import pprint
from pathlib import Path
import os


sourcepath = str(sys.argv[1])
project_name = str(sys.argv[2])


#=======================================================================
# Edit metadata file
#=======================================================================
accepted_datatypes = [
    "number",
    "boolean",
    "data:*/*",
    "data:text/*",
    "data:[image/jpeg,image/png]",
    "data:application/csv",
    "data:application/json",
    "data:application/json;schema=https://my-schema/not/really/schema.json",
    "data:application/vnd.ms-excel",
    "data:text/plain",
    "data:application/hdf5"
    ]


# read submitted metadata
submitted_meta = Path(sourcepath+'sampledat.json')
with submitted_meta .open('r') as fp:
    submitted_dict  = json.load(fp) 
model_inputs = submitted_dict['serviceInterface']['inputs']
num_inputs = len(model_inputs) 
model_outputs = submitted_dict['serviceInterface']['outputs']
num_outputs = len(model_outputs) 


# get metadata file of the cookie
metadata_file = Path(project_name + "/metadata/metadata_copy.yml")
with metadata_file.open('r') as fp:
    metadata_dict = yaml.safe_load(fp)

# replace default INPUT fields in metadata.yml with values from the submitted meetadata
input_keymap = {}
metadata_dict['inputs'] = {}
input_dict={}

for i in range(num_inputs):    

    keyname = model_inputs[i]['name']

    # make sure that the data type given is acceptable
    datatype = model_inputs[i]['type'].lower()
    while datatype not in accepted_datatypes:
        if datatype == 'list':
            print(pprint.pformat(accepted_datatypes))
        else:
            print("\nFor " + model_inputs[i]['label'] + " : \n" + pprint.pformat(model_inputs[i]))
        datatype = input("The datatype '" + datatype + 
        "' is not in the list of valid types. Please enter replacement or 'list' for list of valid types: ")

    metadata_dict['inputs'][keyname] = {
        'displayOrder': i+1,
        'label': model_inputs[i]['label'],
        'description': model_inputs[i]['description'],
        'type': datatype,
        'defaultValue': model_inputs[i]['defaultValue']
    }

    # fill in file mapping if necessary
    if datatype == 'data:*/*' or 'data:application' in datatype:
        answer = ''
        while answer != 'y':
            inputfile_name = input("\nPlease enter the filename for " + pprint.pformat(model_inputs[i]) 
            + "\nhere [" + model_inputs[i]['defaultValue'] + "]: ") or model_inputs[i]['defaultValue']
            answer = input("Validation input file for " + model_inputs[i]['label'] + " will be '" + inputfile_name + "' ok? (y/n): ") 
            metadata_dict['inputs'][keyname].update({'fileToKeyMap': {inputfile_name : model_inputs[i]["name"] }})
        try:
            os.replace(project_name + "/src/" + project_name + "/" + inputfile_name, project_name + "/validation/input/" + inputfile_name)
        except:
            print("File cannot be moved to validation folder")
            quit()
    elif datatype == 'number':
        default_number = float(metadata_dict["inputs"][keyname]["defaultValue"])
        input_dict.update({keyname: default_number})
    else:
        input_dict.update({keyname: metadata_dict["inputs"][keyname]["defaultValue"]})

# replace default OUTPUT fields in metadata.yml with values from the submitted meetadata
output_keymap = {}
metadata_dict['outputs'] = {}
for i in range(num_outputs):    

    keyname = model_outputs[i]['name']

    # make sure that the data type given is acceptable
    datatype = model_outputs[i]['type'].lower()
    while datatype not in accepted_datatypes:
        if datatype == 'list':
            print(pprint.pformat(accepted_datatypes))
        else:
            print("\nFor " + model_outputs[i]['label'] + " : \n" + pprint.pformat(model_outputs[i]))
        datatype = input("The datatype '" + datatype + 
        "' is not in the list of valid types. Please enter replacement or 'list' for list of valid types: ")

    metadata_dict['outputs'][keyname] = {
        'displayOrder': i+1,
        'label': model_outputs[i]['label'],
        'description': model_outputs[i]['description'],
        'type': datatype
    }

    # fill in file mapping if necessary
    if datatype == 'data:*/*' or 'data:application' in datatype:
        answer = ''
        while answer != 'y':
            outputfile_name = input("\nPlease enter the filename for " + pprint.pformat(model_outputs[i]) 
            + "\nhere [" + model_outputs[i]['validationFile'] + "]: ") or model_outputs[i]['validationFile']
            answer = input("Validation output file for " + model_outputs[i]['label'] + " will be '" + outputfile_name + "' ok? (y/n): ") 
            metadata_dict['outputs'][keyname].update({'fileToKeyMap': {outputfile_name : model_outputs[i]["name"] }})
        try:
            os.replace(project_name + "/src/" + project_name + "/" + outputfile_name, project_name + "/validation/output/" + outputfile_name)
        except:
            print("file cannot be moved to validation folder")
            quit()

# write to metadata file
metadata_file_edited = Path(project_name+'/metadata/metadata.yml')
with metadata_file_edited.open('w') as fp:
    yaml.safe_dump(metadata_dict, fp, default_style=None, default_flow_style=False)

#=======================================================================
# write validation input file for non-file inputs
#=======================================================================
inputvalidation_file = Path(project_name+"/validation/input/inputs.json")
if len(input_dict)>0: 
    with inputvalidation_file.open("w") as fpin:
        json.dump(input_dict, fpin, indent=4)
else:
    if os.path.exists(inputvalidation_file):
        os.remove(inputvalidation_file)

#=======================================================================
# edit the Dockerfile
#=======================================================================

Docker_file = Path(project_name+'/docker/ubuntu/Dockerfile_copy')
Docker_fileout = Path(project_name+'/docker/ubuntu/Dockerfile')

# additional text to install dependencies
addtext = """
# make sure that this is the version of Matlab used to compile!!!
ENV MATLAB_VERSION R2019b 

RUN mkdir -p /redist
COPY redist/MATLAB_Runtime_R2019b_Update_4_glnxa64.zip /redist
WORKDIR /redist

RUN unzip MATLAB_Runtime_R2019b_Update_4_glnxa64.zip \
 && ./install -v -mode silent -agreeToLicense yes
RUN chown ${SC_USER_NAME}:${SC_USER_NAME} /usr/local/MATLAB/MATLAB_Runtime/v97/*

WORKDIR /home/${SC_USER_NAME}
RUN rm -rf /redist

"""

# make the changes in the Docker file
with Docker_file.open('r') as d_file:
    buf = d_file.readlines()

with Docker_fileout.open('w') as dout_file:
    for line in buf:
        # install unzip
        if line .__contains__("jq \\"):
            line = line + "\tunzip  xorg \\\n"
        # copy Matlab Runtime into image
        elif line .__contains__("copy docker bootup scripts"):
            line = addtext + line
        elif line .__contains__("RUN cp -R "): 
            line = "RUN cp -R src/" + project_name + "/* /build/bin\n\n"
        dummyvar = dout_file.write(line)


#=======================================================================
# edit execute.sh
#=======================================================================

execute_file = Path(project_name+'/service.cli/execute_copy.sh')
execute_fileout = Path(project_name+'/service.cli/execute.sh')

answer = ''
while answer != 'y':
    input_string = input("\nPlease enter the ordered list of inputs to the compiled matlab program: ")
    input_list = [x.strip() for x in input_string.split(',')]
    answer = input("Ordered list of inputs will be  " + str(input_list) + "  ok? (y/n): ") 

executetext =("\necho \"Starting simulation...\"\n/home/scu/" + project_name + "/run_" 
+ project_name + ".sh /usr/local/MATLAB/MATLAB_Runtime/v97/ " 
+ '} '.join("${{{0}".format(x.upper()) for x in input_list) + '}' 
+ "\necho \"Simulation finished!\"\n\ncp *.csv $OUTPUT_FOLDER/\ncp *.mat $OUTPUT_FOLDER/")


with execute_file.open('r') as e_file:
    ebuf = e_file.readlines()

lastline = len(ebuf)
with execute_fileout.open('w') as eout_file:
    for index, line in enumerate(ebuf):
        if line .__contains__('# For example: input_1 -> $INPUT_1'):
            line = line + executetext
            lastline = index
        if index <= lastline:
            dummyvar = eout_file.write(line)

# #=======================================================================
# # edit README.md
# #=======================================================================
# readme_file = Path(project_name+'/README.md')

# version_text = """ Two versions:

# - integration version (e.g. [src/opencorservice_demo/VERSION_INTEGRATION]) is updated with ``make version-integration-*``
# - service version (e.g. [src/opencorservice_demo/VERSION]) is updated with ``make version-service-*``
# """

# with readme_file.open('r') as r_file:
#     rbuf = r_file.readlines()

# lastline = len(rbuf)
# with readme_file.open('w') as rout_file:
#     for index, line in enumerate(rbuf):
#         if line .__contains__('## Workflow'):
#             line = version_text
#             lastline = index
#         if index <= lastline:
#             dummyvar = rout_file.write(line)

