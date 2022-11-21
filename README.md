# JPMovies

Module with a worker to fetch / store movies and a Rest API for retrieving them.

## Requirements

- Python3
- Mysql Database Instance
- Kubernetes Cluster

## Database Design

For the database backend, Mysql has been chosen.
Movie updates are stored serialized into the main movie table to allow quick retrieval of the items without extra join overhead.
The expected querying is supported as following:

- title: single object directly using the movie table
- year: single object directly using the movie table
- cast: using the extra lookup table movie_cast. Many-to-Many relationship
- genre:  using the extra lookup table movie_genre. Many-to-Many relationship

To have performant pagination, the API is not using `pages` and `ORDER BY LIMIT`, but instead it filters the results using the `start` query parameter which indicates the `id` of the movie that should be used as the cursor filter.

## Worker

Worker is a single thread script that performs the following operations in a non ending loop:

1. Fetch **x** items from bucket.
2. Parse the items contents. Invalid formatted items are deleted.
3. Update database for each item.
4. After the update has been processed and stored in our database, the item is removed from the s3 bucket.

Worker is able to handle `duplicate updates`. If a movie has already been created, then it will be updated.

Movie updates can be `partial` eg: empty genres and then a new update to contain the values.

Also worker will remove cast and genres that `no longer exist`, or append `new ones`.

Worker will try to gracefully stop, to avoid leaving updates in the middlel. However in case this happens it will not cause any data corruption as worker will be able to resume successully and reprocess the data from the S3 bucket.

```bash
$ testmovies4444 make run_worker
INFO:botocore.credentials:Found credentials in shared credentials file: ~/.aws/credentials
INFO:root:Parsed 0 movie updates
INFO:root:Sleeping for 60 seconds
^CStopping worker. Press one more time to exit immediately!
INFO:root:Manager stoppped
```

## Api

The API can be used to fetch movies. Please note that matching is case sensitive and has to match the full world. Support for more sophisticated filtering is out of scope and would require the use of extra indexers.

The API contains the following handles:

Index

```bash
$ curl -s http://127.0.0.1:8080/ | jq .
{
  "movies_url": "/movies"
}
```

Movies

```bash
$ curl -s http://127.0.0.1:8080/movies | jq .
{
  "movies": [
    {
      "id": 12,
      "title": "The Telemarketing",
      "year": 2021,
      "cast": [
        "AB Nick",
        "Mark Zei"
      ],
      "genres": [
        "Politics"
      ],
      "self_url": "/movies/12"
    },
    ...
    {
      "id": 7,
      "title": "Avengers: Age of Ultron",
      "year": 2015,
      "cast": [
        "Robert Downey, Jr.",
        "Chris Evans",
        "Chris Hemsworth",
        "Mark Ruffalo"
      ],
      "genres": [
        "Action"
      ],
      "self_url": "/movies/7"
    }
  ],
  "next_url": null
}
```

Search using limit

```bash
$ curl -s "http://127.0.0.1:8080/movies?limit=2" | jq .
{
  "movies": [
    {
      "id": 12,
      "title": "The Telemarketing",
      "year": 2021,
      "cast": [
        "AB Nick",
        "Mark Zei"
      ],
      "genres": [
        "Politics"
      ],
      "self_url": "/movies/12"
    },
    {
      "id": 11,
      "title": "The mystery meat",
      "year": 2021,
      "cast": [
        "AB Nick",
      ],
      "genres": [
        "Food"
      ],
      "self_url": "/movies/11"
    }
  ],
  "next_url": "/movies?limit=2&start=11"
}
```

Filter based on title

```bash
$ curl -s "http://127.0.0.1:8080/movies?title=The+dawn" | jq .
{
  "movies": [
    {
      "id": 10,
      "title": "The dawn",
      "year": 2020,
      "cast": [
        "Chris Ruf",
        "Mark Zei"
      ],
      "genres": [
        "Politics"
      ],
      "self_url": "/movies/10"
    }
  ],
  "next_url": null
}
```

Filter based on year

```bash
$ curl -s "http://127.0.0.1:8080/movies?year=2017" | jq .
{
  "movies": [
    {
      "id": 9,
      "title": "A new marathon",
      "year": 2017,
      "cast": [
        "Chris Evans",
        "Mark Ruffalo"
      ],
      "genres": [
        "Action"
      ],
      "self_url": "/movies/9"
    }
  ],
  "next_url": null
}
```

Filter based on genre

```bash
$ curl -s "http://127.0.0.1:8080/movies?genre=Action" | jq .
{
  "movies": [
    {
      "id": 9,
      "title": "A new marathon",
      "year": 2017,
      "cast": [
        "Chris Evans",
        "Mark Ruffalo"
      ],
      "genres": [
        "Action"
      ],
      "self_url": "/movies/9"
    },
    {
      "id": 7,
      "title": "Avengers: Age of Ultron",
      "year": 2015,
      "cast": [
        "Robert Downey, Jr.",
        "Chris Evans",
        "Chris Hemsworth",
        "Mark Ruffalo"
      ],
      "genres": [
        "Action"
      ],
      "self_url": "/movies/7"
    }
  ],
  "next_url": null
}
```

Filter based on cast

```bash
$ curl -s "http://127.0.0.1:8080/movies?cast=Mark+Zei" | jq .
{
  "movies": [
    {
      "id": 12,
      "title": "The Telemarketing",
      "year": 2021,
      "cast": [
        "Guga Foods",
        "Mark Zei"
      ],
      "genres": [
        "Politics"
      ],
      "self_url": "/movies/12"
    },
    {
      "id": 10,
      "title": "The dawn",
      "year": 2020,
      "cast": [
        "Chris Ruf",
        "Mark Zei"
      ],
      "genres": [
        "Politics"
      ],
      "self_url": "/movies/10"
    }
  ],
  "next_url": null
}
```

Using multiple filters

```bash
$ curl -s "http://127.0.0.1:8080/movies?genre=Action&year=2015" | jq .
{
  "movies": [
    {
      "id": 7,
      "title": "Avengers: Age of Ultron",
      "year": 2015,
      "cast": [
        "Robert Downey, Jr.",
        "Chris Evans",
        "Chris Hemsworth",
        "Mark Ruffalo"
      ],
      "genres": [
        "Action"
      ],
      "self_url": "/movies/7"
    }
  ],
  "next_url": null
}
```

Single Movie

```bash
curl -s http://127.0.0.1:8080/movies/7 | jq .
{
  "id": 7,
  "title": "Avengers: Age of Ultron",
  "year": 2015,
  "cast": [
    "Robert Downey, Jr.",
    "Chris Evans",
    "Chris Hemsworth",
    "Mark Ruffalo"
  ],
  "genres": [
    "Action"
  ],
  "self_url": "/movies/7"
}
```

## How to develop

Although it is not needed to use a virtualenv, it is recommended.

First install the required dependencies:

```bash
pip install -r requirements/base.txt
pip install -r requirements/dev.txt
```

Then open a mysql client to your database and update the schema from `db.sql`

Then populate and export the following environment variables:

```text
MOVIES_DB_USER=<user>
MOVIES_DB_PASS=<pass>
MOVIES_DB_NAME=movies
MOVIES_DB_HOST=127.0.0.1
MOVIES_DB_PORT=3306
MOVIES_BUCKET_NAME=<bucket_name> 
```

To allow worker use S3, you will need to configure your aws credentials or export the following environment variables:

```text
AWS_ACCESS_KEY_ID: <access_key>
AWS_SECRET_ACCESS_KEY: <secret_key>
```

Then to run the worker, you can use the following command:

```bash
$ make run_worker
INFO:botocore.credentials:Found credentials in shared credentials file: ~/.aws/credentials
INFO:root:Parsed 0 movie updates
INFO:root:Sleeping for 60 seconds
```

To run the api, you can use the following command:

```bash
$ make run_api
 * Serving Flask app 'jpmovies.api'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on http://127.0.0.1:8080
Press CTRL+C to quit
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: 539-905-859
```

## How to lint the source code

To lint the source code, run the following command:

```bash
make lint
--------------------------------------------------------------------
Your code has been rated at 10.00/10 (previous run: 10.00/10, +0.00)

ok
```

## How to run the unit tests

The following command will run the unit tests:

```bash
$ make test
Sorry no tests has been added :(
```

## Repository structure

- jpmovies = the module's code
- run_worker.py = entrypoint script that is used to execute the worker
- deployment = Docker and K8s files
- scripts = development helper scripts
- db.sql = the database schema
- Makefile = the Makefile does not include code, but it only executes the scripts
- README.md = the Readme file
- design.png = the design diagram
- requirements/base.txt = the main requirements of the tool
- requirements/dev.txt = extra requirements for lint/test etc
- tests = the folder that contains the unit tests

## Code structure

The code is split into:

- the worker, which is responsible for fetching the updates and store them in db
- the api, which is the code that handles the rest api
- the database, which contains helper functions for the database queries
- the models, which are classes representing db and api models

## Deploying to Kubernetes

If you have a K8s cluster (eg: using minikube), you can quickly build and deploy to it.

Three pods for the API will be created and only one for the worker (to keep things simple).

First create the secrets manually:

```text
apiVersion: v1
kind: Secret
metadata:
  name: movies-worker
type: Opaque
data:
  AWS_ACCESS_KEY_ID: <access_key>
  AWS_SECRET_ACCESS_KEY: <secret_key>
  MOVIES_DB_PASS: <db_pass>
```

```text
apiVersion: v1
kind: Secret
metadata:
  name: movies-api
type: Opaque
data:
  MOVIES_DB_PASS: <db_pass>
```

Then build the docker images and deploy, using the following commands:

```bash
$ make build
Successfully built faf1da4d2d91
Successfully tagged movies-worker:local
...
Successfully built e774279a22ed
Successfully tagged movies-api:local
```

```bash
$ make deploy
deployment.apps "movies-worker" deleted
deployment.apps/movies-worker replaced
configmap "movies-worker" deleted
configmap/movies-worker replaced
deployment.apps "movies-api" deleted
deployment.apps/movies-api replaced
service/movies-api unchanged
```

```bash
$ kubectl get pods
NAME                                               READY   STATUS    RESTARTS        AGE
movies-api-556b4fcc85-hjbd7                        1/1     Running   0               52s
movies-api-556b4fcc85-ppsmw                        1/1     Running   0               52s
movies-api-556b4fcc85-td7dp                        1/1     Running   0               52s
movies-worker-796fcb699c-wrnn9                     1/1     Running   0               52s
```

To use the worker-api service, you can use the following command:

```bash
$ minikube service movies-api
|-----------|------------|-------------|---------------------------|
| NAMESPACE |    NAME    | TARGET PORT |            URL            |
|-----------|------------|-------------|---------------------------|
| default   | movies-api |        8080 | http://192.168.49.2:30000 |
|-----------|------------|-------------|---------------------------|
🏃  Starting tunnel for service movies-api.
|-----------|------------|-------------|------------------------|
| NAMESPACE |    NAME    | TARGET PORT |          URL           |
|-----------|------------|-------------|------------------------|
| default   | movies-api |             | http://127.0.0.1:64257 |
|-----------|------------|-------------|------------------------|
🎉  Opening service default/movies-api in default browser...
❗  Because you are using a Docker driver on darwin, the terminal needs to be open to run it.
```
