# Hotel Reviews bot

Testing creating a local Ollama bot to help summarize reviews for hotel/airbnb listings

## Setup

- Ensure you have docker installed.
- Run `bash run.sh`
    - This will build main app container and the ollama container
    - Exec into the app container: `docker exec -it scraper bash`
    - Run `python main.py`

### TODOS:

 Lots to update:
 - Convert entrypoint to fastapi endpoint
    - This will ensure we can pass in listing url
- Add tests
- Fetch model names from env file
- Use sqlite or some other db to store the embeddings
- For much later, host this on the cloud
