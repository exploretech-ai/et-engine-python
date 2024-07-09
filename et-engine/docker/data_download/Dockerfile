# Use an official Python runtime as a parent image
FROM public.ecr.aws/amazonlinux/amazonlinux:2

RUN yum install -y python3 python3-pip
# RUN python3 -m pip install boto3 waitress

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
ADD . /app

# Install any needed packages specified in requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variable
# ENV NAME World

# Run app.py when the container launches
CMD ["python3", "app.py"]
