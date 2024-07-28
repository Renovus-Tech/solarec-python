# Automated Onboarding Data Extraction

The `OnboardingHelper` class is used to extract onboarding data from a given document using an `LLMClient`.

- `LLMClient` is an abstract class that defines the interface for interacting with a Language Model.
- `LLMClientFactory` is a factory class that creates an instance of an `LLMClient` based on the configuration.

## Configuration

The specific `LLMClient` to use is determined by the environment variable `LLM_CLIENT_NAME` (e.g., `"GeminiAI"`).

Each `LLMClient` requires different environment variables to be set. The required environment variables for each client are listed below.

---

**Note:** Ensure you set up the environment variables according to the client you choose to use.


### OpenAI

#### Obtaining an API Key

1. **Access the OpenAI Website**
   - First, create an account by visiting [OpenAI](https://www.openai.com). Click on "Sign Up" and follow the on-screen instructions to complete the registration process.

2. **Obtain an API Key**
   - After your account is approved, log in and navigate to the "API Keys" section.
   - Here, you will find your API key. Copy your key for use in your environment variables.

#### Available Models

- The complete list of models is available [here](https://beta.openai.com/docs/models).
- For automated onboarding data extraction tasks, models like `gpt-3.5-turbo-1106` are recommended.

#### Set Up Environment Variables

Set up the following environment variables in your development environment:

- `OPENAI_API_KEY`: Your API Key (e.g., `"sk-xxxxxx"`)
- `OPENAI_MODEL_NAME`: The model you want to use (e.g., `"text-davinci-003"`)
- `OPENAI_INITIAL_PROMPT`: The initial prompt for the model (e.g., `"Extract location, capacity, installation date from the following document. The output should be in JSON format, including only the fields: location, capacity, installation_date."`)

### Gemini

#### Obtaining an API Key

1. **Access the GeminiAI Website**
   - First, create an account by visiting [GeminiAI](https://www.gemini-ai.com). Click on "Sign Up" and follow the on-screen instructions to complete the registration process.

2. **Obtain an API Key**
   - After your account is approved, log in and navigate to the "API Keys" section.
   - Here, you will find your API key. Copy your key for use in your environment variables.

#### Available Models

- The complete list of models is available [here](https://ai.google.dev/gemini-api/docs/models/gemini).
- For automated onboarding data extraction tasks, models like `gemini-1.5-flash` are recommended.

#### Set Up Environment Variables

Set up the following environment variables in your development environment:

- `GEMINI_API_KEY`: Your API Key (e.g., `"KF5JQJ2JX0Z0YXKJZQ2J0"`)
- `GEMINI_MODEL_NAME`: The model you want to use (e.g., `"gemini3.1-8b"`)
- `GEMINI_INITIAL_PROMPT`: The initial prompt for the model (e.g., `"Extract location, capacity, installation date from the following document. The output should be in JSON format, including only the fields: location, capacity, installation_date."`)

### Llama API Guide

#### Obtaining an API Token

1. **Access the Llama Website**
   - First, create an account by visiting [Llama API](https://www.llama-api.com). Click on "Log In" and then "Sign up." Follow the on-screen instructions to complete the registration process.

2. **Obtain an API Token**
   - After your account is approved, log in and navigate to the "API Token" section.
   - Here, you will find your API token. Hover over the clipboard icon to copy your token.

#### Available Models

- The complete list of models is available [here](https://docs.llama-api.com/quickstart#available-models).
- For automated onboarding data extraction tasks, "instruct/chat" models are recommended, such as `llama3.1-8b`.

#### Set Up Environment Variables

Set up the following environment variables in your development environment:

- `GEMINI_API_KEY`: Your API Token (e.g., `"KF5JQJ2JX0Z0YXKJZQ2J0"`)
- `GEMINI_MODEL_NAME`: The model you want to use (e.g., `"llama3.1-8b"`)
- `GEMINI_INITIAL_PROMPT`: The initial prompt for the model (e.g., `"Extract location, capacity, installation date from the following document. The output should be in JSON format, including only the fields: location, capacity, installation_date."`)