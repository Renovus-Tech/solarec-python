
from endpoints.solar import solar_overview, solar_climate, solar_performance, solar_power_curve, solar_alerts, solar_emissions
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import uvicorn
from urllib.parse import unquote

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('root')
app = FastAPI()


@app.exception_handler(Exception)
async def unicorn_exception_handler(request: Request, exc: Exception):
    request_url = request.url.path
    params = unquote(request.url.query)
    logger.error("Endpoint: %s\nParams: %s\nError: %s",
                 request_url, params, exc, exc_info=True)
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

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5000)
