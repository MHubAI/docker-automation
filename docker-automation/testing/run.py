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
        print("Error running image %s"%test_dict["name"])
        print(e)
        return None

    # run some basic checks on the output
    try:       
        utils.check_pipeline_run(test_dict)    
    except Exception as e:
        print("Error checking pipeline results for image %s"%test_dict["name"])
        print(e)
        return None

    # compare the output to the expected output
    try:       
        utils.compare_results(test_dict)    
    except Exception as e:
        print("Error comparing results for image %s"%test_dict["name"])
        print(e)
        return None

## --------------------------------

def dryrun_core(test_dict):
    print("- Docker command to be executed:")
    print(" ".join(test_dict["docker_command"]))

    print("- Ouput file to be generated:")
    print(test_dict["pipeline_output"])

    print("- Ground truth file to be compared to:")
    print(test_dict["ground_truth_output"])

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

    test_sample_list = list()
    test_sample_list = [x for x in list(config_dict.keys()) if "sample" in x]

    # FIXME: parse this from command line or read all of the workflows?
    workflows_list = ["dicom"]

    test_list = list()

    # FIXME: handle all of the following in a dedicated function?
    for mhub_image in mhub_images_dict.keys():

        test_dict = dict()
        image_dict = config_dict["images"][mhub_image]

        test_dict["image_to_test"] = "mhubai/" + image_dict["name"] + ":" + image_dict["version"]

        for test_sample in test_sample_list:

            test_sample_dict = config_dict[test_sample]
            test_dict["sample_data_name"] = test_sample_dict["name"]
            
            for workflow_name in workflows_list:

                workflow_dict = test_sample_dict["workflow"][workflow_name]

                # build the docker command to run
                test_dict["docker_command"] = utils.get_docker_command(
                    image_to_test = test_dict["image_to_test"],
                    workflow_dict = workflow_dict,
                    use_gpu = args.gpu
                    )

                test_dict["pipeline_output"] = os.path.join(
                    workflow_dict["output_data"]["base_folder"],
                    workflow_dict["output_data"]["folder_name"],
                    workflow_dict["output_data"]["file_name"]
                )

                test_dict["ground_truth_output"] = os.path.join(
                    workflow_dict["ground_truth"]["base_folder"],
                    workflow_dict["ground_truth"]["folder_name"],
                    workflow_dict["ground_truth"]["file_name"]
                )

                # append to the list of task to run (single proc./multi proc.)
                test_list.append(test_dict)

    if args.verbose:
        print("Found %g image(s) to test on %g sample(s)"%(len(test_list), len(test_sample_list)))

    # for every image in the config file, build the docker image and push it to the registry
    if use_multiprocessing:
        pool = multiprocessing.Pool(processes = args.ncores)

        if args.dryrun:
            print("This will run in parallel, on %g cores.\n"%(args.ncores))
            for _ in tqdm.tqdm(pool.imap_unordered(dryrun_core, test_list), total = len(test_list)):
                pass
        else:
            print("\nRunning in parallel on %g cores.\n"%(args.ncores))
            for _ in tqdm.tqdm(pool.imap_unordered(run_core, test_list), total = len(test_list)):
                pass

    else:
        print("Running on a single core.\n")
        for idx, test_dict in  enumerate(test_list):

            if args.verbose:
                print("Running test %g/%g"%(idx+1, len(test_list)))
                print("MHub image: %s"%test_dict["image_to_test"])
                print("Sample data: %s"%test_dict["sample_data_name"])
                print("Using GPU") if args.gpu else print("Using CPU")

            if args.dryrun:
                dryrun_core(test_dict)
            else:
                run_core(test_dict)

            if args.verbose: print("... Done \n")

if __name__ == '__main__':
    main()