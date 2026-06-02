"""
Quick script to check Kafka status and consumer groups
"""
import os
from dotenv import load_dotenv
from kafka import KafkaAdminClient, KafkaConsumer
from kafka.admin import ConsumerGroupDescription

load_dotenv()

KAFKA_SERVER = os.getenv('KAFKA_BOOTSTRAP_SERVER', 'localhost:9092')
TOPIC_NAME = 'air_quality_stream'

def check_kafka_status():
    print("=" * 60)
    print("KAFKA STATUS CHECK")
    print("=" * 60)
    print()
    
    try:
        # Check consumer groups
        admin = KafkaAdminClient(bootstrap_servers=KAFKA_SERVER)
        
        print("Consumer Groups:")
        groups = admin.list_consumer_groups()
        for group in groups:
            print(f"  - {group[0]} (type: {group[1]})")
        
        print()
        
        # Check topic info
        consumer = KafkaConsumer(
            bootstrap_servers=KAFKA_SERVER,
            group_id='checker_temp'
        )
        
        partitions = consumer.partitions_for_topic(TOPIC_NAME)
        print(f"Topic: {TOPIC_NAME}")
        print(f"  Partitions: {len(partitions) if partitions else 0}")
        
        # Get latest offsets
        if partitions:
            topic_partitions = [('air_quality_stream', p) for p in partitions]
            end_offsets = consumer.end_offsets([('air_quality_stream', p) for p in partitions])
            print(f"  Total messages: {sum(end_offsets.values())}")
        
        consumer.close()
        admin.close()
        
        print()
        print("=" * 60)
        print("Check complete!")
        
    except Exception as e:
        print(f"ERROR: {e}")
        print("\nMake sure Kafka is running!")

if __name__ == "__main__":
    check_kafka_status()
