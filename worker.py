import pika
import requests
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

print("Worker Starting...")

MAX_URLS = 10
visited = set()

connection = pika.BlockingConnection(
    pika.ConnectionParameters('localhost')
    
)
channel = connection.channel()

# Declare queue

channel.queue_declare(queue='url_queue', durable=True)

def callback(ch, method, properties, body):
    global visited

    worker_id = os.getpid()   # 👈 Identify worker
    url = body.decode()

    print(f"\n🟢 Worker {worker_id} received: {url}")

    # Stop if crawl limit reached
    if len(visited) >= MAX_URLS:
        print(f"🔴 Worker {worker_id}: Crawl limit reached. Stopping...")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        channel.stop_consuming()
        return

    # Skip if already visited
    if url in visited:
        print(f"⚠ Worker {worker_id}: Already visited {url}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    try:
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            print(f"✅ Worker {worker_id} fetched: {url}")

            os.makedirs("pages", exist_ok=True)

            parsed = urlparse(url)
            domain = parsed.netloc
            filename = f"pages/{domain}_{len(visited)}.html"

            with open(filename, "w", encoding="utf-8") as f:
                f.write(response.text)

            print(f"💾 Worker {worker_id} saved: {filename}")

            visited.add(url)

            soup = BeautifulSoup(response.text, "html.parser")

            # Extract and republish links
            for link in soup.find_all("a", href=True):
                new_url = urljoin(url, link['href'])

                # Stay within same domain
                if urlparse(new_url).netloc == domain:
                    if new_url not in visited:
                        channel.basic_publish(
                            exchange='',
                            routing_key='url_queue',
                            body=new_url,
                            properties=pika.BasicProperties(
                                delivery_mode=2,
                            )
                        )
                        print(f"🔁 Worker {worker_id} requeued: {new_url}")

    except Exception as e:
        print(f"❌ Worker {worker_id} error: {e}")

    ch.basic_ack(delivery_tag=method.delivery_tag)


# Fair distribution
channel.basic_qos(prefetch_count=1)

channel.basic_consume(
    queue='url_queue',
    on_message_callback=callback
)

print("Waiting for URLs...")
channel.start_consuming()

connection.close()
print("Worker stopped automatically.")
