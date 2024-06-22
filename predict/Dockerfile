# Use an official Python runtime as a parent image
FROM python:3.9-slim
# slimden alpine a gec calismazsa

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Make port 4000 available to the world outside this container
EXPOSE 5000

# Run app.py when the container launches
ENTRYPOINT ["python3", "app.py"]
