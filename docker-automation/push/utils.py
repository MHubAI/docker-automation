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
