[![Python application](https://github.com/Renovus-Tech/solarec-python/actions/workflows/python-app.yml/badge.svg?branch=main)](https://github.com/Renovus-Tech/solarec-python/actions/workflows/python-app.yml)
[![Python application](https://github.com/Renovus-Tech/solarec-python/blob/coverage-badge/coverage.svg)](https://github.com/Renovus-Tech/solarec-python/actions/workflows/python-app.yml)


# SolaREC
 
## Data API

### Setting up the Environment
To set up the environment for SolaREC's data API, follow these steps:

- Create a virtual environment: `python -m venv .venv`.
- Change the source to the virtual environment: `source .venv/bin/activate`.

#### Database Configuration

- Locate the `database.ini` file in the /app directory of the project.
- In the `database.ini` file, you'll find a section for PostgreSQL with the following parameters:

```ini
[postgresql]
host=
database=
user=
password=
```

#### Dependencies installation
- Install the required dependencies from `requirements.txt`:
```
pip install -r requirements.txt
```

### Running the API
To run the API, follow these steps:

- Navigate to the /app directory.
- Execute the following command: `uvicorn main:app --reload`.


### API Endpoints
After starting the API, visit `<url>/docs` to access the API documentation and explore its endpoints.
