FROM apache/airflow:2.8.0-python3.11

# Switch to root to install system dependencies
USER root

# Install any system dependencies if needed
RUN apt-get update && apt-get install -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Switch back to airflow user
USER airflow

# Copy requirements and install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy DAGs (optional - can also use git-sync or ConfigMap)
# COPY dags/ /opt/airflow/dags/

# Set proper permissions
USER root
RUN chown -R airflow:root /opt/airflow
USER airflow

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1