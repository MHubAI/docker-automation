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

import argparse
import subprocess

#import logging
#import logging.config

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
    bash_command = ["docker", "build",
                    "--file", "%s"%path_to_dockerfile,
                    "--tag", "%s"%image_tag,
                    "--no-cache"]

    if not verbose:
        bash_command += ["--quiet", "."]
    else:
        bash_command += ["."]

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


def get_dotgit_folder(path_to_folder):

    # check the folder exists
    if not os.path.exists(path_to_folder):
        raise FileNotFoundError("Folder %s not found"%path_to_folder)
    
    # check if the specified folder is already a .git repository
    # if not, check the .git repository exists and is a folder, otherwise raise an error
    if ".git" in path_to_folder:
        path_to_dotgit_folder = path_to_folder
    else:
        if not os.path.exists(os.path.join(path_to_folder, ".git")):
            raise FileNotFoundError("Folder %s not found"%os.path.join(path_to_folder, ".git"))

        path_to_dotgit_folder = os.path.join(path_to_folder, ".git")

    return path_to_dotgit_folder


## --------------------------------

def get_git_hash(path_to_folder, source):

    # check source is valid
    # TO-DO: add checks on other branches? Does it even make sense?
    if source not in ["HEAD", "origin/main"]:
        raise ValueError("Source %s is not valid"%source)

    path_to_dotgit_folder = get_dotgit_folder(path_to_folder)

    # bash command to get the current commit hash
    bash_command =  ["git",
                     "--git-dir", "%s"%path_to_dotgit_folder,
                     "rev-parse", "--verify", "HEAD"]

    # run git in subprocess
    process = subprocess.Popen(bash_command, stdout=subprocess.PIPE)
    # get the output of the git command
    output, error = process.communicate()
    # decode the output
    commit_hash = output.decode('utf-8').strip()

    return commit_hash


## --------------------------------

def git_pull(path_to_folder):

    path_to_dotgit_folder = get_dotgit_folder(path_to_folder)

    # bash command to get the current commit hash
    bash_command =  ["git",
                     "--git-dir", "%s"%path_to_dotgit_folder,
                     "pull"]

    # run git in subprocess
    process = subprocess.Popen(bash_command, stdout=subprocess.PIPE)
    # get the output of the git command
    output, error = process.communicate()

    return output


## --------------------------------
## --------------------------------

def main():

    # TO-DO: implement ands set up logging
    # https://stackoverflow.com/questions/7507825/where-is-a-complete-example-of-logging-config-dictconfig
    #logging.config.dictConfig(config['logging'])
    #logger = logging.getLogger(__name__)

    # parse command line arguments
    parser = argparse.ArgumentParser(description='MHub - local automation for docker builds')
    #parser.add_argument('-l', '--logging', action='store_true', help='enable logging')
    parser.add_argument('-v', '--verbose', action='store_true', help='enable verbose mode')
    parser.add_argument('--dryrun', action='store_true', help='execute in dry run mode')
    parser.add_argument('-c', '--config', action='store', help='path to config file', required=True)
    parser.add_argument('-p', '--push', action='store_true', help='whether to push the images or not')

    args = parser.parse_args()

    # parse yaml config file
    with open(args.config, 'r') as f:
        config_dict = yaml.safe_load(f)
    
    # get hash for the current commit using git
    # - using python:
    #   https://stackoverflow.com/questions/14989858/get-the-current-git-hash-in-a-python-script
    # - using subprocess:
    #   https://stackoverflow.com/questions/949314/how-do-i-get-the-hash-for-the-current-commit-in-git
    commit_hash = get_git_hash(path_to_folder = config_dict["github"]["repository_folder"],
                               source = "HEAD")
    remote_hash = get_git_hash(path_to_folder = config_dict["github"]["repository_folder"],
                               source = "origin/main")

    # if the two hashes are different, pull the latest changes
    if commit_hash != remote_hash:
        if args.dryrun:
            print("git pull %s"%config_dict["github"]["repository_folder"])
        else:
            print(git_pull(path_to_folder = config_dict["github"]["repository_folder"]))


    # for every image in the config file, build the docker image and push it to the registry
    for image in config_dict["images"]:
        
        # get the image dictionary
        image_dict = config_dict["images"][image]

        # quick workaround to avoid passing the config dictionary to the `build_docker_image` function
        image_dict["repository_folder"] = config_dict["github"]["repository_folder"]
        image_dict["dockerhub_username"] = config_dict["dockerhub"]["username"]

        # TO-DO: add option to build only the images that have changed
        if args.dryrun:
            print("docker build")
            if args.push:
                print("docker push")
            pp.pprint(image_dict)
            print("")
        else:
            image_tag = build_docker_image(image_dict, verbose=args.verbose)
            if args.push:
                push_docker_image(image_tag, verbose=args.verbose)

        # TO-DO: add option to send an email with the output of the build and the logs


if __name__ == '__main__':
    main()