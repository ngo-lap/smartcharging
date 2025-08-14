from typing import Dict, List, Literal
import pandas as pd
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from core.api.routers import cpo

description = """
First API endpoints for day-ahead planning. 🚀

* **Author**: Van-Lap NGO
"""

app = FastAPI(
    title='SmartChargingAPI', description=description, version='0.1', docs_url='/docs', redoc_url='/redocs'
)
app.include_router(cpo.router, tags=["cpo"])


@app.get("/")
async def root() -> Dict[str, str]:
    return {"message": "Home of EV Charging Planners"}


if __name__ == '__main__':

    uvicorn.run(app, host="localhost", port=8000)
