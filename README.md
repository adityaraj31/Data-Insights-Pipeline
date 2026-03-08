# Data Insights Pipeline

A complete end-to-end data processing pipeline and interactive dashboard.

This project automates the cleaning and analysis of raw CSV data (customers, orders, products) and serves the resulting business insights through a FastAPI backend to a modern React frontend dashboard.

## Architecture

- **Data Flow (`src/`)**: 
  - `clean_data.py`: Deduplicates customers, standardizes emails, parses multi-format dates, and dropping/imputing missing rows/values.
  - `analyze.py`: Merges cleaned datasets and derives key business metrics (Monthly Revenue, Top Customers, Category Performance, Regional Analysis, and Churn Indicators).
- **Backend (`backend/`)**: FastAPI server that natively triggers the data pipeline on startup via standard Python imports, reading the processed CSV files and securely exposing them as REST endpoints.
- **Frontend (`frontend/`)**: React application using Vite, Recharts, and Lucide Icons, providing a fully responsive and interactive data dashboard.

## Prerequisites

- [Python 3.11+](https://www.python.org/downloads/)
- [Node.js 20.19+](https://nodejs.org/) (for the frontend)
- [uv](https://github.com/astral-sh/uv) (Python package manager, strongly recommended)

## Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/adityaraj31/Data-Insights-Pipeline.git
cd Data-Insights-Pipeline
```

### 2. Setup the Python Backend

Using `uv` (recommended):

```bash
uv venv
# Activate the virtual environment:
# On Windows: .venv\Scripts\activate
# On macOS/Linux: source .venv/bin/activate

# Install dependencies (automatically installs what's needed from uv.lock / pyproject.toml)
uv pip install -r backend/requirements.txt
```

### 3. Setup the React Frontend

Open a new terminal, navigate to the frontend folder, and install dependencies:

```bash
cd frontend
npm install
```

## Running the Application

This is designed to be an automated pipeline. When you start the backend server, it will **automatically** run `clean_data.py` and `analyze.py` to ensure the data is fresh before making the API available.

### 1. Start the Backend API

In the root directory of the project (with your Python environment active):

```bash
uv run uvicorn backend.main:app --reload --port 8000
```
*The data pipeline (cleaning + analysis) will immediately execute in your console, after which the server will open at `http://127.0.0.1:8000`.*

### 2. Start the Frontend Dashboard

In a new terminal window, navigate to the `frontend` folder and start the Vite dev server:

```bash
cd frontend
npm run dev
```
*Your interactive dashboard will now be live locally at `http://localhost:5173`.*

## Docker Support

We also support containerizing the backend using Docker! (Ensure Docker Desktop is running).

```bash
docker-compose up --build -d
```
This automatically bind-mounts the local `./data` folder into the container, allowing the FastAPI process to seamlessly process raw CSVs and serve them over port 8000.

## Project Structure

```
├── backend/
│   ├── main.py                # FastAPI app (runs data pipeline on startup)
│   ├── Dockerfile             # Container image configuration
│   └── requirements.txt       # Python dependencies
├── data/
│   ├── processed/             # Cleaned files and generated insights go here
│   └── raw/                   # Place your raw .csv files here
├── frontend/                  
│   ├── src/
│   │   ├── App.jsx            # React Dashboard with Recharts components
│   │   └── index.css          # Modern dark-theme styling
│   └── package.json           # Node dependencies
├── src/
│   ├── analyze.py             # Data merging & mathematical insight derivations
│   └── clean_data.py          # Data cleansing rules & Pandas logic
├── tests/
│   └── test_clean_data.py     # Pytest unit tests mocking CSV structures
└── run_pipeline.py            # (Optional) Standalone pipeline orchestrator script
```

## API Endpoints

Once the FastAPI backend is running, it exposes the following intuitive REST endpoints (accessible via `http://localhost:8000`):

- `GET /health` : Returns `{ "status": "ok" }` to verify server up-time.
- `GET /api/revenue` : Returns a JSON array of the monthly revenue over time.
- `GET /api/top-customers` : Returns the top 10 highest-spending customers, resolving details like total spend, region, and their respective Churn Risk status.
- `GET /api/categories` : Returns a categorical breakdown reflecting product-specific revenue, count, and average order volumes.
- `GET /api/regions` : Returns a regional breakdown showing discrete geographical distributions.

**Note**: Since Swagger UI is automatically baked into FastAPI, you can instantly test and explore all of these endpoints right in your browser by visiting **[`http://127.0.0.1:8000/docs`](http://127.0.0.1:8000/docs)** while the server is alive!
