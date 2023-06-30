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
import multiprocessing

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

# FIXME: for now, single thread/process only
#max_cores = os.cpu_count()
max_cores = 1

## --------------------------------

# FIXME: for now, single thread/process only
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
        print("Error comparing results for image %s"%test_dict["image_to_test"])
        print(e)
        return None

    if same_tree:
        print(">>> The directory tree of the output matches the expected output")
    else:
        print("WARNING: The directory tree of the output DOES NOT match the expected output")
        return

    # FIXME: this needs to become a compare_results_file that, based on the extension, calls the appropriate function
    utils.compare_results_file(test_dict)


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
    parser.add_argument('--ncores', action='store', type=int, default=4,
                        help='number of cores to execute on (max is %g)'%max_cores)
    parser.add_argument('--config', action='store', help='path to config file', required=True)

    # FIXME: what's the best way to handle this?
    # FIXME: for now, support only DICOM to DICOM testing
    #parser.add_argument('--test_dicom', action='store_true', help='test the DICOM to DICOM worflow')
    #parser.add_argument('--test_slicer', action='store_true', help='test the NRRD to NRRD 3DSlicer worflow')

    args = parser.parse_args()

    # parse yaml config file
    with open(args.config, 'r') as f:
        config_dict = yaml.safe_load(f)
    
    # FIXME: for now, single thread/process only
    #use_multiprocessing = True if args.ncores > 1 else False
    use_multiprocessing = False

    # dict of versions of the MHub image to test
    mhub_images_dict = config_dict["images"]

    workflows_list = list(config_dict["workflows"].keys())

    test_list = list()

    # FIXME: handle all of the following in a dedicated function?
    for mhub_image in mhub_images_dict.keys():

        image_dict = config_dict["images"][mhub_image]
            
        for workflow_name in workflows_list:

            test_dict = dict()
            test_dict["image_to_test"] = "mhubai/" + image_dict["name"] + ":" + image_dict["version"]
            
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

            # append to the list of task to run (single proc./multi proc.)
            test_list.append(test_dict)

    if args.verbose:
        print("Found %g image(s) to test running %g workflow(s)"%(len(test_list), len(workflows_list)))
        
        for test_dict in test_list:
            print("- %s - %s"%(test_dict["image_to_test"], test_dict["workflow_name"]))

    # for every image in the config file, build the docker image and push it to the registry
    if use_multiprocessing:
        pool = multiprocessing.Pool(processes = args.ncores)

        if args.dryrun:
            print("This will run in parallel, on %g cores.\n"%(args.ncores))
            for _ in tqdm.tqdm(pool.imap_unordered(dryrun_core, test_list), total = len(test_list)):
                pass
        else:
            print("Running in parallel on %g cores.\n"%(args.ncores))
            for _ in tqdm.tqdm(pool.imap_unordered(run_core, test_list), total = len(test_list)):
                pass

    else:
        print("Running on a single core.")
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