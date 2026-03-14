# producer.py
import pika

print("Starting Producer...")

connection = pika.BlockingConnection(
    pika.ConnectionParameters('localhost')
)
channel = connection.channel()

channel.queue_declare(queue='url_queue', durable=True)

seed_urls = [
    "https://realpython.com/python-web-scraping-practical-introduction/",
    "https://www.geeksforgeeks.org/web-scraping-with-python/"
]

for url in seed_urls:
    channel.basic_publish(
        exchange='',
        routing_key='url_queue',
        body=url,
        properties=pika.BasicProperties(
            delivery_mode=2, 
        )
    )
    print("Sent:", url)

connection.close()
print("Producer Finished")
