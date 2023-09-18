#!/bin/bash
BUILD_BASE_CONF="../build/config/base.yml"
BUILD_MODEL_CONF="../build/config/models.yml"

TEST_CT_CHEST_CONF="../test/config/latest_chest.yml"
TEST_CT_ABDOMEN_CONF="../test/config/latest_abdomen.yml"

DATE_TIME=$(date +"%d%m%Y%H%M%S")
RUN_ID=${DATE_TIME}_$(cat /dev/urandom | tr -cd 'a-f0-9' | head -c 16)

TEST_LOG_DIR="/home/mhubai/mhubai_testing/logs/${RUN_ID}"
IMAGE_LOG_DIR="${TEST_LOG_DIR}/inspect/"

mkdir -p ${TEST_LOG_DIR}
mkdir -p ${IMAGE_LOG_DIR}

echo -e "Run ID: ${RUN_ID}\n"

# -- BUILD --

echo "Building the base Docker image (using ${BUILD_BASE_CONF})"
python ../build/run.py --config ${BUILD_BASE_CONF} --ncores 1

echo "Building the model Docker images (using ${BUILD_MODEL_CONF})"
python ../build/run.py --config ${BUILD_MODEL_CONF} --ncores 8

# -- DOCKER INSPECT --

for image in $(docker images --filter "since=mhubai/base:latest" --format '{{.Repository}}:{{.Tag}}' | grep "mhubai.*:latest"); do
    echo "Exporting report for $image..."
    image_name=$(echo $image | cut -d/ -f2 | cut -d: -f1)
    docker inspect $image > ${IMAGE_LOG_DIR}/$(echo ${image_name} | sed 's/\//_/g' | sed 's/:/_/g').json
done

# -- PRUNE --

echo -e "\n-----------------\n"
echo "Deleting all of the dangling Docker images..."
docker image prune -f

# -- TEST --

echo -e "\n-----------------\n"
echo "Running the testing routine for CHEST CT images (using ${TEST_CT_CHEST_CONF})"
python ../test/run.py --config ${TEST_CT_CHEST_CONF} --verbose --outpath ${TEST_LOG_DIR}

echo "Running the testing routine for ABDOMEN CT images (using ${TEST_CT_ABDOMEN_CONF})"
python ../test/run.py --config ${TEST_CT_ABDOMEN_CONF} --verbose --outpath ${TEST_LOG_DIR}

# -- PUSH --

echo -e "\n-----------------\n"
echo "Pushing all models that passed the checks (using the reports at ${TEST_LOG_DIR})"
python ../push/run.py --path_to_logs_folder ${TEST_LOG_DIR} --ncores 8 
