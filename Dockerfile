ARG BASE_IMAGE=python:3.13

# Use an official Python runtime as a parent image
FROM ${BASE_IMAGE}

# Create a non-root user and group
RUN groupadd --system appgroup && \
    useradd --system --gid appgroup --create-home --home-dir /home/appuser appuser

# Set the working directory in the container
WORKDIR /home/appuser/certicopter

# Create required directories and set permissions
RUN mkdir -p /home/appuser/certicopter/files/logs && \
    mkdir -p /home/appuser/certicopter/files/certificates && \
    chown -R appuser:appgroup /home/appuser/certicopter

# Copy the SSL_Certificate_App directory contents into the container at /home/appuser/certicopter
COPY ./SSL_Certificate_App /home/appuser/certicopter

# Install any needed dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Change ownership to non-root user
RUN chown -R appuser:appgroup /home/appuser

# Drop privileges to non-root user
USER appuser

# Run app_starter.py when the container launches
CMD ["python", "app_starter.py"]
