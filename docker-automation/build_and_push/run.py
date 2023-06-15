"""
-------------------------------------------------
MHub - local automation for docker builds
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

max_cores = os.cpu_count()

## --------------------------------

# for now, build only
def run_core(image_dict):
    try:
        image_tag = utils.build_docker_image(image_dict)    
    except Exception as e:
        print("Error building image %s"%image_dict["name"])
        print(e)
        return None

## --------------------------------

def dryrun_core(image_dict):
    print("docker build")
    pp.pprint(image_dict)
    print("")

## --------------------------------

def main():

    # TO-DO: implement ands set up logging
    # https://stackoverflow.com/questions/7507825/where-is-a-complete-example-of-logging-config-dictconfig
    #logging.config.dictConfig(config['logging'])
    #logger = logging.getLogger(__name__)

    # parse command line arguments
    parser = argparse.ArgumentParser(description='MHub - local automation for docker builds')
    #parser.add_argument('-l', '--logging', action='store_true', help='enable logging')
    parser.add_argument('--verbose', action='store_true', help='enable verbose mode')
    parser.add_argument('--dryrun', action='store_true', help='execute in dry run mode')
    parser.add_argument('--ncores', action='store', type=int, default=4,
                        help='number of cores to execute on (max is %g)'%max_cores)
    parser.add_argument('--config', action='store', help='path to config file', required=True)
    parser.add_argument('--push', action='store_true', help='whether to push the images or not')
    parser.add_argument('--updated-only', action='store_true', help='whether to build only the updated images')

    args = parser.parse_args()

    # parse yaml config file
    with open(args.config, 'r') as f:
        config_dict = yaml.safe_load(f)
    
    use_multiprocessing = True if args.ncores > 1 else False
    
    # get hash for the current commit using git
    commit_hash = utils.get_git_hash(path_to_repo = config_dict["github"]["repository_folder"])
    remote_hash = utils.get_git_hash_remote(repo_url = config_dict["github"]["repository_url"])

    if args.verbose:
        print("Commit hash:", commit_hash)
        print("Remote hash:", remote_hash, "\n")

    # if the two hashes are different, pull the latest changes
    if commit_hash != remote_hash:
        if args.dryrun:
            print("git pull %s \n"%config_dict["github"]["repository_folder"])
        else:
            print(utils.git_pull(path_to_repo = config_dict["github"]["repository_folder"]))

    # get the list of changed folders
    updated_folders = utils.get_list_of_updated_folders(path_to_repo = config_dict["github"]["repository_folder"])

    image_list = list()

    # populate a list of images to build (formatted in dictionaries)
    for image in config_dict["images"]:
        
        # get the image dictionary
        image_dict = config_dict["images"][image]

        # quick workaround to avoid passing the config dictionary to the `build_docker_image` function
        image_dict["repository_folder"] = config_dict["github"]["repository_folder"]
        image_dict["dockerhub_username"] = config_dict["dockerhub"]["username"]

        skip_build = False
        # if the option to build only the updated images is enabled, check if the image has changed
        if args.updated_only:

            # if at least one file in the model directory was updated, build the image - otherwise continue
            for folder in updated_folders:
                if not image_dict["name"] in folder:
                    skip_build = True

        if skip_build: continue

        image_list.append(image_dict)


    # for every image in the config file, build the docker image and push it to the registry
    if use_multiprocessing:
        pool = multiprocessing.Pool(processes = args.ncores)

        if args.dryrun:
            print("This will run in parallel, on %g cores.\n"%(args.ncores))
            for _ in tqdm.tqdm(pool.imap_unordered(dryrun_core, image_list), total = len(image_list)):
                pass
        else:
            print("\nRunning in parallel on %g cores.\n"%(args.ncores))
            for _ in tqdm.tqdm(pool.imap_unordered(run_core, image_list), total = len(image_list)):
                pass

    else:
        if args.dryrun:
            print("This will run on a single core.\n")
            for image_dict in image_list:
                dryrun_core(image_dict)
        else:
            print("Running on a single core.\n")
            for image_dict in image_list:
                run_core(image_dict)

if __name__ == '__main__':
    main()