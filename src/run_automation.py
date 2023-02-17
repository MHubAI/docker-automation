"""
-------------------------------------------------
MHub - GitHub automation for docker builds
-------------------------------------------------
-------------------------------------------------
Author: Dennis Bontempi
Email:  dbontempi@bwh.harvard.edu
-------------------------------------------------
"""

import os
import sys
import time

import argparse
import subprocess

import yaml
import pprint

pp = pprint.PrettyPrinter(indent=2)

# TO-DO: move the functions below to a separate file


def build_docker_image(image_dict, verbose):
    
    # get the path to the Dockerfile
    rel_path_to_dockerfile = image_dict["dockerfile"]
    path_to_dockerfile = os.path.join(image_dict["repository_folder"], rel_path_to_dockerfile)

    # check the file exists
    if not os.path.exists(path_to_dockerfile):
        raise FileNotFoundError("File %s not found"%path_to_dockerfile)

    # generate image tag based on the dictionary keys
    image_tag = "%s/%s:%s"%(image_dict["dockerhub_username"],
                            image_dict["name"],
                            image_dict["version"])

    print("Building dockerfile at %s as: '%s'\n"%(path_to_dockerfile, image_tag))            
    time.sleep(2)

    # build the docker image
    # TO-DO: add checks on the docker build
    # TO-DO: add option to build the image without pushing it to the registry
    bash_command = ["docker", "build",
                    "--file", "%s"%path_to_dockerfile,
                    "--tag", "%s"%image_tag,
                    "--no-cache", "."]

    if verbose:
        print("Running the shell command:\n", " ".join(bash_command), "\n")
        time.sleep(2)

    # TO-DO: add logging
    output = subprocess.run(bash_command, check=True, text=True,
                            stdout=None if verbose else subprocess.DEVNULL,
                            stderr=None if verbose else subprocess.DEVNULL)

    return image_tag


def push_docker_image(image_tag, verbose):

    # push the docker image to the registry
    # TO-DO: add checks on the docker push
    bash_command = ["docker", "push", "%s"%(image_tag)]
    
    output = subprocess.run(bash_command, check=True, text=True,
                            stdout=None if verbose else subprocess.DEVNULL,
                            stderr=None if verbose else subprocess.DEVNULL)


## --------------------------------
## --------------------------------

def main():

    # parse command line arguments
    parser = argparse.ArgumentParser(description='MHub - GitHub automation for docker builds')
    #parser.add_argument('-l', '--logging', action='store_true', help='enable logging')
    parser.add_argument('-v', '--verbose', action='store_true', help='enable verbose mode')
    parser.add_argument('--dryrun', action='store_true', help='execute in dry run mode')
    parser.add_argument('-c', '--config', action='store', help='path to config file', required=True)

    args = parser.parse_args()

    # parse yaml config file
    with open(args.config, 'r') as f:
        config_dict = yaml.safe_load(f)
    
    # for every image in the config file, build the docker image and push it to the registry
    for image in config_dict["images"]:
        
        # get the image dictionary
        image_dict = config_dict["images"][image]

        # quick workaround to avoid passing the config dictionary to the `build_docker_image` function
        image_dict["repository_folder"] = config_dict["github"]["repository_folder"]
        image_dict["dockerhub_username"] = config_dict["dockerhub"]["username"]

        # TO-DO: add option to build only the images that have changed
        if args.dryrun:
            print("docker build and push")
            pp.pprint(image_dict)
            print("")
        else:
            image_tag = build_docker_image(image_dict, verbose=args.verbose)
            push_docker_image(image_tag, verbose=args.verbose)


if __name__ == '__main__':
    main()