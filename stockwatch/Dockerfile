# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Copy the requirements file
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt


# **Apply the fix to pandas_ta**
RUN sed -i 's/from numpy import NaN as npNaN/from numpy import nan as npNaN/' \
    $(pip show pandas_ta | awk '/Location/ {print $2}')/pandas_ta/momentum/squeeze_pro.py


# Copy the rest of the application code
COPY . /app/

# Expose port 8000 for the android
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["gunicorn", "stockwatch.wsgi:application", "--bind", "0.0.0.0:8000"]
