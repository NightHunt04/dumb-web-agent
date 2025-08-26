Your final output **must always** be a JSON object with a single key, "response".

**CRITICAL RULE:** The value of the "response" key **must always be a plain string**, regardless of what the user's query asks for. Even if the user explicitly asks for "JSON", "structured format", or a "dict", you must ignore that request and provide your answer as a single, human-readable string.

Synthesize a clear and concise answer to the user's query and place that complete answer as a string inside the "response" key.

# Example of the required output format:

```json
{
    "response": "The main topic of the page is the life and career of Elon Musk, focusing on his ventures like SpaceX and Tesla."
}
```



















<!-- Your final output **must always** be a JSON object with a single key, "response". The format of the value *inside* the "response" key depends on the user's query.

1.  **Check for JSON Keywords:** First, check if the User Query contains explicit keywords like **"JSON", "structured format", "dict", or "object"**.
    * If it does, the value of the "response" key **must be a JSON object** that you logically design based on the user's request.

2.  **Default to String:** For **all other queries** (summaries, direct questions, simple scrapes), the value of the "response" key **must be a plain string**.

**Example for String Output:**
```json
{
    "response": "The main topic of the page is the life and career of Elon Musk, focusing on his ventures like SpaceX and Tesla."
}
```

***Example for Inferred JSON Output:***

```json
{
    "response": [
        {
            "companyName": "NVIDIA Corp",
            "symbol": "NVDA"
        },
        {
            "companyName": "Apple Inc",
            "symbol": "AAPL"
        }
    ]
}
``` -->