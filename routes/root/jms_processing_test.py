from config.database import collection, collection_weather, collection_searchTrack
import os
import xml.etree.ElementTree as ET
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pymongo import MongoClient
import time


LOG_DIR = r"C:\Users\ujasv\Downloads\jumpstart-latest\log"
PROCESSED_DIR = os.path.join(LOG_DIR, "processed")
ERROR_DIR = os.path.join(LOG_DIR, "errors")

# Ensure directories exist
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(ERROR_DIR, exist_ok=True)


def process_xml(file_path):
    """Parse XML file and extract relevant data"""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Extract data - modify this based on your XML structure
        data = {
            "timestamp": root.find("timestamp").text,
            "message_id": root.find("messageId").text,
            "content": root.find("content").text,
            "source": root.find("source").text
        }
        
        # Add processing metadata
        data["processed_time"] = time.time()
        data["original_file"] = os.path.basename(file_path)
        
        return data
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
        return None

class LogHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            file_path = event.src_path
            if file_path.endswith(".xml"):  # Add your file pattern if needed
                self.handle_file(file_path)

    def handle_file(self, file_path):
        try:
            # Wait briefly to ensure file write is complete
            time.sleep(0.1)
            
            # Process XML
            data = process_xml(file_path)
            
            if data:
                # Insert into MongoDB
                collection.insert_one(data)
                
                # Move to processed directory
                new_path = os.path.join(PROCESSED_DIR, os.path.basename(file_path))
                os.rename(file_path, new_path)
                
                # Optional: Delete instead of moving
                # os.remove(file_path)
        except Exception as e:
            print(f"Error handling file {file_path}: {str(e)}")
            error_path = os.path.join(ERROR_DIR, os.path.basename(file_path))
            os.rename(file_path, error_path)

def start_monitoring():
    event_handler = LogHandler()
    observer = Observer()
    observer.schedule(event_handler, LOG_DIR, recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    start_monitoring()