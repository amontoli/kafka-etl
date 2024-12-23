import pandas as pd
import time, datetime, logging
from configparser import ConfigParser 
from influxdb_client import InfluxDBClient

logging.basicConfig(filename = "logs/app.log", filemode = 'w',
                    format='%(asctime)s - %(levelname)s: %(message)s', 
                    datefmt='%d-%b-%y %H:%M:%S',
                    level = logging.DEBUG)

# Read InfluxDB parameters 
config = ConfigParser()
config.read("conf/influxdb.ini")
org = config.get("main", "org")
bucket_raw = config.get("main", "bucket_raw")  # Raw data bucket
bucket_out = config.get("main", "bucket_out")  # Data output by Python
token = config.get("main", "token")
url = config.get("main", "url")


client = InfluxDBClient(url = url, token=token, org=org)
query_api = client.query_api()
write_api = client.write_api()

################################################################################
# Read all data available
################################################################################

logging.info("Read all available data")

query = f'from(bucket: "{bucket_raw}")\
  |> range(start: 2014-01-28T22:00:00Z, stop: now())\
  |> filter(fn: (r) => r["_measurement"] == "Microsoft_stocks")\
  |> filter(fn: (r) => r["_field"] != "timestamp")'

## Print data row by row
#result = client.query_api().query(org = org, query = query)
#
#for table in result:
#    for record in table.records:
#        print(record)


df = client.query_api().query_data_frame(org = org, query = query)

cleaned_df = df.pivot_table(values = "_value", index = "_time", columns = "_field", aggfunc = "first")
cleaned_df.index = pd.to_datetime(cleaned_df.index)
cleaned_df.sort_index(inplace = True)
rolled_df = cleaned_df.rolling("7d").mean()

##### Create bucket
buckets_api = client.buckets_api()
try:
##    retention_rules = BucketRetentionRules(type="expire", every_seconds=3600)
    buckets_api.create_bucket(bucket_name = bucket_out, org = org)
    logging.info(f"New bucket {bucket_out} created")
except Exception as e:
    logging.info(f"Impossible to create new bucket {bucket_out}, it already exists!")

write_api.write(bucket_out, org, record = rolled_df,
        data_frame_measurement_name = "Microsoft rolled")

write_api.close()
logging.info(f"Data elaborated, last datapoint on {cleaned_df.index[-1]}")

# Dirty way to perform a listener: a cleaner way would be that of using the rx library. See:
# - https://github.com/influxdata/influxdb-client-python/blob/master/examples/iot_sensor.py
# - https://github.com/influxdata/influxdb-client-python/blob/master/notebooks/realtime-stream.ipynb
# for a couple of examples.

logging.debug("Entering main cycle")
while True:
    # Find new data added after the last element.
    # Last element has to be formatted to perform the query.
    last_element = (cleaned_df.index[-1] + datetime.timedelta(seconds = 1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    time.sleep(10) # TO CHECK: sleep time set

    query = f'from(bucket: "{bucket_raw}")\
      |> range(start: {last_element}, stop: now())\
      |> filter(fn: (r) => r["_measurement"] == "Microsoft_stocks")\
      |> filter(fn: (r) => r["_field"] != "timestamp")'

    df = client.query_api().query_data_frame(org = org, query = query)

    # Check if new data is available:
    if df.empty:
        logging.debug("Database check: no new data")
        continue

    df = df.pivot_table(values = "_value", index = "_time",
                        columns = "_field", aggfunc = "first")

    len_df = len(df) # Check how many new datapoints have been added

    ### TO CHECK: since we are performing a rolling mean on weekly basis,
    # we keep only the last 10 points in the dataframe.
    cleaned_df = cleaned_df[-10:].append(df)
    cleaned_df.index = pd.to_datetime(cleaned_df.index)
    cleaned_df.sort_index(inplace = True)
    rolled_df = cleaned_df.rolling("7d").mean()[-len_df:]

    write_api = client.write_api()
    write_api.write(bucket_out, org, record = rolled_df,
            data_frame_measurement_name = "Microsoft rolled")
    write_api.close()
    logging.info(f"Data elaborated, last datapoint on {cleaned_df.index[-1]}")
