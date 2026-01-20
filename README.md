# EUreka3D-XR AR Tour Builder Backend

To deploy this application call `EUREKA_PORT=2345 docker compose up`
Or choose whatever port you like (if you dont specify one, the default is 8000, see docker-compose.yml file)

If its the first time, some more steps are involved to configure the database of the app:

Find the container of the django app, it should be `eureka-backend-web-1` or something very similar.
Do a `docker container ls | grep eureka` to be sure.

Execute a shell in the container with `docker exec -it eureka-backend-web-1 bash`

Run `python manage.py migrate`
and
`python manage.py createsuperuser` and interactively provide some superuser detail. This user can access the django admin web UI.

Get some useful documentation at `http://localhost:EUREKA_PORT/api/docs`

Some exmaples on how to use the API will be collected in `src/eureka/tests/integrations`



