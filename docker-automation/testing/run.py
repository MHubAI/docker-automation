"""
-------------------------------------------------
MHub - automated testing for MHub containers
-------------------------------------------------
-------------------------------------------------
Author: Dennis Bontempi
Email:  dbontempi@bwh.harvard.edu
-------------------------------------------------
"""

import os
import sys
import time
import tqdm

import argparse
import subprocess

#import logging
#import logging.config

import yaml
import pprint

pp = pprint.PrettyPrinter(indent=2)

import utils

# constants definition
INPUT_BASE_DIR = "/home/mhubai/mhubai_testing/input_data"
OUTPUT_BASE_DIR = "/home/mhubai/mhubai_testing/output_data"
REFERENCE_BASE_DIR = "/home/mhubai/mhubai_testing/reference_data"

## --------------------------------

def run_core(test_dict):
    """
     The core function should run the following operations:
        - run the processing using the MHub container
        - run some basic checks on the output
        - compare the output to the expected output
    """

    # Run the processing using the MHub container
    try:
        docker_command = test_dict["docker_command"]
        utils.run_mhub_model(docker_command)    
    except Exception as e:
        print("Error running image %s"%test_dict["image_to_test"])
        print(e)
        return None

    # compare the tree of the output directory to the reference
    try:       
        same_tree = utils.compare_results_dir(test_dict)    
    except Exception as e:
        print("Error comparing directory trees for image %s"%test_dict["image_to_test"])
        print(e)
        same_tree = False
        return None

    if same_tree:
        print(">>> The directory tree of the output matches the expected output")
    else:
        print("WARNING: The directory tree of the output DOES NOT match the expected output")

    try:
        are_files_equal = utils.compare_results_file(test_dict)
    except Exception as e:
        print("Error comparing results for image %s"%test_dict["image_to_test"])
        print(e)
        are_files_equal = False
        return None

    with open(test_dict["output_file"], "a") as f:
        f.write("%s,%s,%s,%s,%s\n"%(
            test_dict["image_to_test"],
            test_dict["workflow_name"],
            test_dict["data_sample"],
            same_tree,
            are_files_equal
            ))
    
## --------------------------------

def dryrun_core(test_dict):
    print("")
    print("- Docker command to be executed:")
    print(" ".join(test_dict["docker_command"]))

    print("- Output dir to be generated:")
    print(test_dict["pipeline_output"])

    print("- Reference dir to be compared to:")
    print(test_dict["pipeline_reference"])

## --------------------------------

def main():

    # TO-DO: implement ands set up logging
    # https://stackoverflow.com/questions/7507825/where-is-a-complete-example-of-logging-config-dictconfig
    #logging.config.dictConfig(config['logging'])
    #logger = logging.getLogger(__name__)

    # parse command line arguments
    parser = argparse.ArgumentParser(description='MHub - automated testing for MHub containers')
    #parser.add_argument('-l', '--logging', action='store_true', help='enable logging')
    parser.add_argument('--verbose', action='store_true', help='enable verbose mode')
    # FIXME: past this directly in the docker command?
    parser.add_argument('--gpu', action='store_true', help='enable verbose mode')
    parser.add_argument('--dryrun', action='store_true', help='execute in dry run mode')
    parser.add_argument('--config', action='store', help='path to config file', required=True)
    parser.add_argument('--outpath', action='store', help='path to the folder storing the output file', required=True)


    args = parser.parse_args()
    
    # split the config file name from the path
    config_name = os.path.basename(args.config).split(".yml")[0]
    csv_fn = config_name + ".csv"
    csv_path = os.path.join(args.outpath, csv_fn)

    # parse yaml config file
    with open(args.config, 'r') as f:
        config_dict = yaml.safe_load(f)
    
    # if the output file is already found, delete it
    if os.path.isfile(csv_path):
        os.remove(csv_path)

    # initialize the output file
    with open(csv_path, "a") as f:
        f.write("image,workflow,data_sample,dirtree_match,output_match\n")

    # dict of versions of the MHub image to test
    mhub_images_dict = config_dict["images"]

    workflows_list = list(config_dict["workflows"].keys())

    test_list = list()
    image_name_list = list()

    # FIXME: handle all of the following in a dedicated function?
    for mhub_image in mhub_images_dict.keys():

        image_dict = config_dict["images"][mhub_image]
            
        for workflow_name in workflows_list:

            test_dict = dict()

            test_dict["output_file"] = csv_path
            test_dict["image_to_test"] = "mhubai/" + image_dict["name"] + ":" + image_dict["version"]

            if test_dict["image_to_test"] not in image_name_list:
                image_name_list.append(test_dict["image_to_test"])        

            workflow_dict = config_dict["workflows"][workflow_name]

            test_dict["workflow_name"] = workflow_name
            test_dict["data_sample"] = workflow_dict["data_sample"]
            test_dict["config"] = workflow_dict["config"]

            # build the docker command to run
            test_dict["docker_command"] = utils.get_docker_command(
                image_to_test = test_dict["image_to_test"],
                workflow_name = workflow_name,
                workflow_dict = workflow_dict,
                input_base_dir = INPUT_BASE_DIR,
                output_base_dir = OUTPUT_BASE_DIR,
                use_gpu = args.gpu
                )

            test_dict["pipeline_output"] = os.path.join(
                OUTPUT_BASE_DIR,
                image_dict["name"],
                workflow_dict["data_sample"],
                workflow_name)

            test_dict["pipeline_reference"] = os.path.join(
                REFERENCE_BASE_DIR,
                image_dict["name"],
                workflow_dict["data_sample"],
                workflow_name)

            # append to the list of task to run (single proc.)
            test_list.append(test_dict)

    if args.verbose:
        print("Found %g image(s) to test running %g workflow(s)"%(len(image_name_list), len(workflows_list)))
        
        for test_dict in test_list:
            print("- %s - %s"%(test_dict["image_to_test"], test_dict["workflow_name"]))

    for idx, test_dict in  enumerate(test_list):

        if args.verbose:
            print("\nRunning test %g/%g"%(idx+1, len(test_list)))
            print("MHub image: %s"%test_dict["image_to_test"])
            print("Workflow: %s"%test_dict["workflow_name"])
            print("Sample data: %s"%test_dict["data_sample"])
            print("Using GPU") if args.gpu else print("Using CPU")

        if args.dryrun:
            dryrun_core(test_dict)
        else:
            run_core(test_dict)

if __name__ == '__main__':
    main()