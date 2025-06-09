import requests
import mysql.connector
from mysql.connector import Error
import schedule
import time
import logging

# Configure logging
logging.basicConfig(
    filename="pipeline.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Qwert54321@',
    'database': 'assessmentdb',
    'port': 3306
}

BASE_API_URL = "https://www.federalregister.gov/api/v1/documents.json?per_page=100&order=newest"

def create_table():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS federal_documents (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title TEXT,
                doc_type VARCHAR(255),
                abstract TEXT,
                pdf_url TEXT,
                publication_date DATE,
                excerpts TEXT,
                agency_raw_name VARCHAR(255),
                agency_name VARCHAR(255)
            );
        """)
        conn.commit()
        cursor.close()
        conn.close()
        logging.info("[STEP] Table created successfully.")
    except Error as e:
        logging.error(f"[ERROR] Error creating table: {e}")

def fetch_all_pages():
    logging.info("[STEP] Fetching data from all pages...")
    results = []
    page_url = BASE_API_URL
    page_count = 0

    while page_url:
        try:
            response = requests.get(page_url)
            data = response.json()

            for item in data.get('results', []):
                title = item.get('title')
                doc_type = item.get('type')
                abstract = item.get('abstract')
                pdf_url = item.get('pdf_url')
                publication_date = item.get('publication_date')
                excerpts = item.get('excerpts')

                agencies = item.get('agencies', [])
                agency_raw_name = agencies[0].get('raw_name') if agencies else None
                agency_name = agencies[0].get('name') if agencies else None

                results.append((
                    title,
                    doc_type,
                    abstract,
                    pdf_url,
                    publication_date,
                    excerpts,
                    agency_raw_name,
                    agency_name
                ))

            page_count += 1
            logging.info(f"[INFO] Fetched page {page_count}, total records so far: {len(results)}")

            page_url = data.get('next_page_url')  # Move to next page if available

            if not page_url:
                logging.info("[STEP] Reached last page.")
        except Exception as e:
            logging.error(f"[ERROR] Failed to fetch or parse page: {e}")
            break

    return results

def insert_into_db(records):
    if not records:
        logging.info("[INFO] No records to insert.")
        return

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        insert_query = """
            INSERT INTO federal_documents (
                title, doc_type, abstract, pdf_url, publication_date, excerpts,
                agency_raw_name, agency_name
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """

        cursor.executemany(insert_query, records)
        conn.commit()

        logging.info(f"[STEP] Inserted {cursor.rowcount} records into the database.")
        cursor.close()
        conn.close()
    except Error as e:
        logging.error(f"[ERROR] Database insertion failed: {e}")

def run_pipeline():
    logging.info("[STEP] Starting Data Pipeline with Pagination...")
    create_table()
    records = fetch_all_pages()
    insert_into_db(records)
    logging.info("[SUCCESS] Data pipeline completed successfully.")

def schedule_pipeline():
    schedule.every().day.at("17:20").do(run_pipeline)  # Run every day at 1 AM

    logging.info("[INFO] Scheduler started. Waiting for scheduled time...")
    while True:
        schedule.run_pending()
        time.sleep(60)  # check every minute

if __name__ == "__main__":
    schedule_pipeline()
