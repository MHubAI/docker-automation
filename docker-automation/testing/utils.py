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

import argparse
import subprocess

# TO-DO: add logging
#import logging
#import logging.config

import yaml
import pprint

pp = pprint.PrettyPrinter(indent=2)



def get_docker_command(image_to_test, workflow_dict, use_gpu):

    """
    Generate a Docker command for running a container via subprocess.

    Args:
        image_to_test (str): The name of the Docker image to test in the usual format (repo/image:tag).
        workflow_dict (dict): A dictionary containing information (e.g., paths) on the sample data for the specific workflow.
        use_gpu (bool): Flag indicating whether to run the docker containers using a GPU.

    Returns:
        list: A list representing the Docker command (subprocess runnable).

    Example:
        Example of command returned by this function (once unpacked from list)):
        ```
        docker run \
            -v /home/dennis/Desktop/sample_data/input_dcm:/app/data/input_data
            -v /home/dennis/Desktop/sample_data/output_data:/app/data/output_data
            --gpus all
            mhubai/totalsegmentator:cuda12.0
        ```
    """

    path_to_input_data = os.path.join(workflow_dict["input_data"]["base_folder"], workflow_dict["input_data"]["folder_name"])
    path_to_output_data = workflow_dict["output_data"]["base_folder"]

    map_input_data = "/app/data/input_data"
    map_output_data = "/app/data/output_data"
    
    docker_command = list()
    docker_command += ["docker", "run"]
    docker_command += ["-v", path_to_input_data + ":" + map_input_data]
    docker_command += ["-v", path_to_output_data + ":" + map_output_data]
    
    if use_gpu:
        docker_command += ["--gpus", "all"]
    
    docker_command += [image_to_test]

    return docker_command
        
## --------------------------------

def run_mhub_model(docker_command, verbose=False):

    # run the docker command

    print("Running subprocess...")
    output = subprocess.run(docker_command, check=True, text=True,
                            stdout=None if verbose else subprocess.DEVNULL,
                            stderr=None if verbose else subprocess.DEVNULL)

## --------------------------------

def check_pipeline_run(test_dict, verbose=False):
    
    print(" ")

## --------------------------------

def compare_results(test_dict, verbose=False):
    
    print(" ")
