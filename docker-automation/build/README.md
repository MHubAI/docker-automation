# MHub Container Automated Building Pipeline

```
usage: run.py [-h] [--verbose] [--dryrun] [--ncores NCORES] [--branch BRANCH] --config CONFIG

MHub - automated building of MHub containers

optional arguments:
  -h, --help       show this help message and exit
  --verbose        enable verbose mode
  --dryrun         execute in dry run mode
  --ncores NCORES  number of cores to execute on (max is 128)
  --branch BRANCH  name of the branch to build the images from
  --config CONFIG  path to config file
```

Example command (from the `docker-automation` folder):

```
python build_and_push/run.py --config build_and_push/config/dev.yaml --dryrun --branch patch-models
```

## Config file

The config file will be used to specify the parameters for building the Docker images. The config file is a YAML file with the following structure:

- DockerHub Username (`dockerhub.username`): This parameter specifies the DockerHub username that will be used for tagging the MHub images.

- GitHub Repository Folder (`github.repository_folder`): This parameter specifies the local path of the Git repository on the node where the script is executed. The script will build Docker images from this repository.

- GitHub Repository URL (`github.repository_url`): This parameter specifies the URL of the GitHub repository that corresponds to the local repository folder mentioned above. This is used for cloning and fetching the latest code from GitHub.

- Images to Build (`images`): This section defines the Docker images that will be built. It consists of a dictionary with keys representing the names of the images to be built. Each image has the following attributes:
  - `name`: The name of the Docker image.
  - `version`: The version or tag to be used when tagging the built Docker image.
  - `dockerfile`: The relative path (with respect to the `github.repository_folder` folder) to the Dockerfile that should be used for building the image.

An example of config file is shown below:

```
dockerhub:
    username: mhubai

github:
    repository_folder: /home/mhubai/git/mhubai-org/models
    repository_url: https://github.com/MHubAI/models

images:
    base:
        name: base
        version: latest
        dockerfile: base/dockerfiles/Dockerfile

    platipy:
        name: platipy
        version: latest
        dockerfile: models/platipy/dockerfiles/Dockerfile
```

## Example Output

```
python build_and_push/run.py --config build_and_push/config/dev.yaml --dryrun --ncores 1

git pull /home/mhubai/git/mhubai-org/models 

This will run on a single core.

docker build
{ 'dockerfile': 'base/dockerfiles/Dockerfile',
  'dockerhub_username': 'mhubai',
  'name': 'base',
  'repository_folder': '/home/mhubai/git/mhubai-org/models',
  'version': 'latest'}

docker build
{ 'dockerfile': 'models/platipy/dockerfiles/Dockerfile',
  'dockerhub_username': 'mhubai',
  'name': 'platipy',
  'repository_folder': '/home/mhubai/git/mhubai-org/models',
  'version': 'latest'}
```

```
python build_and_push/run.py --config build_and_push/config/dev.yaml --dryrun --branch patch-models

git pull /home/mhubai/git/mhubai-org/models 

This will run in parallel, on 4 cores.

docker build
docker build
{ 'dockerfile': 'base/dockerfiles/Dockerfile',
  'dockerhub_username': 'mhubai',
  'name': 'base',
  'repository_folder': '/home/mhubai/git/mhubai-org/models',
  'version': 'patch-models'}

{ 'dockerfile': 'models/platipy/dockerfiles/Dockerfile',
  'dockerhub_username': 'mhubai',
  'name': 'platipy',
  'repository_folder': '/home/mhubai/git/mhubai-org/models',
  'version': 'patch-models'}
```