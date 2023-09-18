"""
-------------------------------------------------
MHub - utils for automation of docker builds
-------------------------------------------------
-------------------------------------------------
Author: Dennis Bontempi
Email:  dbontempi@bwh.harvard.edu
-------------------------------------------------
"""

import os
import sys
import time

import fileinput

import argparse
import subprocess

# TO-DO: add logging
#import logging
#import logging.config

import yaml
import pprint

pp = pprint.PrettyPrinter(indent=2)

def build_docker_image(image_dict, verbose=False):
    
    """
    Builds a Docker image based on the provided image dictionary.

    Args:
        image_dict (dict): A dictionary containing the image details.
        verbose (bool, optional): Controls the verbosity of the output. Defaults to False.

    Returns:
        str: The tag of the built Docker image.

    Raises:
        FileNotFoundError: If the Dockerfile specified in the image dictionary is not found.

    Example:
        >>> image_dict = {
        ...     "dockerfile": "Dockerfile",
        ...     "repository_folder": "/path/to/repository",
        ...     "dockerhub_username": "myusername",
        ...     "name": "myimage",
        ...     "version": "1.0"
        ... }
        >>> image_tag = build_docker_image(image_dict, verbose=True)
    """

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
    time.sleep(1)

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

## --------------------------------

def push_docker_image(image_tag, verbose=False):

    """
    Pushes a Docker image to the dockerhub registry.

    Args:
        image_tag (str): The tag of the Docker image to push.
        verbose (bool, optional): Controls the verbosity of the output. Defaults to False.

    Returns:
        None

    Raises:
        CalledProcessError: If the Docker push command fails.

    Example:
        >>> image_tag = "my-docker-image:latest"
        >>> push_docker_image(image_tag, verbose=True)
    """

    # push the docker image to the registry
    # TO-DO: add checks on the docker push
    bash_command = ["docker", "push", "%s"%(image_tag)]
    
    output = subprocess.run(bash_command, check=True, text=True,
                            stdout=None if verbose else subprocess.DEVNULL,
                            stderr=None if verbose else subprocess.DEVNULL)


## --------------------------------

def get_git_hash(path_to_repo):

    """
    Returns the current commit hash of a local Git repository.

    Args:
        path_to_repo (str): The path to the local Git repository.

    Returns:
        str: The current commit hash.

    Example:
        >>> repo_path = "/path/to/repository"
        >>> commit_hash = get_git_hash(repo_path)
        >>> print(commit_hash)
        'b45e63a71c08e8c3ef1b9a4fb5ebf1bebc58a52d'
    """

    # bash command to get the current commit hash
    bash_command =  ["git",
                     "-C", "%s"%path_to_repo,
                     "rev-parse", "--verify", "HEAD"]

    # run git in subprocess
    process = subprocess.Popen(bash_command, stdout=subprocess.PIPE)
    # get the output of the git command
    output, error = process.communicate()
    # decode the output
    commit_hash = output.decode('utf-8').strip()

    return commit_hash

## --------------------------------

def get_git_hash_remote(repo_url):
        
    """
    Returns the current commit hash of a remote Git repository.

    Args:
        repo_url (str): The URL of the remote Git repository.

    Returns:
        str: The current commit hash.

    Example:
        >>> repository_url = "https://github.com/username/repository.git"
        >>> commit_hash = get_git_hash_remote(repository_url)
        >>> print(commit_hash)
        'b45e63a71c08e8c3ef1b9a4fb5ebf1bebc58a52d'
    
    Pointers/References:
        - using python: https://stackoverflow.com/questions/14989858/get-the-current-git-hash-in-a-python-script
        - using subprocess: https://stackoverflow.com/questions/949314/how-do-i-get-the-hash-for-the-current-commit-in-git
    """

    # bash command to get the current commit hash
    bash_command =  ["git",
                    "ls-remote", "--heads",
                    "%s"%repo_url, "refs/heads/main"]

    # run git in subprocess
    process = subprocess.Popen(bash_command, stdout=subprocess.PIPE)
    # get the output of the git command
    output, error = process.communicate()
    # decode the output
    commit_hash = output.decode('utf-8').strip()
    commit_hash = commit_hash.split("\t")[0]

    return commit_hash

## --------------------------------

def get_list_of_updated_folders(path_to_repo):

    """
    Returns a list of updated folders in the repository based on the last commit.

    Args:
        path_to_repo (str): The path to the repository.

    Returns:
        list: A list of updated folders.

    Example:
        >>> repo_path = "/path/to/repository"
        >>> updated_folders = get_list_of_updated_folders(repo_path)
        >>> print(updated_folders)
        ['/path/to/folder1', '/path/to/folder2', '/path/to/folder3']
    """


    # bash command to get the list of folders changed in the last commit
    bash_command =  ["git",
                     "-C", "%s"%path_to_repo,
                     "diff", "--name-only", "HEAD~2...HEAD"]
    
    # run git in subprocess
    process = subprocess.Popen(bash_command, stdout=subprocess.PIPE)
    # get the output of the git command
    output, error = process.communicate()
    # decode the output
    updated_folders = output.decode('utf-8').strip().split("\n")

    # for each entry in the list, separate the file name from the path
    updated_folders = [os.path.dirname(f) for f in updated_folders]

    return updated_folders

## --------------------------------

def git_pull(path_to_repo):

    """
    Performs a git pull operation on a local Git repository.

    Args:
        path_to_repo (str): The path to the local Git repository.

    Returns:
        bytes: The output of the git pull command.

    Example:
        >>> repo_path = "/path/to/repository"
        >>> output = git_pull(repo_path)
        >>> print(output.decode('utf-8'))
        'Updating b45e63a71c..a1b2c3d4e5f'
    """

    # bash command to git pull
    bash_command =  ["git",
                     "-C", "%s"%path_to_repo,
                     "pull"]

    # run git in subprocess
    process = subprocess.Popen(bash_command, stdout=subprocess.PIPE)
    # get the output of the git command
    output, error = process.communicate()

    return output

## --------------------------------

def modify_dockerfile(image_dict, branch):

    # update the Dockerfile to pull the correct branch
    rel_path_to_dockerfile = image_dict["dockerfile"]
    path_to_dockerfile = os.path.join(image_dict["repository_folder"], rel_path_to_dockerfile)

    # for both model and base images, replace the line that pulls the models repository
    to_replace = "git fetch https://github.com/MHubAI/models.git main"
    replace_with = "git fetch https://github.com/MHubAI/models.git %s"%branch

    for line in fileinput.input(path_to_dockerfile, inplace=True): 
        print(line.replace(to_replace, replace_with), end = "")
    
    fileinput.close()

    # for model images only, replace the first line to build the image starting from the "branch" base image
    if image_dict["name"] != "base":
        to_replace = "FROM mhubai/base:latest"
        replace_with = "FROM mhubai/base:%s"%branch

        for line in fileinput.input(path_to_dockerfile, inplace=True): 
            print(line.replace(to_replace, replace_with), end = "")
        
        fileinput.close()

## --------------------------------

def git_restore(path_to_repo):
    
    """
    Performs a git restore operation on a local Git repository.

    Args:
        path_to_repo (str): The path to the local Git repository.

    Returns:
        bytes: The output of the git restore command.

    Example:
        >>> repo_path = "/path/to/repository"
        >>> output = git_restore(repo_path)
        >>> print(output.decode('utf-8'))
        ' '
    """

    # bash command to git restore
    bash_command =  ["git",
                     "-C", "%s"%path_to_repo,
                     "restore", "%s"%path_to_repo]

    # run git in subprocess
    process = subprocess.Popen(bash_command, stdout=subprocess.PIPE)
    # get the output of the git command
    output, error = process.communicate()

    return output

