FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy dependency file and install required packages
COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

# Copy the entrypoint script into the container
COPY entrypoint.sh /app/entrypoint.sh

# Copy the entire project into the container
COPY . .

# Make the entrypoint script executable
RUN chmod +x /app/entrypoint.sh

RUN ls -l /app/entrypoint.sh

RUN chown root:root /app/entrypoint.sh

# Expose the port your Flask app uses
EXPOSE 5000

# Set PYTHONPATH so Python can locate app/
ENV PYTHONPATH=/app

# Accept FLASK_ENV as a build argument
ARG FLASK_ENV

# Set FLASK_ENV as an environment variable inside the container
ENV FLASK_ENV=${FLASK_ENV}

# Display FLASK_ENV value during build for debugging purposes
RUN echo "FLASK_ENV during build: $FLASK_ENV"


# Conditionally run entrypoint.sh only if ENV is not local
ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]

# Command to run the Flask app
CMD ["python", "run.py"]
