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

import filecmp

import argparse
import subprocess

# TO-DO: add logging
#import logging
#import logging.config

import yaml
import json
import pprint

import pydicom
import pydicom_seg
import SimpleITK as sitk

pp = pprint.PrettyPrinter(indent=2)



def get_docker_command(image_to_test, workflow_name, workflow_dict, input_base_dir, output_base_dir, use_gpu):

    """
    Generate a Docker command for running a container via subprocess.

    Args:
        image_to_test (str): The name of the Docker image to test in the usual format (repo/image:tag).
        workflow_name (str):
        workflow_dict (dict):
        input_base_dir (str):
        output_base_dir (str): 
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

    model_name = image_to_test.split("/")[-1].split(":")[0]

    path_to_input_data = os.path.join(input_base_dir, workflow_dict["data_sample"], workflow_name)
    path_to_output_data = os.path.join(output_base_dir, model_name, workflow_dict["data_sample"], workflow_name)

    map_input_data = "/app/data/input_data"
    map_output_data = "/app/data/output_data"
    
    docker_command = list()
    docker_command += ["docker", "run"]
    docker_command += ["-v", path_to_input_data + ":" + map_input_data]
    docker_command += ["-v", path_to_output_data + ":" + map_output_data]
    
    if use_gpu:
        docker_command += ["--gpus", "all"]
    
    docker_command += [image_to_test]
    
    path_to_config = os.path.join("/app/models/%s/config"%model_name, workflow_dict["config"])
    docker_command += ["python3", "-m", "mhubio.run", "--config", path_to_config]
    
    return docker_command
        
## --------------------------------

def run_mhub_model(docker_command, verbose=False):

    # run the docker command

    print("Data processing - running subprocess...")
    output = subprocess.run(docker_command, check=True, text=True,
                            stdout=None if verbose else subprocess.DEVNULL,
                            stderr=None if verbose else subprocess.DEVNULL)

    print("... Done.")

    if verbose:
        print("Subprocess output:", output)

## --------------------------------

def compare_results_file(test_dict, verbose=False):

    # FIXME: debug
    #verbose = True

    output_dir = test_dict["pipeline_output"]

    output_file_list = list()
    reference_file_list = list()

    # use os.walk to iterate over the files in the output directory and create a list of paths to the files
    for root, dirs, files in os.walk(output_dir):
        for file in files:
            output_file_list.append(os.path.join(root, file))

    # at this stage, we should already have checked the directory trees are equal, so we can safely assume
    # any file found under "reference_data" will have a counterpart in the "output_data" directory
    # we can therefore create a list of paths to the files in the reference directory by replacing the
    # "output_data" part of the path with "reference_data", and loop on both lists together
    reference_file_list = [f.replace("output_data", "reference_data") for f in output_file_list]

    itk_image_formats = tuple([".nii.gz", ".nrrd", ".mha", ".mhd"])

    if verbose:
        print("output_file_list:", output_file_list)
        print("reference_file_list:", reference_file_list)

    # depending on the file extension, we will use different functions to compare the files
    # DICOM SEG
    for output_file, reference_file in zip(output_file_list, reference_file_list):

        if output_file.endswith(".seg.dcm"):
            same_content = compare_results_dicomseg(output_file, reference_file, verbose=verbose)

            if not same_content:
                print("DICOM SEG files %s and %s are not equal"%(output_file, reference_file))
                return False
        
        elif output_file.endswith(itk_image_formats):
            same_content = compare_results_itk(output_file, reference_file, verbose=verbose)

            if not same_content:
                print("ITK image files %s and %s are not equal"%(output_file, reference_file))
                return False

        elif output_file.endswith(".json"):
            same_content = compare_results_json(output_file, reference_file, verbose=verbose)

            if not same_content:
                print("JSON files %s and %s are not equal"%(output_file, reference_file))
                return False

        else:
            print("File %s has an unsupported format; moving on..."%output_file)
            continue
        
    return True
    
## --------------------------------

def compare_results_itk(output_file, reference_file, dc_thresh=0.99, verbose=False):
    
    if verbose:
        print("\nComparing ITK image files...")

        print("Output file:", output_file)
        print("Reference file:", reference_file)

    # FIXME: swap this block out for whatever we decide to stick with
    output_seg = sitk.ReadImage(output_file)
    reference_seg = sitk.ReadImage(reference_file)

    dc = compute_overlap(output_seg, reference_seg)
    
    # FIXME: we can bend this rule as much as we want
    if dc > dc_thresh:
        print(">>> The ITK image files are equal (DC/DC threshold: %g/%g)"%(dc, dc_thresh))
        return True
    else:
        print(">>> The ITK image files are NOT equal (DC/DC threshold: %g/%g)"%(dc, dc_thresh))
        return False

## --------------------------------

def compute_overlap(itksegimage1, itksegimage2):
    # Load segmentation volumes

    # Compute the overlap between the segmentations
    overlap_filter = sitk.LabelOverlapMeasuresImageFilter()
    overlap_filter.Execute(itksegimage1, itksegimage2)

    # Get the overlap measures
    dice_coefficient = overlap_filter.GetDiceCoefficient()

    return dice_coefficient

## --------------------------------

def compare_results_dicomseg(output_file, reference_file, dc_thresh=0.99, verbose=False):

    if verbose:
        print("\nComparing DICOM SEG files...")

        print("Output file:", output_file)
        print("Reference file:", reference_file)

    dcm = pydicom.dcmread(output_file)
    reader = pydicom_seg.SegmentReader()
    output_seg = reader.read(dcm)

    dcm = pydicom.dcmread(reference_file)
    reader = pydicom_seg.SegmentReader()
    reference_seg = reader.read(dcm)

    if len(output_seg.available_segments) != len(reference_seg.available_segments):
        print(">>> The DICOM SEG files store a different number of segments")
        return False

    for segment_number in output_seg.available_segments:
        output_segment = output_seg.segment_image(segment_number)
        reference_segment = reference_seg.segment_image(segment_number)

        dc = compute_overlap(output_segment, reference_segment)

        # FIXME: how do we aggregate the DCs for each segment?
        if dc < dc_thresh:
            print(">>> DICOM SEG segments #%g are not equal (DC/DC threshold: %g/%g)"%(segment_number, dc, dc_thresh))
            return False
    

    print(">>> The DICOM SEG files are equal (DC threshold: %g)"%dc_thresh)
    return True

## --------------------------------

def compare_results_json(output_file, reference_file, verbose=False):

    if verbose:
        print("\nComparing JSON files...")

        print("Output file:", output_file)
        print("Reference file:", reference_file)

    # load the json files
    with open(output_file, "r") as f:
        json1 = json.load(f)

    with open(reference_file, "r") as f:
        json2 = json.load(f)

    # NOTE: this compares every (key;value) pair in the json files and should not raise any errors
    # provided nothing strange is in the json (i.e., everything needs to be comparable with "==")
    # therefore, it should be good for now, but we might want to change it in the future
    if json1 == json2:
        print(">>> The JSON files are equal")
        return True


## --------------------------------

def compare_results_dir(test_dict, verbose=False, check_files=False):

    output_dir = test_dict["pipeline_output"]
    reference_dir = test_dict["pipeline_reference"]

    print("\nOutput directory:", output_dir)
    print("Reference directory:", reference_dir)
    
    print("Comparing the results with the reference...")

    # check that the directories exist (they should, since they were created by the docker container)
    assert os.path.exists(output_dir), "Output directory %s does not exist"%output_dir
    assert os.path.exists(output_dir), "Reference directory %s does not exist"%output_dir

    # check that the directories trees are equal
    same_tree = are_dir_trees_equal(output_dir, reference_dir, check_files=check_files, verbose=verbose)

    print("... Done.")

    return same_tree

## --------------------------------
    
def are_dir_trees_equal(dir1, dir2, check_files=False, verbose=False):

    """
    Compare two directory trees.

    Args:
        dir1 (str): Path to the first directory.
        dir2 (str): Path to the second directory.
        check_files (bool): Flag indicating whether to check the files in the directories or just the directoy trees.
                            Defaults to False (as binary files in Linux can be different even if the content the same).
        verbose (bool): Flag indicating whether to print a bunch of text that might help with debug. Defaults to False.

    Returns:
        bool: True if the directory trees are equal, False otherwise.
    """

    # construct a new directory comparison object, to compare the directories a and b
    # The dircmp class compares files by doing shallow comparisons
    dirs_cmp = filecmp.dircmp(dir1, dir2)

    # left_only: list of files and subdirectories that are in dir1 but not in dir2
    # right_only: list of files and subdirectories that are in dir2 but not in dir1
    # funny_files: list of files that are in both directories, but could not be compared
    # if some of these lists are not empty, the directories are definitely not equal
    if len(dirs_cmp.left_only)>0 or len(dirs_cmp.right_only)>0 or len(dirs_cmp.funny_files)>0:
        if verbose: 
            print("left_only:", dirs_cmp.left_only)
            print("right_only:", dirs_cmp.right_only)
            print("funny_files:", dirs_cmp.funny_files)
        return False

    # common_files: list of files that are common to both directories
    # if the check above is passed, compare each file in common_files
    # if the directories do not have files (e.g., are only nested subdirectories), this will be an empty list
    # and this step will simply be skipped, if this is not the case
    # filecmp.cmpfiles will compare the files in the two directories and return a tuple of lists:
    #   - match: list of files that match
    #   - mismatch: list of files that do not match
    #   - errors: list of files that could not be compared (including those that don’t exist in one of the directories)
    match, mismatch, errors =  filecmp.cmpfiles(dir1, dir2, dirs_cmp.common_files, shallow=False)

    if verbose:
        print("match:", match)

    # if some of the files in common_files do not match, the directories are not equal
    # however, we know binary files in Linux can be different even if the content the same
    # (which is why we are also going to check the segmentation/classifications results in other ways)
    #   - if the check_files flag is set to False, we will ignore "mismatch" and focus on "errors" alone
    #   - if the check_files flag is set to True, we will check both "mismatch" and "errors"
    if check_files:
        if len(mismatch)>0 or len(errors)>0:
            if verbose:
                print("mismatch:", mismatch)
                print("errors:", errors)
            return False
    else:
        if len(errors)>0:
            if verbose:
                print("errors:", errors)
            return False

    # common_dirs: list of subdirectories that are common to both directories
    # assuming the tree is identical, this should be a list of subdirectories
    # if there are commons directories, run the same function recursively on each of them (always in pairs)
    for common_dir in dirs_cmp.common_dirs:
        new_dir1 = os.path.join(dir1, common_dir)
        new_dir2 = os.path.join(dir2, common_dir)

        if verbose:
            print("new_dir1:", new_dir1)
            print("new_dir2:", new_dir2)

        if not are_dir_trees_equal(new_dir1, new_dir2, verbose=verbose):
            if verbose:
                print("subdirectories %s and %s are not equal"%(new_dir1, new_dir2))
            return False

    # if all of the checks above are passed, the directories are equal
    if verbose:
        print("Directories %s and %s are equal"%(dir1, dir2))

    return True