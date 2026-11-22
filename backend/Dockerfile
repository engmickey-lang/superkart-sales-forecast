# Minimal official Python 3.12 image (the version this model was trained with)
FROM python:3.12-slim

# Working directory inside the container
WORKDIR /app

# Copy the requirements first so the dependency layer is cached between rebuilds
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy the API code and the serialized model
COPY . .

# The API listens on port 7860
EXPOSE 7860

# Serve the Flask app with gunicorn: 2 worker processes bound to port 7860 on all interfaces
# app:superkart_api means "the superkart_api object inside app.py"
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:7860", "--timeout", "120", "app:superkart_api"]
