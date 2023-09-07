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

import yaml
import pprint
import pandas as pd

pp = pprint.PrettyPrinter(indent=2)

import utils

max_cores = os.cpu_count()

## --------------------------------

# for now, build only
def run_core(image_dict):

    try:
        image_tag = utils.push_docker_image(image_tag = image_dict["name"])    
    except Exception as e:
        print("Error pushing image %s"%image_dict["name"])
        print(e)
        return None

## --------------------------------

def dryrun_core(image_dict):
    print("docker push")
    pp.pprint(image_dict["name"])
    print("")

## --------------------------------

def main():

    # FIXME: for now, assume the log-in to the correct dockerhub account was already set up on the system

    # parse command line arguments
    parser = argparse.ArgumentParser(description='MHub - local automation for docker builds')
    #parser.add_argument('-l', '--logging', action='store_true', help='enable logging')
    parser.add_argument('--verbose', action='store_true', help='enable verbose mode')
    parser.add_argument('--dryrun', action='store_true', help='execute in dry run mode')
    parser.add_argument('--ncores', action='store', help='number of cores to execute on (max is %g)'%max_cores, 
                        type=int, default=4)
    parser.add_argument('--path_to_logs_folder', action='store', help='path to the folder storing the automated testing reports', required=True)

    args = parser.parse_args()
    
    use_multiprocessing = True if args.ncores > 1 else False

    # load all of the CSV files storing the automated testing reports
    csv_files = [os.path.join(args.path_to_logs_folder, f) for f in os.listdir(args.path_to_logs_folder) if f.endswith(".csv")]
    
    # check that there is at least one CSV file
    if len(csv_files) == 0:
        print("WARNING: no CSV files found in %s"%args.path_to_logs_folder)
        sys.exit(1)

    # load the CSV files using pandas
    df_list = []
    csv_columns = ["image", "workflow", "data_sample", "dirtree_match", "output_match"]
    for csv_file in csv_files:

        tmp = pd.read_csv(csv_file)

        # FIXME: implement better checks?
        # check that the CSV file has the correct columns (they need to be the same as csv_columns)
        if not set(csv_columns).issubset(set(tmp.columns)):
            print("WARNING: CSV file %s does not have the correct format. Skipping..."%csv_file)
            continue
        
        # check the last two columns have only boolean values
        if not tmp["dirtree_match"].isin([True, False]).all() or not tmp["output_match"].isin([True, False]).all():
            print("WARNING: CSV file %s does not have the correct format. Skipping..."%csv_file)
            continue
        
        df_list.append(tmp)
    
    if len(df_list) == 0:
        print("WARNING: no CSV files correctly formatted found in %s"%args.path_to_logs_folder)
        sys.exit(1)

    # concatenate the dataframes
    df = pd.concat(df_list)
    df.reset_index(inplace=True, drop=True)

    # check which images passed the automated testing (both dirtree and output, for all the workflows and data samples)
    image_list = list()
    tags_list = list()

    for image in df["image"].unique():
        
        image_dict = dict() 

        # collect all the tags of the images that passed the test for later use
        tags_list.append(image.split(":")[-1])

        tmp = df[df["image"] == image]
        val = tmp["dirtree_match"].all() and tmp["output_match"].all()

        if val:
            image_dict["name"] = image
            image_list.append(image_dict)
    
    # if more than one model passed the checks (i.e., image_list is not empty)
    # add the base image to the list

    tags_list = list(set(tags_list))

    if len(image_list) > 0:
        for tag in tags_list:
            image_list.append({"name": "mhubai/base:%s"%tag})

    # for every image that passed the test, push the docker image to the registry
    if args.dryrun:
        pool = multiprocessing.Pool(processes = 1)

        if use_multiprocessing:
            print("This will run in parallel, on %g cores.\n"%(args.ncores))
        else:
            print("This will run on a single core.\n")

        for _ in tqdm.tqdm(pool.imap_unordered(dryrun_core, image_list), total = len(image_list)):
            pass
    else:
        if use_multiprocessing:
            pool = multiprocessing.Pool(processes = args.ncores)

            print("\nRunning in parallel on %g cores.\n"%(args.ncores))
            for _ in tqdm.tqdm(pool.imap_unordered(run_core, image_list), total = len(image_list)):
                pass
        else:
            print("Running on a single core.\n")
            for image_dict in image_list:
                run_core(image_dict)

if __name__ == '__main__':
    main()

