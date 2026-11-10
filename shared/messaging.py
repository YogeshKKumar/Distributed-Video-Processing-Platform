import json
import logging
import time
import queue
import threading
from typing import Callable, Any, Optional
import pika
from shared.config import shared_settings
from shared.events import BaseEvent

logger = logging.getLogger("messaging")

class InMemoryBroker:
    """
    High-fidelity asynchronous in-memory message broker.
    Uses background worker thread to process queued messages asynchronously,
    matching RabbitMQ's decoupled async behavior.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(InMemoryBroker, cls).__new__(cls)
                cls._instance._subscribers = {}
                cls._instance._dead_letter_queue = []
                cls._instance._history = []
                cls._instance._queue = queue.Queue()
                cls._instance._running = True
                cls._instance._worker_thread = threading.Thread(
                    target=cls._instance._worker_loop, daemon=True
                )
                cls._instance._worker_thread.start()
            return cls._instance

    def _worker_loop(self):
        while self._running:
            try:
                item = self._queue.get(timeout=0.05)
                routing_key, body_str, callbacks = item
                for cb in callbacks:
                    try:
                        cb(routing_key, body_str)
                    except Exception as e:
                        logger.error(f"[InMemoryBroker] Callback error for {routing_key}: {e}")
                self._queue.task_done()
            except queue.Empty:
                continue

    def publish(self, exchange: str, routing_key: str, body: str | dict):
        if isinstance(body, dict):
            body_str = json.dumps(body)
        else:
            body_str = body

        self._history.append({"exchange": exchange, "routing_key": routing_key, "body": body_str})
        logger.debug(f"[InMemoryBroker] Queued for {routing_key}: {body_str[:80]}...")

        matching_callbacks = []
        for pattern, callbacks in list(self._subscribers.items()):
            if pattern == routing_key or (pattern.endswith(".*") and routing_key.startswith(pattern[:-2])) or pattern == "#":
                matching_callbacks.extend(callbacks)

        if matching_callbacks:
            self._queue.put((routing_key, body_str, matching_callbacks))

    def subscribe(self, routing_key_pattern: str, callback: Callable[[str, str], None]):
        if routing_key_pattern not in self._subscribers:
            self._subscribers[routing_key_pattern] = []
        self._subscribers[routing_key_pattern].append(callback)

    def send_to_dlq(self, routing_key: str, body: str, error: str):
        self._dead_letter_queue.append({
            "routing_key": routing_key,
            "body": body,
            "error": error,
            "timestamp": time.time()
        })
        logger.warning(f"[InMemoryBroker] Sent to DLQ: {routing_key} - Error: {error}")

    def get_dlq_messages(self):
        return list(self._dead_letter_queue)

    def wait_for_idle(self, timeout: float = 3.0):
        """
        Wait for all messages currently in queue to be processed.
        """
        start = time.time()
        while not self._queue.empty():
            time.sleep(0.05)
            if time.time() - start > timeout:
                break
        time.sleep(0.1)

    def clear(self):
        # Empty queue
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                self._queue.task_done()
            except Exception:
                break
        self._subscribers.clear()
        self._dead_letter_queue.clear()
        self._history.clear()


class RabbitMQClient:
    """
    Production-grade RabbitMQ client with DLX, retry handling, and automatic reconnection.
    Falls back gracefully to InMemoryBroker if connection fails or USE_IN_MEMORY_BROKER is set.
    """
    def __init__(self):
        self.settings = shared_settings
        self.in_memory = InMemoryBroker()
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.adapters.blocking_connection.BlockingChannel] = None
        self._connect_lock = threading.Lock()
        self._is_connected = False

        if not self.settings.USE_IN_MEMORY_BROKER:
            self._try_connect()

    def _try_connect(self) -> bool:
        with self._connect_lock:
            if self._is_connected and self.channel and not self.channel.is_closed:
                return True
            try:
                credentials = pika.PlainCredentials(self.settings.RABBITMQ_USER, self.settings.RABBITMQ_PASSWORD)
                parameters = pika.ConnectionParameters(
                    host=self.settings.RABBITMQ_HOST,
                    port=self.settings.RABBITMQ_PORT,
                    credentials=credentials,
                    connection_attempts=15,
                    retry_delay=2,
                    socket_timeout=5,
                    heartbeat=0,
                )
                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()
                self._setup_topology()
                self._is_connected = True
                logger.info("Successfully connected to RabbitMQ.")
                return True
            except Exception as e:
                logger.warning(f"Could not connect to RabbitMQ ({e}). Falling back to InMemoryBroker.")
                self._is_connected = False
                return False

    def _setup_topology(self):
        if not self.channel:
            return

        # Dead Letter Exchange & Queue
        self.channel.exchange_declare(
            exchange=self.settings.DLX_EXCHANGE_NAME,
            exchange_type="direct",
            durable=True,
        )
        self.channel.queue_declare(
            queue=self.settings.DLQ_QUEUE,
            durable=True,
        )
        self.channel.queue_bind(
            queue=self.settings.DLQ_QUEUE,
            exchange=self.settings.DLX_EXCHANGE_NAME,
            routing_key="dlq",
        )

        # Main Topic Exchange
        self.channel.exchange_declare(
            exchange=self.settings.EXCHANGE_NAME,
            exchange_type="topic",
            durable=True,
        )

        # Transcoding Queue with DLX
        self.channel.queue_declare(
            queue=self.settings.TRANSCODING_QUEUE,
            durable=True,
            arguments={
                "x-dead-letter-exchange": self.settings.DLX_EXCHANGE_NAME,
                "x-dead-letter-routing-key": "dlq",
            },
        )
        self.channel.queue_bind(
            queue=self.settings.TRANSCODING_QUEUE,
            exchange=self.settings.EXCHANGE_NAME,
            routing_key=self.settings.ROUTING_KEY_TRANSCODE,
        )

        # Thumbnail Queue with DLX
        self.channel.queue_declare(
            queue=self.settings.THUMBNAIL_QUEUE,
            durable=True,
            arguments={
                "x-dead-letter-exchange": self.settings.DLX_EXCHANGE_NAME,
                "x-dead-letter-routing-key": "dlq",
            },
        )
        self.channel.queue_bind(
            queue=self.settings.THUMBNAIL_QUEUE,
            exchange=self.settings.EXCHANGE_NAME,
            routing_key=self.settings.ROUTING_KEY_THUMBNAIL,
        )

        # Events Queue
        self.channel.queue_declare(
            queue=self.settings.EVENTS_QUEUE,
            durable=True,
        )
        self.channel.queue_bind(
            queue=self.settings.EVENTS_QUEUE,
            exchange=self.settings.EXCHANGE_NAME,
            routing_key="event.*",
        )
        self.channel.queue_bind(
            queue=self.settings.EVENTS_QUEUE,
            exchange=self.settings.EXCHANGE_NAME,
            routing_key="video.uploaded",
        )

    def publish_event(self, routing_key: str, event: BaseEvent):
        body = event.to_json()
        if not self.settings.USE_IN_MEMORY_BROKER:
            for attempt in range(2):
                if not self._is_connected or not self.channel or self.channel.is_closed or not self.connection or self.connection.is_closed:
                    self._try_connect()

                if self._is_connected and self.channel and not self.channel.is_closed:
                    try:
                        self.channel.basic_publish(
                            exchange=self.settings.EXCHANGE_NAME,
                            routing_key=routing_key,
                            body=body.encode("utf-8"),
                            properties=pika.BasicProperties(
                                delivery_mode=2,
                                content_type="application/json",
                            ),
                        )
                        logger.info(f"Published to RabbitMQ [{routing_key}]: {event.event_type}")
                        return
                    except Exception as e:
                        logger.warning(f"Failed to publish to RabbitMQ on attempt {attempt+1} ({e}), reconnecting...")
                        self._is_connected = False
                        if self.connection and not self.connection.is_closed:
                            try:
                                self.connection.close()
                            except Exception:
                                pass

        self.in_memory.publish(self.settings.EXCHANGE_NAME, routing_key, body)

    def subscribe(self, routing_key: str, callback: Callable[[str, str], None]):
        self.in_memory.subscribe(routing_key, callback)
        if not self.settings.USE_IN_MEMORY_BROKER:
            self._start_consumer_thread(routing_key, callback)

    def _start_consumer_thread(self, routing_key: str, callback: Callable[[str, str], None]):
        def run_consumer():
            while True:
                try:
                    credentials = pika.PlainCredentials(self.settings.RABBITMQ_USER, self.settings.RABBITMQ_PASSWORD)
                    params = pika.ConnectionParameters(
                        host=self.settings.RABBITMQ_HOST,
                        port=self.settings.RABBITMQ_PORT,
                        credentials=credentials,
                        connection_attempts=15,
                        retry_delay=2,
                        heartbeat=30,
                    )
                    conn = pika.BlockingConnection(params)
                    ch = conn.channel()

                    if routing_key == self.settings.ROUTING_KEY_TRANSCODE:
                        queue_name = self.settings.TRANSCODING_QUEUE
                    elif routing_key == self.settings.ROUTING_KEY_THUMBNAIL:
                        queue_name = self.settings.THUMBNAIL_QUEUE
                    else:
                        import os
                        service_id = os.environ.get("HOSTNAME", "node")
                        safe_key = routing_key.replace("*", "star").replace("#", "hash")
                        queue_name = f"events_{service_id}_{safe_key}"
                        ch.queue_declare(queue=queue_name, durable=False, auto_delete=True)
                        ch.queue_bind(queue=queue_name, exchange=self.settings.EXCHANGE_NAME, routing_key=routing_key)

                    def on_message(channel, method, properties, body):
                        try:
                            body_str = body.decode("utf-8")
                            callback(method.routing_key, body_str)
                            channel.basic_ack(delivery_tag=method.delivery_tag)
                        except Exception as exc:
                            logger.error(f"Error executing callback for {method.routing_key}: {exc}")
                            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

                    ch.basic_qos(prefetch_count=1)
                    ch.basic_consume(queue=queue_name, on_message_callback=on_message)
                    logger.info(f"Subscribed RabbitMQ consumer on queue '{queue_name}' for routing key '{routing_key}'")
                    ch.start_consuming()
                except Exception as e:
                    logger.warning(f"RabbitMQ consumer connection lost ({e}). Reconnecting in 3 seconds...")
                    time.sleep(3)

        thread = threading.Thread(target=run_consumer, daemon=True)
        thread.start()

    def publish_dlq(self, routing_key: str, body: str, error: str):
        if self._is_connected and self.channel and not self.channel.is_closed:
            try:
                payload = json.dumps({"original_body": body, "error": error, "timestamp": time.time()})
                self.channel.basic_publish(
                    exchange=self.settings.DLX_EXCHANGE_NAME,
                    routing_key="dlq",
                    body=payload.encode("utf-8"),
                    properties=pika.BasicProperties(delivery_mode=2),
                )
                return
            except Exception:
                pass
        self.in_memory.send_to_dlq(routing_key, body, error)


message_broker = RabbitMQClient()
