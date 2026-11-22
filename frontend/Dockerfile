# Minimal official Python 3.12 image
FROM python:3.12-slim

# Working directory inside the container
WORKDIR /app

# Install the dependencies first so this layer is cached between rebuilds
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Streamlit app
COPY . .

# Streamlit listens on port 8501
EXPOSE 8501

# Launch the app on port 8501, reachable from outside the container.
# XSRF protection is disabled because the Codespaces port-forwarding proxy otherwise blocks file uploads.
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.enableXsrfProtection=false"]
