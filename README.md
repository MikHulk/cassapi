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

# Document Initial Indexing

The document are fetched from DILA repo and indexed in Elastic Search with the dedicated script
`app/scripts/ininitscript.py`. You can run it directly or from a container with propers 
positional arguments.

```
$ python app/scripts/initscript.py --help
usage: initscript.py [-h] url dir index

Fetch data from the specified source url and indexes the document under the specified index in Elastic Search

positional arguments:
  url         the url where fetch xml documents
  dir         the working dir where files will be processed
  index       the index under which documents will be indexed

options:
  -h, --help  show this help message and exit
```

an example:

```
$ python app/scripts/initscript.py https://echanges.dila.gouv.fr/OPENDATA/CASS/ . demo
fetch CASS_20231125-130812.tar.gz
fetch CASS_20231127-204209.tar.gz
fetch CASS_20231204-205306.tar.gz
fetch CASS_20231211-211048.tar.gz
fetch CASS_20231218-205651.tar.gz
fetch CASS_20240101-200918.tar.gz
fetch CASS_20240108-211850.tar.gz
...
process 20240325-204641
process 20240408-211446
20231125-130812  92 processed,  92 created,   0 updated,   0 on error and   0 errors on parsing
20231127-204209  53 processed,  43 created,  10 updated,   0 on error and   0 errors on parsing
20231204-205306  55 processed,  13 created,  42 updated,   0 on error and   0 errors on parsing
20231211-211048  84 processed,  51 created,  33 updated,   0 on error and   0 errors on parsing
20231218-205651 113 processed,  41 created,  72 updated,   0 on error and   0 errors on parsing
20240101-200918 130 processed, 102 created,  28 updated,   0 on error and   0 errors on parsing
20240108-211850  58 processed,   2 created,  56 updated,   0 on error and   0 errors on parsing
20240115-204455 113 processed,  34 created,  79 updated,   0 on error and   0 errors on parsing
20240122-202244 114 processed,  38 created,  76 updated,   0 on error and   0 errors on parsing
20240129-204426  64 processed,  32 created,  32 updated,   0 on error and   0 errors on parsing
20240205-205927  71 processed,  30 created,  41 updated,   0 on error and   0 errors on parsing
20240212-210229  89 processed,  40 created,  49 updated,   0 on error and   0 errors on parsing
20240219-204359 132 processed,  29 created, 103 updated,   0 on error and   0 errors on parsing
20240226-204034  42 processed,   3 created,  39 updated,   0 on error and   0 errors on parsing
20240228-205615   0 processed,   0 created,   0 updated,   0 on error and   0 errors on parsing
20240304-203843   7 processed,   4 created,   3 updated,   0 on error and   0 errors on parsing
20240311-205444  77 processed,  39 created,  38 updated,   0 on error and   0 errors on parsing
20240318-210947  95 processed,  42 created,  53 updated,   0 on error and   0 errors on parsing
20240319-205938  13 processed,  13 created,   0 updated,   0 on error and   0 errors on parsing
20240321-212125   1 processed,   0 created,   1 updated,   0 on error and   0 errors on parsing
20240325-204641  98 processed,  30 created,  68 updated,   0 on error and   0 errors on parsing
20240408-211446  90 processed,  47 created,  43 updated,   0 on error and   0 errors on parsing
clean? y
bye
```

At the end the script show a report and asks for working dir removal. You can say y and the 
fetched and extracted files will be removed. If you need to keep these file just answer 
something else and files will be available under the folder `./work-YYMMDD` under the path
you passed with `dir` positional argument.


# Rootless Podman Howto

With Podman we can run a pod with ES and the app in two rootless containers sharing 
the same network space.

1. We create a new pod with the ports we want to expose (note we expose both ES and api ports):
```
$ podman pod create -p 9200:9200 -p 9300:9300 -p 8000:80 cassapod
```
2. Then start ES:
```
$ podman run --name es02 --pod cassapod  \
  -e "discovery.type=single-node" \
  -t docker.elastic.co/elasticsearch/elasticsearch:8.13.2
```
3. We create a sharing folder for the ES certificate and an env file (we add the PYTHONPATH 
   to run the script see bellow):
```
$ mkdir share
$ cat env
ELASTIC_CERTS_PATH=/usr/local/cassapi/http_ca.crt
ELASTIC_USER=elastic
ELASTIC_URL=https://localhost:9200
ELASTIC_PASSWORD=es_password_here
ELASTIC_INDEX=testjuri
ADMIN_PASSWORD=admin_api_password_there
ADMIN_USER=test
PYTHONPATH=/usr/src/app
```
4. Then copy ES certificate in the sharing folder:
```
$ podman cp es02:/usr/share/elasticsearch/config/certs/http_ca.crt ./share/
```
5. We can run the api container(built from the Docker file see the docker section):
```
$ podman run --pod cassapod  --name cassapi -v ./share:/usr/local/cassapi --env-file env cassapi
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:80 (Press CTRL+C to quit)
INFO:     Shutting down
INFO:     Waiting for application shutdown.
INFO:     Application shutdown complete.
INFO:     Finished server process [1]
```
6. Now we can indexe document from dila repo from the container:
```
$ podman exec -it cassapi bash
root@cassapod:/usr/src/app# echo $PYTHONPATH
/usr/app
root@cassapod:/usr/src/app# PYTHONPATH=/usr/src/app python app/scripts/initscript.py https://echanges.dila.gouv.fr/OPENDATA/CASS/ . testjuri
fetch CASS_20231125-130812.tar.gz
fetch CASS_20231127-204209.tar.gz
fetch CASS_20231204-205306.tar.gz
fetch CASS_20231211-211048.tar.gz
...
20240408-211446  90 processed,  47 created,  43 updated,   0 on error and   0 errors on parsing
clean? y
bye
root@cassapod:/usr/src/app# exit
```
7. Check the API with
```
curl  -v -u test:password_here http://127.0.0.1:8000/summary?page=8 | python -m json.tool --no-ensure-ascii
```
   You should get a list of court decisions as expected:
```
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0*   Trying 127.0.0.1:8000...
* Connected to 127.0.0.1 (127.0.0.1) port 8000
* Server auth using Basic with user 'test'
> GET /summary?page=8 HTTP/1.1
> Host: 127.0.0.1:8000
> Authorization: Basic fjkljhfedkhjze
> User-Agent: curl/8.4.0
> Accept: */*
> 
< HTTP/1.1 200 OK
< date: Sun, 14 Apr 2024 16:58:05 GMT
< server: uvicorn
< content-length: 4532
< content-type: application/json
< 
{ [4532 bytes data]
100  4532  100  4532    0     0  16924      0 --:--:-- --:--:-- --:--:-- 16973
* Connection #0 to host 127.0.0.1 left intact
{
    "stats": {
        "count": 25,
        "total": 725,
        "page": 8,
        "page_size": 100,
        "total_page": 8
    },
    "decisions": [
        {
            "title": "Cour de cassation, Chambre mixte, ...",
            "identifier": "JURITEXTxxxxxxx",
            "code_chambre": "CHAMBRE_MIXTE"
        },
...
```

## Start and Stop the pod

To stop the pod(and all containers into):
```
$ podman pod stop cassapod
```
To restart:
```
$ podman pod start cassapod
```
