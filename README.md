# SuperKart Sales Forecast - containerised deployment

A Flask API serving the tuned Random Forest sales-forecast pipeline, and a Streamlit app that calls it.
Both run as Docker containers inside a GitHub Codespace and talk to each other over a Docker network.

## Run it in a GitHub Codespace

1. On this repository's page: **Code > Codespaces > Create codespace on main**.
2. In the Codespace terminal:

```bash
docker network create superkart-network

cd backend
docker build -t superkart-backend .
docker run -d --name backend --network superkart-network -p 7860:7860 superkart-backend

cd ../frontend
docker build -t superkart-frontend .
docker run -d --name frontend --network superkart-network -p 8501:8501 superkart-frontend

docker ps          # both containers should show as Up
```

3. Open the **Ports** tab, right-click ports **7860** and **8501**, and set **Port Visibility > Public**.
4. Open the forwarded address of port **8501** to use the app; the address of port **7860** is the API.

## API

- `GET /` health check
- `POST /v1/predict` JSON body with the ten features, returns `{"Predicted_Product_Store_Sales_Total": value}`
- `POST /v1/predictbatch` CSV file in the multipart field `file`, returns `{"row index": value, ...}`

## Clean up

```bash
docker stop frontend backend && docker rm frontend backend && docker network rm superkart-network
```
