from csv import DictReader 
import time, json
from kafka import KafkaProducer
from kafka.errors import KafkaError

producer = KafkaProducer(
        bootstrap_servers = ["localhost:9092"],
        value_serializer = lambda x: json.dumps(x).encode("utf-8")
        )

if __name__ == "__main__":
    with open("Microsoft_Stock.csv", 'r') as read_obj:
        csv_reader = DictReader(read_obj)
    
        for row in csv_reader:
#            print(row)
            row["timestamp"] = time.mktime(time.strptime(row["Date"], "%m/%d/%Y %H:%M:%S"))
            print(row)
            producer.send("prova1", row)
#            try:
#                record_metadata = future.get(timeout=10)
#            except KafkaError:
#                # Decide what to do if produce request failed...
#                log.exception()
#                pass
            time.sleep(0.1)
