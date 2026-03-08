from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import pandas as pd
import numpy as np
from pathlib import Path
import logging
import sys

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to sys.path so we can dynamically import src
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"

# Import pipeline dynamically
try:
    from src.clean_data import main as run_cleaning
    from src.analyze import perform_analysis as run_analysis
except ImportError as e:
    logger.error(f"Failed to import data pipeline scripts: {e}")
    run_cleaning = None
    run_analysis = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run data pipeline on startup
    logger.info("Starting up data pipeline...")
    if run_cleaning and run_analysis:
        try:
            logger.info("Running clean_data.py...")
            run_cleaning()
            logger.info("Running analyze.py...")
            run_analysis()
            logger.info("Data pipeline finished successfully! Starting server.")
        except Exception as e:
            logger.error(f"Error running data pipeline: {e}")
    yield

app = FastAPI(title="Data Insights API", lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths relative to the project structure

def read_processed_csv(filename: str):
    """Safely read a CSV file and convert it to a JSON-ready list of dictionaries."""
    file_path = PROCESSED_DATA_DIR / filename
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        raise HTTPException(
            status_code=404, 
            detail=f"Data file '{filename}' not found. Please run the analysis script first."
        )
    
    try:
        df = pd.read_csv(file_path)
        # Handle NaN values to make them JSON-serializable (replace with None/null)
        df = df.replace({np.nan: None})
        return df.to_dict(orient="records")
    except Exception as e:
        logger.error(f"Error reading {filename}: {e}")
        raise HTTPException(status_code=500, detail="Error processing data file internally.")

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/revenue")
def get_revenue():
    return read_processed_csv("monthly_revenue.csv")

@app.get("/api/top-customers")
def get_top_customers():
    return read_processed_csv("top_customers.csv")

@app.get("/api/categories")
def get_categories():
    return read_processed_csv("category_performance.csv")

@app.get("/api/regions")
def get_regions():
    return read_processed_csv("regional_analysis.csv")

if __name__ == "__main__":
    import uvicorn
    # Use standard host/port for local dev
    uvicorn.run(app, host="127.0.0.1", port=8000)
