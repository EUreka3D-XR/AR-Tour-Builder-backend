# EUreka3D-XR AR Tour Builder Backend

To deploy this application call `EUREKA_PORT=2345 docker compose up`
Or choose whatever port you like (if you dont specify one, the default is 8000, see docker-compose.yml file)

If there are changes in the requirements.txt then you need to `EUREKA_PORT=2345 docker compose build web` in order
to force re-run `pip install -r requirements.txt`

If its the first time, some more steps are involved to configure the database of the app:

Find the container of the django app, it should be `eureka-backend-web-1` or something very similar.
Do a `docker container ls | grep eureka` to be sure.

Execute a shell in the container with `docker exec -it eureka-backend-web-1 bash`

Run `python manage.py migrate`
and
`python manage.py createsuperuser` and interactively provide some superuser detail. This user can access the django admin web UI.

Get some useful documentation at `http://localhost:EUREKA_PORT/api/docs`

Some exmaples on how to use the API will be collected in `src/eureka/tests/integrations`

## Run checks and tests

### Checks

`docker exec eureka-backend-web-1 bash -c "python manage.py check"`

### Tests

Run this command to run current tests and save them to a test_errors.txt in order to help Claude read the results
`docker exec eureka-backend-web-1 bash -c "python manage.py test eureka --keepdb 2>&1" > test_errors.txt`

Or if you just wanna run the tests:
`docker exec eureka-backend-web-1 bash -c "python manage.py test eureka --keepdb 2>&1"`
