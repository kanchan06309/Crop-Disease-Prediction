# Use Python 3.9 image
FROM python:3.9

# Set the working directory inside the container
WORKDIR /code

# Copy the requirements file first (for better caching)
COPY ./requirements.txt /code/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy the rest of your app's code
COPY . /code

# Create a writable directory for temporary file uploads (Fixes Permission Errors)
RUN mkdir -p /code/static/uploads && chmod 777 /code/static/uploads

# Command to run your app
CMD ["python", "main.py"]
