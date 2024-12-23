# Kafka time series ETL

Small proof of concept for a Kafka streaming ETL, on Docker (December 2021).

- Kafka container has been downloaded from the [DockerHub](https://hub.docker.com/r/confluentinc/cp-kafka). The topics can be either be created by accessing the container (with `docker exec`) or simply by writing something to a non-existing topic (the topic will be created automatically). Note that for Kafka to run [Zookeeper](https://hub.docker.com/r/confluentinc/cp-zookeeper) is necessary.
- Data is then processed by [Telegraf](https://hub.docker.com/_/telegraf) in order to be sent to InfluxDB. The Telegraf configuration file is stored in `telegraf/telegraf.conf` on the host machine and mounted as a volume on `/etc/telegraf/telegraf.conf` in the container. In order to be sure to read from the correct topic, this has to be set in the configuration file. The metrics to "consume" are hard-coded in the Telegraf configuration file, as well as the Influx bucket to write to, and the login credentials to the Influx database.
- The [Influx database](https://hub.docker.com/_/influxdb) is automatically created in the docker compose file, where I set an admin username, access token and password, an organisation, and a default bucket. The InfluxDB dashboard can be accessed at [http://localhost:8086](http://localhost:8086), the default username is `admin` and the password is `administrator`. The database has been mounted in the `influxdb` directory. Remember to create a configuration inside the Influx container to perform tasks like deletion of data. Here is an example of configuration:
```
influx config create --config-name default_config --host-url http://localhost:8086 --org microsoft --token aaaaa --active
```

- The Python image is based on the one on the [DockerHub](https://hub.docker.com/_/python): I have created a new image using a Dockerfile (in `python/Dockerfile`). It copies the `python/` directory content inside the container, runs `pip install -r requirements.txt`, and it runs `app.py`. At the moment, a volume is mounted on home of the container, for development purposes. `app.py` reads the configuration file (database access token, organisation, bucket), reads all data from the database, and creates a new bucket (whose name is saved in the config file) to output its results (a weekly rolling mean of the data). After that, it checks every 10 seconds if new data has been added to the database: if it has, the script calculates the rolling mean for the new points.
- Finally, a [Grafana](https://hub.docker.com/grafana/grafana) container has been added: at the moment, the only way to connect Grafana to the database seems to be manually via GUI. Remember to set http://influxdb:8086 as URL, to untoggle any auth buttons, and to set organisation and token in the InfluxDB details, in order to configure InfluxDB as a source for Grafana.

In the test folder, a simple Python script - `producer.py` - is available, which loads data of Microsoft shares from a csv file and sends a line of it every second to Kafka, in order to check the functionality of the architecture. A second script is available - `consumer.py` - which checks what Kafka outputs to Telegraf. A `requirements.txt` file is available.

To start the whole architecture, it should be enough to type
```
docker-compose up
```

NOTE: The credentials of the Influx database are in clear text in the docker-compose file, the Telegraf configuration file, and in the Python configuration file. Maybe this has to be checked in future.

NOTE2: `help.txt` contains some useful links I have visited to set up the infrastructure.
