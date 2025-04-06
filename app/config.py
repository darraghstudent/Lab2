import boto3
import os
import json

def get_secret(secret_name, region_name="eu-west-1"):
    """Retrieve secret from AWS Secrets Manager."""
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    try:
        secret_value = client.get_secret_value(SecretId=secret_name)
        secret = json.loads(secret_value['SecretString'])
        return secret
    except Exception as e:
        raise RuntimeError(f"Error retrieving secret: {e}")

class Config:
    SECRET_KEY = "supersecretkey"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CREATE_DB = False
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True 


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True
    CREATE_DB = True

    DB_USER = "postgres"
    DB_PASSWORD = "postgres"
    DB_HOST = "localhost"
    DB_PORT = "5432"
    DB_NAME = "moviemaking_db"

    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    
    # Log Database URI for debugging (Optional)
    print(f"Connecting to database at {DB_HOST}:{DB_PORT}")
    
class DevelopmentConfig2(Config):
     """Development configuration (AWS database)."""
     DEBUG = True
     SQLALCHEMY_ECHO = True  # Log SQL queries
     CREATE_DB = True  # Automatically create tables in development

     # Environment variables for other configurations
     DB_USER = os.getenv('DB_USER', 'DB_Admin')
     DB_PASSWORD = os.getenv('DB_PASSWORD', '2ZnaqSZ:')
     DB_HOST = os.getenv('DB_HOST', 'mydbinstance.endpoint.amazonaws.com')
     DB_PORT = os.getenv('DB_PORT', '5432')
     DB_NAME = os.getenv('DB_NAME', 'moviemaking_dev')

     SQLALCHEMY_DATABASE_URI = (
         f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
     )

      # Mask the password in logs
     print(f"Connecting to database at {DB_HOST}:{DB_PORT} with user {DB_USER}")


class ProductionConfig(Config):
    """Development configuration (AWS database)."""
    DEBUG = True
    SQLALCHEMY_ECHO = True  # Log SQL queries
    CREATE_DB = True  # Automatically create tables in development

    # Environment variables for other configurations
    DB_USER = os.getenv('DB_USER', 'DB_Admin')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '2ZnaqSZ:')
    DB_HOST = os.getenv('DB_HOST', 'mydbinstance.endpoint.amazonaws.com')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'moviemaking_dev')

    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    # Mask the password in logs
    print(f"Connecting to database at {DB_HOST}:{DB_PORT} with user {DB_USER}")


class TestingConfig(Config):
    TESTING = True
    DEBUG = False
    CREATE_DB = True
    WTF_CSRF_ENABLED = False

    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


config = {
    "development": DevelopmentConfig,
    "development2": DevelopmentConfig2,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
# Dynamically load the configuration
flask_env = os.getenv("FLASK_ENV", "production")
selected_config = config.get(flask_env, {ProductionConfig})
print(f"Using configuration: {selected_config.__name__}")
