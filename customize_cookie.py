import yaml
import sys
import json
import pprint
from pathlib import Path
import os
from shutil import copyfile

sourcepath = str(sys.argv[1])
project_name = str(sys.argv[2])
copyfile(project_name + "/docker/ubuntu/Dockerfile", project_name + "/docker/ubuntu/Dockerfile_copy")
copyfile(project_name + "/service.cli/execute.sh", project_name + "/service.cli/execute_copy.sh")
copyfile(project_name+ "/metadata/metadata.yml", project_name + "/metadata/metadata_copy.yml")

#=======================================================================
# Edit metadata file
#=======================================================================
accepted_datatypes = [
    "number",
    "integer",
    "boolean",
    "data:*/*",
    "data:text/*",
    "data:image/jpeg",
    "data:image/png",
    "data:application/csv",
    "data:application/json",
    "data:application/json;schema=https://my-schema/not/really/schema.json",
    "data:application/vnd.ms-excel",
    "data:text/plain",
    "data:application/hdf5"
    ]

file_datatypes = [
    "data:*/*",
    "data:image",
    "data:application",
    "data:text"
]

def xstr(s):
    return 'null' if s is None else str(s)

def fill_meta_dict(modeldict, numentries, iostr):
    json_dict = {}
    filled_meta_dict = {}
    keymap = {}

    for i in range(numentries):    
        keyname = iostr + str(i).zfill(3)
        keymap[keyname] = modeldict[i]['name']


        # make sure that the data type given is acceptable
        datatype = modeldict[i]['type'].lower()
        while datatype not in accepted_datatypes:
            if datatype == 'list':
                print(pprint.pformat(accepted_datatypes))
            else:
                print("\nFor \n" + modeldict[i]['label'] + " : \n" + pprint.pformat(modeldict[i]))
            datatype = input("The datatype '" + datatype + 
            "' is not in the list of valid types. Please enter replacement or 'list' for list of valid types: ")

        filled_meta_dict[keyname] = {
            'displayOrder': i+1,
            'label': modeldict[i]['label'],
            'description': modeldict[i]['description'],
            'type': datatype,
            'defaultValue': modeldict[i]['defaultValue']
        }
        if iostr .__contains__('out'):
            filled_meta_dict[keyname].pop('defaultValue', None)

        # fill in file mapping if necessary
        if any(ftype in datatype for ftype in file_datatypes):
            answer = ''
            while answer.lower() not in ['y', 'yes', 's']:
                file_name = input("\nPlease enter the filename for \n" + pprint.pformat(modeldict[i]) 
                + "\nhere [" + modeldict[i]['defaultValue'] + "]: ") or modeldict[i]['defaultValue']
                answer = input("Validation file for \n" + modeldict[i]['label'] + " will be '" + file_name + "' ok? (y/n) or 's' to skip this file: ") 
                filled_meta_dict[keyname].update({'fileToKeyMap': {file_name : keyname }})
            if answer.lower() in ['y', 'yes']:
                try:
                    if iostr .__contains__('out'):
                        os.replace(project_name + "/src/" + project_name + "/" + file_name, project_name + "/validation/output/" + file_name)
                    else:
                        os.replace(project_name + "/src/" + project_name + "/" + file_name, project_name + "/validation/input/" + file_name)
                except:
                    print("file " + filename + " cannot be moved to validation folder - make sure it exists in " + project_name + "/src")
                    quit()
        else:
            if 'out' not in iostr:
                try:
                    if datatype == 'number':
                        default_number = float(filled_meta_dict[keyname]['defaultValue'])
                        json_dict.update({keyname: default_number})
                    elif datatype == 'integer':
                        default_int = int(filled_meta_dict[keyname]['defaultValue'])
                        json_dict.update({keyname: default_int})
                    elif datatype == 'boolean':
                        default_bool = filled_meta_dict[keyname]['defaultValue'].capitalize()
                        json_dict.update({keyname: default_bool})
                    else:
                        json_dict.update({keyname: filled_meta_dict[keyname]['defaultValue']})
                except ValueError:
                    print("WARNING: Value of " + xstr(filled_meta_dict[keyname]['defaultValue']) + " could not be converted to " + datatype)
                    json_dict.update({keyname: filled_meta_dict[keyname]['defaultValue']})
                except:
                    print("WARNING: Problem with output value: " + xstr(filled_meta_dict[keyname]['defaultValue']) + " with datatype: " + datatype)
                    json_dict.update({keyname: filled_meta_dict[keyname]['defaultValue']})
    return filled_meta_dict, json_dict, keymap
        

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


# replace default OUTPUT fields in metadata.yml with values from the submitted meetadata
metadata_dict['inputs'], input_dict, input_keymap = fill_meta_dict(model_inputs, num_inputs, 'input_')

# replace default OUTPUT fields in metadata.yml with values from the submitted meetadata
metadata_dict['outputs'], output_dict, output_keymap = fill_meta_dict(model_outputs, num_outputs, 'output_')


# write to metadata file
metadata_file_edited = Path(project_name+'/metadata/metadata.yml')
with metadata_file_edited.open('w') as fp:
    yaml.safe_dump(metadata_dict, fp, default_style=None, default_flow_style=False)

# write input map to file
input_map_file = Path(project_name+"/src/" + project_name + "/input_keymap.json")
with input_map_file.open("w") as fp:
    json.dump(input_keymap, fp, indent=4)

output_map_file = Path(project_name+"/src/" + project_name + "/output_keymap.json")
with output_map_file.open("w") as fp:
    json.dump(output_keymap, fp, indent=4)

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

outputvalidation_file = Path(project_name+"/validation/output/outputs.json")
if len(output_dict)>0: 
    with outputvalidation_file.open("w") as fpin:
        json.dump(output_dict, fpin, indent=4)
else:
    if os.path.exists(outputvalidation_file):
        os.remove(outputvalidation_file)
        
#=======================================================================
# edit the Dockerfile
#=======================================================================

Docker_file = Path(project_name+'/docker/ubuntu/Dockerfile_copy')
Docker_fileout = Path(project_name+'/docker/ubuntu/Dockerfile')

# make the changes in the Docker file
with Docker_file.open('r') as d_file:
    buf = d_file.readlines()

with Docker_fileout.open('w') as dout_file:
    for line in buf:
        # use existing image with Matlab Runtime
        if line .__contains__("as base"):
            line = "FROM ${SC_CI_MASTER_REGISTRY:-masu.speag.com}/simcore/base-images/mat2019b_ubu1804:0.1.0 as base\n"
        # copy executable into docker image
        elif line .__contains__("RUN cp -R "): 
            line = "RUN cp -R src/" + project_name + "/* /build/bin\n\n"
        dummyvar = dout_file.write(line)


#=======================================================================
# edit execute.sh
#=======================================================================

execute_file = Path(project_name+'/service.cli/execute_copy.sh')
execute_fileout = Path(project_name+'/service.cli/execute.sh')

input_keys = []
answer = ''
while answer != 'y':
    input_string = input("\nPlease enter the ordered list of inputs to the compiled matlab program: ")
    input_list = [x.strip() for x in input_string.split(',')]
    answer = input("Ordered list of inputs will be  " + str(input_list) + "  ok? (y/n): ") 


for input_str in input_list:
    for key, value in input_keymap.items():
        if input_str not in input_keymap.values():
            print("ERROR: Input variable " + value + " was not found in input list: " + str(input_keymap.values()))
        elif str(input_str) == str(value):
            input_keys.append(key)

executetext =("\necho \"Starting simulation...\"\n/home/scu/" + project_name + "/run_" 
+ project_name + ".sh /usr/local/MATLAB/MATLAB_Runtime/v97/ " 
+ '} '.join("${{{0}".format(x.upper()) for x in input_keys) + '}' 
+ "\necho \"Simulation finished!\"\n\n")


with execute_file.open('r') as e_file:
    ebuf = e_file.readlines()

lastline = len(ebuf)
with execute_fileout.open('w') as eout_file:
    for index, line in enumerate(ebuf):
        if line .__contains__("# For example: input_1 -> $INPUT_1"):
            line = line + executetext
            lastline = index
        elif line .__contains__("cd "):
            line = "cd $OUTPUT_FOLDER/\n"
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

