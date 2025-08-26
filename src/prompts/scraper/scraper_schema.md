Your task is to extract data that STRICTLY ADHERES to the provided JSON schema. This is a mandatory requirement. Your entire response MUST be a single JSON object with a single key "response", where the value is the structured data matching the schema. If information is missing, use `null`.

**JSON Schema to place inside the "response" key:**
```json
[JSON_SCHEMA_HERE]
```

***Example of the final output structure:***
If the schema was for a product, your final output should look like this:

```json
{
  "response": [{
    "product_name": "Example Laptop",
    "price": 999.99,
    "in_stock": true
  }, ...]
}
```