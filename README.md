# docker-automation

Tools for automating various MHubAI-related docker actions from a local node (and GitHub actions).


## Automated Testing



## Build and Push

Before running the script, make sure the repository to which the script is pointing to is up to date (it should pull automatically anyways, but still). On W2-S1, the path to the repository should be:

```
/home/mhub/git/mhubai-org/models
```

To run the script, `cd` in the source directory of the docker-automation repository and run the following:

```
# exec a dryrun before the actual build and push run
python run.py --push --config ../config/build_all.yaml --dryrun

# run the script 
python run.py --push --config ../config/build_all.yaml

```


The first command runs a dry run so the user can check everything looks good. Once that checks out, you're free to run the second command.
