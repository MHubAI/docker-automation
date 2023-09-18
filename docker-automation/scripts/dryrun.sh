#!/bin/bash

BUILD_BASE_CONF="../build/config/base.yml"
BUILD_MODEL_CONF="../build/config/models.yml"

TEST_CT_CHEST_CONF="../test/config/latest_chest.yml"
TEST_CT_ABDOMEN_CONF="../test/config/latest_abdomen.yml"

PUSH_CONF="/home/mhubai/mhubai_testing/logs"

# -- BUILD --

echo "Building the base Docker image (using $BUILD_BASE_CONF)"
python ../build/run.py --config $BUILD_BASE_CONF --ncores 1 --dryrun

echo "Building the model Docker images (using $BUILD_MODEL_CONF)"
python ../build/run.py --config $BUILD_MODEL_CONF --ncores 1 --dryrun

# -- PRUNE --

echo -e "\n-----------------\n"
echo "Purging all of the dangling Docker images..."
echo ">> run docker prune"

# -- TEST --

echo -e "\n-----------------\n"
echo "Running the testing routine for CHEST CT images (using $TEST_CT_CHEST_CONF)"
python ../test/run.py --config $TEST_CT_CHEST_CONF --verbose --outpath $PUSH_CONF --dryrun

echo "Running the testing routine for ABDOMEN CT images (using $TEST_CT_ABDOMEN_CONF)"
python ../test/run.py --config $TEST_CT_ABDOMEN_CONF --verbose --outpath $PUSH_CONF --dryrun

# -- PUSH --

echo -e "\n-----------------\n"
echo "Pushing all models that passed the checks (using the reports at $PUSH_CONF)"
python ../push/run.py --path_to_logs_folder $PUSH_CONF --ncores 1 --dryrun