# MHub container automated testing pipeline

## Running the testing pipeline

The testing pipeline can be run with the following command:

```
python run.py --config config/totalsegmentator.yml --verbose --gpu
```

See the script help for details. Example of the pipeline output:


```
dennis@W2-S1:~/git/mhubai-org/docker-automation/docker-automation/testing$ time python run.py --config config/totalsegmentator.yml --verbose --gpu 
Found 4 image(s) to test running 2 workflow(s)
- mhubai/totalsegmentator:cuda11.4 - dicom
- mhubai/totalsegmentator:cuda11.4 - nrrd
- mhubai/totalsegmentator:cuda12.0 - dicom
- mhubai/totalsegmentator:cuda12.0 - nrrd
Running on a single core.

Running test 1/4
MHub image: mhubai/totalsegmentator:cuda11.4
Workflow: dicom
Sample data: chest_ct
Using GPU
Data processing - running subprocess...
... Done.

Output directory: /home/mhubai/mhubai_testing/output_data/totalsegmentator/chest_ct/dicom
Reference directory: /home/mhubai/mhubai_testing/reference_data/totalsegmentator/chest_ct/dicom
Comparing the results with the reference...
... Done.
>>> The directory tree of the output matches the expected output
>>> The DICOM SEG files are equal (DC threshold: 0.99)

Running test 2/4
MHub image: mhubai/totalsegmentator:cuda11.4
Workflow: nrrd
Sample data: chest_ct
Using GPU
Data processing - running subprocess...
... Done.

Output directory: /home/mhubai/mhubai_testing/output_data/totalsegmentator/chest_ct/nrrd
Reference directory: /home/mhubai/mhubai_testing/reference_data/totalsegmentator/chest_ct/nrrd
Comparing the results with the reference...
... Done.
>>> The directory tree of the output matches the expected output
>>> The ITK image files are equal (DC/DC threshold: 0.99997/0.99)
>>> The JSON files are equal

Running test 3/4
MHub image: mhubai/totalsegmentator:cuda12.0
Workflow: dicom
Sample data: chest_ct
Using GPU
Data processing - running subprocess...
... Done.

Output directory: /home/mhubai/mhubai_testing/output_data/totalsegmentator/chest_ct/dicom
Reference directory: /home/mhubai/mhubai_testing/reference_data/totalsegmentator/chest_ct/dicom
Comparing the results with the reference...
... Done.
>>> The directory tree of the output matches the expected output
>>> The DICOM SEG files are equal (DC threshold: 0.99)

Running test 4/4
MHub image: mhubai/totalsegmentator:cuda12.0
Workflow: nrrd
Sample data: chest_ct
Using GPU
Data processing - running subprocess...
... Done.

Output directory: /home/mhubai/mhubai_testing/output_data/totalsegmentator/chest_ct/nrrd
Reference directory: /home/mhubai/mhubai_testing/reference_data/totalsegmentator/chest_ct/nrrd
Comparing the results with the reference...
... Done.
>>> The directory tree of the output matches the expected output
>>> The ITK image files are equal (DC/DC threshold: 0.99997/0.99)
>>> The JSON files are equal

real	1m52,515s
user	1m31,143s
sys	0m11,694s
```

```
dennis@W2-S1:/home/mhubai/mhubai_testing$ tree output_data/
output_data/
└── totalsegmentator
    └── chest_ct
        ├── dicom
        │   └── 1.2.826.0.1.3680043.8.498.99748665631895691356693177610672446391
        │       └── TotalSegmentator.seg.dcm
        └── nrrd
            ├── segdef.json
            └── segmentations.nii.gz
```

## Config File

Every image will require one configuration file. The configuration file should follow the structure below:

```
images:
    # the name of the entries does not really make a difference, but it should be unique
    totalsegmentator_cuda11.4:
        name: totalsegmentator
        version: cuda11.4

    totalsegmentator_cuda12.0:
        name: totalsegmentator
        version: cuda12.0

workflows:
    # this should identify the format of the input data
    dicom:
        # this should identify the body part examined and the modality
        data_sample: "chest_ct"
        # FIXME: to change in "default"
        config: "config.yml"
    nrrd:
    # this should identify the body part examined and the modality
        data_sample: "chest_ct"
        config: "slicer.yml"
```

Under `images` the user should specify the images to run the processing pipeline for and their versions.

Under workflows, the user should specify the processing workflows (e.g., `dicom` for DICOM to DICOM, or `nrrd` for 3DSlicer) that should be automatically tested. For now, the name of the workflow corresponds to the input data (by design). The `config` field is used to specify the config file to use for the workflow. The config file should be located in the `config` folder under `/app/models/$MODEL_NAME` in the container.

## Input Data

Output data should be organized according to the following structure:

```
input_data/
├── abdomen_ce_ct
│   ├── dicom
│   └── nrrd
├── chest_ct
│   ├── dicom
│   └── nrrd
└── wholebody_ct
    ├── dicom
    └── nrrd
```

The base path to the input data folder(s) is hardcoded in the script as a constant:

```
# constants definition
INPUT_BASE_DIR = "/home/mhubai/mhubai_testing/input_data"
```

The rest of the absolute path (to allow for mounting in the docker containers) is obtained from the config file. For example, if the config file specifies:

```
workflows:
    dicom:
        data_sample: "chest_ct"
```

The following will be asserted for the input data (and mounted in the docker container):

```
INPUT_BASE_DIR = "/home/mhubai/mhubai_testing/input_data"

# mounted in the container
>>> path_to_input
"/home/mhubai/mhubai_testing/input_data/chest_ct/dicom"

```

## Output and Reference Data


The output and reference data should be organized according to the following structure (in the example of TotalSegmentator):

```
output_data/
└── totalsegmentator
    └── chest_ct
        ├── dicom
        │   └── 1.2.826.0.1.3680043.8.498.99748665631895691356693177610672446391
        │       └── TotalSegmentator.seg.dcm
        └── nrrd
            ├── segdef.json
            └── segmentations.nii.gz
```

The base path to the output data and reference data folders is hardcoded in the script as a constant:

```
# constants definition
OUTPUT_BASE_DIR = "/home/mhubai/mhubai_testing/output_data"
REFERENCE_BASE_DIR = "/home/mhubai/mhubai_testing/reference_data"
```

The rest of the absolute path (to allow for mounting in the docker containers) is obtained from the config file. For example, if the config file specifies:

```
workflows:
    dicom:
        data_sample: "chest_ct"
```

The following will be asserted for the input data (and mounted in the docker container):

```
OUTPUT_BASE_DIR = "/home/mhubai/mhubai_testing/output_data"

# mounted in the container
>>> path_to_output
"/home/mhubai/mhubai_testing/output_data/totalsegmentator/chest_ct/dicom"

```

