# MHub Container Automated Testing Pipeline

```
usage: run.py [-h] [--verbose] [--gpu] [--dryrun] [--ncores NCORES] --config CONFIG

MHub - automated testing of MHub containers

optional arguments:
  -h, --help       show this help message and exit
  --verbose        enable verbose mode
  --gpu            enable verbose mode
  --dryrun         execute in dry run mode
  --ncores NCORES  number of cores to execute on (max is 1 for now)
  --config CONFIG  path to config file
```

Example command:

```
python testing/run.py --config testing/config/dev.yml --gpu --dryrun --verbose
```

## Config file

The config file will be used to specify the parameters for testing the Docker images. The config file is a YAML file with the following structure:

- Docker Images (`images`): This section defines the MHub images that will be tested. It consists of a dictionary with keys representing the names of the Docker images. Each image has the following attributes:
    - `name`: The name of the Docker image .
    - `version`: The version or tag of the Docker image to be used.

- Workflows (`workflows`): This section defines the different workflows/scenarios for which every MHub container will be tested. It consists of a dictionary with keys (usually) representing the formats of the input data. Each workflow has the following attributes:
    - `data_sample`: This should identify the body part examined and the modality of the input data.
    - `config`: This specifies the name of the configuration file to be used for the workflow.

An example of config file is shown below:

```
images:
    platipy:
        name: platipy
        version: patch-models
    
    lungmask:
        name: lungmask
        version: patch-models

workflows:
    dicom:
        data_sample: "chest_ct"
        config: "default.yml"
        
    nrrd:
        data_sample: "chest_ct"
        config: "slicer.yml"
```

The structure of the directory storing the reference files should match that of the config file in the following way:

```
tree -L 3 reference_data/
reference_data/
└── platipy
    └── chest_ct
        ├── dicom
        └── nrrd
```

## Example Output

``````
python testing/run.py --config testing/config/dev.yml --gpu --dryrun --verbose

Found 2 image(s) to test running 2 workflow(s)
- mhubai/platipy:patch-models - dicom
- mhubai/platipy:patch-models - nrrd
- mhubai/lungmask:patch-models - dicom
- mhubai/lungmask:patch-models - nrrd

Running on a single core.

Running test 1/4
MHub image: mhubai/platipy:patch-models
Workflow: dicom
Sample data: chest_ct
Using GPU

- Docker command to be executed:
docker run -v /home/mhubai/mhubai_testing/input_data/chest_ct/dicom:/app/data/input_data -v /home/mhubai/mhubai_testing/output_data/platipy/chest_ct/dicom:/app/data/output_data --rm --gpus device=0 mhubai/platipy:patch-models --workflow default
- Output dir to be generated:
/home/mhubai/mhubai_testing/output_data/platipy/chest_ct/dicom
- Reference dir to be compared to:
/home/mhubai/mhubai_testing/reference_data/platipy/chest_ct/dicom

Running test 2/4
MHub image: mhubai/platipy:patch-models
Workflow: nrrd
Sample data: chest_ct
Using GPU

- Docker command to be executed:
docker run -v /home/mhubai/mhubai_testing/input_data/chest_ct/nrrd:/app/data/input_data -v /home/mhubai/mhubai_testing/output_data/platipy/chest_ct/nrrd:/app/data/output_data --rm --gpus device=0 mhubai/platipy:patch-models --workflow slicer
- Output dir to be generated:
/home/mhubai/mhubai_testing/output_data/platipy/chest_ct/nrrd
- Reference dir to be compared to:
/home/mhubai/mhubai_testing/reference_data/platipy/chest_ct/nrrd

Running test 3/4
MHub image: mhubai/lungmask:patch-models
Workflow: dicom
Sample data: chest_ct
Using GPU

- Docker command to be executed:
docker run -v /home/mhubai/mhubai_testing/input_data/chest_ct/dicom:/app/data/input_data -v /home/mhubai/mhubai_testing/output_data/lungmask/chest_ct/dicom:/app/data/output_data --rm --gpus device=0 mhubai/lungmask:patch-models --workflow default
- Output dir to be generated:
/home/mhubai/mhubai_testing/output_data/lungmask/chest_ct/dicom
- Reference dir to be compared to:
/home/mhubai/mhubai_testing/reference_data/lungmask/chest_ct/dicom

Running test 4/4
MHub image: mhubai/lungmask:patch-models
Workflow: nrrd
Sample data: chest_ct
Using GPU

- Docker command to be executed:
docker run -v /home/mhubai/mhubai_testing/input_data/chest_ct/nrrd:/app/data/input_data -v /home/mhubai/mhubai_testing/output_data/lungmask/chest_ct/nrrd:/app/data/output_data --rm --gpus device=0 mhubai/lungmask:patch-models --workflow slicer
- Output dir to be generated:
/home/mhubai/mhubai_testing/output_data/lungmask/chest_ct/nrrd
- Reference dir to be compared to:
/home/mhubai/mhubai_testing/reference_data/lungmask/chest_ct/nrrd
```