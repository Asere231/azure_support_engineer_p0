import os
import psycopg2
import logging
import hashlib
import subprocess
from app.exceptions import DatabaseConnectionError, LogCreationError, UserRegistrationError, InvalidCredentialsError

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class ServicesDAO:
    """DAO layer abstraction managing operational payloads for system_logs."""

    def __init__(self):
        self.host = os.getenv("DB_HOST", "db")
        self.database = os.getenv("DB_NAME", "postgres")
        self.user = os.getenv("DB_USER", "postgres")
        self.password = os.getenv("DB_PASSWORD", "secret")
        self._ensure_table_exists()

    def _get_connection(self):
        try:
            return psycopg2.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password
            )
        except psycopg2.OperationalError as e:
            logging.error(f"Failed to establish live connection to database: {e}")
            raise DatabaseConnectionError("Database backend service is unreachable.")


    def _ensure_table_exists(self):
        """Initializes database schema structurally if missing."""
        connection = None
        cursor = None
        try:    
            connection = self._get_connection()
            cursor = connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS services(
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) UNIQUE NOT NULL,
                    url VARCHAR(255) NOT NULL,
                    status_code INTEGER
                );                
            """)

            connection.commit()
            logging.info("Schema integrity verified: services table exists.")
        except Exception as e:
            logging.error(f"Failed to bootstrap application table schema: {e}")
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

    def check_and_insert_service(self, name: str, url: str) -> dict:
        """Securely inserts services strings using parameterized inputs."""
        connection = None
        cursor = None
        try:
            status_code = self.get_status_page(url)
            connection = self._get_connection()
            cursor = connection.cursor()

            query = "INSERT INTO services (name, url, status_code) VALUES(%s, %s, %s);"
            cursor.execute(query, (name, url, status_code))
            connection.commit()
            logging.info(f"Successfully recorded service log entry for: {name}")
            return {
                "name": name, 
                "url": url, 
                "status_code": status_code
            }
        except DatabaseConnectionError:
            raise
        except Exception as e:
            logging.error(f"Failed to execute target insert statement: {e}")
            raise LogCreationError("Data layer constraint violation occurred.")
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

    def get_all_services(self) -> list:
        """Fetches and handles database record sets cleanly."""
        connection = None
        cursor = None
        try:
            connection = self._get_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT name, url, status_code FROM services ORDER BY id DESC;")
            records = cursor.fetchall()

            all_services = [{"name": row[0], "url": row[1], "status_code": row[2]} for row in records]
            return all_services
        except Exception as e:
            logging.error(f"Retrieval failure across data layers: {e}")
            return []
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

    def get_status_page(self, url: str) -> int:
        status = subprocess.run(["curl", "-I", url], capture_output=True, text=True)
        http_code_line = status.stdout.splitlines()[0]
        http_status_code = int(http_code_line.split()[1])
        return http_status_code


class UserDAO:
    """DAO Layer abstraction for managing authentication"""

    def __init__(self, service_dao):
        self.host = service_dao.host
        self.database = service_dao.database
        self.user = service_dao.user
        self.password = service_dao.password
        self._ensure_table_exist()

    def _get_connection(self):
        try:
            return psycopg2.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password
            )
        except psycopg2.OperationalError as e:
            logging.error(f"Failed to establish live connection to database: {e}")
            raise DatabaseConnectionError("Database backend service is unreachable.")

    def _ensure_table_exist(self):
        """Initializes database schema structurally if missing."""
        connection = None
        cursor = None
        try:
            connection = self._get_connection()
            cursor = connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS application_users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    hashed_password VARCHAR(64) NOT NULL
                );
            """)
            connection.commit()
            logging.info("Schema integrity verified: application_users table exists.")
        except Exception as err:
            logging.critical(f"Failed to bootstrap application table schema: {err}")
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()
    
    def create_user(self, username: str, password: str):
        connection = None
        cursor = None
        try:
            connection = self._get_connection()
            cursor = connection.cursor()
            hashed_password = self._hash_password(password)
            query = "INSERT INTO application_users (username, hashed_password) VALUES (%s, %s);"
            cursor.execute(query, (username, hashed_password))
            connection.commit()
        except psycopg2.IntegrityError:
            raise UserRegistrationError("Username is already registered inside the domain")
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

    def authenticate_user(self, username: str, password: str) -> bool:
        connection = None
        cursor = None
        try:
            connection = self._get_connection()
            cursor = connection.cursor()
            hashed_password = self._hash_password(password)

            cursor.execute("SELECT id FROM application_users WHERE username=%s AND hashed_password=%s", 
                           (username, hashed_password))
            
            user_record = cursor.fetchone()
            if not user_record:
                raise InvalidCredentialsError("Invalid username or password validation cred")
            return True
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

