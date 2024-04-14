# Development

## Getting started

You can start in a new virtualenv and "pip install" the requirement:

```sh
pip install -r requirements.txt
```

> [!IMPORTANT]
> You need an Elastic Search cluster to connect to. And you MUST set some env
> variables in your environment if you want to use client and async client 
> provided by the `es` module:
>    - `ELASTIC_CERTS_PATH` for the client certificate,
>    - `ELASTIC_USER` for the user,
>    - `ELASTIC_PASSWORD` for the password,
>    - `ELASTIC_URL` for the url,
    
It might be convenient to set up an init file. 
By instance this one load these variables, source the python virtual env 
add app folder in `PYTHONPATH`(useful to run the script) in one "source" command
(`source [myenvfile]`):

```sh
export ELASTIC_CERTS_PATH="$PROJECT_ROOT/http_ca.crt"
export ELASTIC_USER="elastic"
export ELASTIC_URL="https://localhost:9200"
export ELASTIC_PASSWORD="yourpassword"
export PYTHONPATH=$PROJECT_ROOT/app
source ./.pyenv/bin/activate
```

Alternatively and only from the repl, for testing purpose, the config can be
passed to `es.get_client` function (see `app/es.py` module):

```python
>>> config = {
...   "user": "elastic",
...   "passwd": "yourpassword",
...   "url": "https://localhost:9200",
...   "ca_certs": "./http_ca.crt",
... }
>>> c = get_client(config)
>>> c.info()
ObjectApiResponse({'name': '860166a0e06e', 'cluster_name': 'docker-cluster', 'cluster_uuid': 'qK9yhtVFSLuWdPGPJtXZEQ', 'version': {'number': '8.13.2', 'build_flavor': 'default', 'build_type': 'docker', 'build_hash': '16cc90cd2d08a3147ce02b07e50894bc060a4cbf', 'build_date': '2024-04-05T14:45:26.420424304Z', 'build_snapshot': False, 'lucene_version': '9.10.0', 'minimum_wire_compatibility_version': '7.17.0', 'minimum_index_compatibility_version': '7.0.0'}, 'tagline': 'You Know, for Search'})
>>>
```

## Documentation

Each module have a documentation and can be read with `pydoc` from the terminal:

```sh
python -m pydoc app/scripts/initscript.py
```

## Running tests

> [!IMPORTANT]
> Since the app relies intensively on Elastic Search a working cluster is
> mandatory to run the tests.
> You have to set up your environment as described in the previous section.

Once this is done test can be run with pytest from the project root:

```sh
pytest app
```


> [!TIP]
> The test create a specific index for each test with a random name and remove
> it after.

# Container

> [!IMPORTANT]
> I am using podman here but these instructions are easily transposable to docker or
> kubernetes. The Dockerfile is no more no less a "classic" docker file and will work
> with docker.

One can build a new image from the provided Dockerfile.

```
podman build -t cassapi .
```

Certificat for Elastic search, network or pod configuration and environment variable
have to be specified at **run time**. A dir is available as mount point in the container
`/usr/local/cassapi` to share data.

By instance here we put the es certificate in `./dockershare` and share it with the container.
We pass an env file for credentials too with `env-file` option:

```
podman run --pod cassapod --rm --name cassapi \
    -v ./dockershare:/usr/local/cassapi --env-file dockerenv cassapi
```


