import logging
from urllib.parse import unquote

import uvicorn
from endpoints.solar import (solar_alerts, solar_anomaly_detection,
                             solar_certificates, solar_climate,
                             solar_data_availability, solar_emissions,
                             solar_overview, solar_performance,
                             solar_power_curve, solar_sales)
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('root')
app = FastAPI()


@app.exception_handler(Exception)
async def unicorn_exception_handler(request: Request, exc: Exception):
    request_url = request.url.path
    params = unquote(request.url.query)
    logger.error("Endpoint: %s\nParams: %s\nError: %s",
                 request_url, params, exc, exc_info=True)
    print(f"Endpoint: {request_url}\nParams: {params}\nError: {exc}")
    return JSONResponse(
        status_code=500,
        content=jsonable_encoder(
            {"endpoint": request_url, "params": params, "error": repr(exc)}),
    )


@app.get("/")
def read_root():
    msg = "Go to ./docs to read about what's on this API"
    return {"Hello!": msg}


@app.get("/info/")
def root():
    msg = []
    msg.append({"Overview": "General operation information"})
    return {"General information about graphs on this API": msg}


# Solar
app.include_router(solar_overview.router)
app.include_router(solar_climate.router)
app.include_router(solar_performance.router)
app.include_router(solar_power_curve.router)
app.include_router(solar_alerts.router)
app.include_router(solar_emissions.router)
app.include_router(solar_certificates.router)
app.include_router(solar_sales.router)
app.include_router(solar_anomaly_detection.router)
app.include_router(solar_data_availability.router)
# app.include_router(solar_onboard_location.router)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5000)
