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
    parser.add_argument('--ncores', action='store', help='number of cores to execute on (max is %g)'%max_cores, 
                        type=int, default=4)
    parser.add_argument('--branch', action='store', help='name of the branch to build the images from',
                        type=str, default="main")
    parser.add_argument('--config', action='store', help='path to config file', required=True)

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

    image_list = list()

    # populate a list of images to build (formatted in dictionaries)
    for image in config_dict["images"]:
        
        # get the image dictionary
        image_dict = config_dict["images"][image]

        # quick workaround to avoid passing the config dictionary to the `build_docker_image` function
        image_dict["repository_folder"] = config_dict["github"]["repository_folder"]
        image_dict["dockerhub_username"] = config_dict["dockerhub"]["username"]

        # if a branch different from main is specified, append it to the image tag
        # furthermore, modify the Dockerfiles to pull the correct branch
        if args.branch != "main":
            image_dict["version"] = args.branch

            # modify the Dockerfile
            utils.modify_dockerfile(image_dict, branch = args.branch)

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

    
    # if a branch different from main is specified, revert the Dockerfiles to the original state
    # by running a git restore command
    if args.branch != "main":
        if args.verbose:
            print("git restore %s \n"%config_dict["github"]["repository_folder"])

        utils.git_restore(path_to_repo = config_dict["github"]["repository_folder"])

if __name__ == '__main__':
    main()