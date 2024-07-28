[![Build](https://github.com/Renovus-Tech/solarec-python/actions/workflows/python-build.yml/badge.svg?branch=main)](https://github.com/Renovus-Tech/solarec-python/actions/workflows/python-build.yml)
[![Tests](https://github.com/Renovus-Tech/solarec-python/actions/workflows/python-tests.yml/badge.svg?branch=main)](https://github.com/Renovus-Tech/solarec-python/actions/workflows/python-tests.yml)
[![Coverage](https://github.com/Renovus-Tech/solarec-python/blob/coverage-badge/coverage.svg)](https://github.com/Renovus-Tech/solarec-python/actions/workflows/python-app.yml)
[![CLA assistant](https://cla-assistant.io/readme/badge/Renovus-Tech/solarec-python)](https://cla-assistant.io/Renovus-Tech/solarec-python)

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

### LLM Client Integration for Automated Onboarding Extraction
For guidance on integrating various Language Model (LLM) clients and configuring automated onboarding data extraction, refer to the LLM Client Integration [Guide](https://github.com/Renovus-Tech/solarec-python/blob/main/app/nlp/readme.md). This guide covers the setup and usage of different LLM APIs to streamline the extraction of onboarding information from unstructured text.
