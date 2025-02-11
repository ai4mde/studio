## Create actor node
```json
curl -X POST "https://acc-api.ai4mde.org/api/v1/diagram/6fc4cc8f-1cec-443f-8b11-dd7b72e20776/node/" \
-H "accept: application/json" \
-H "Content-Type: application/json" \
-H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MzgwNTcxMjksIm5iZiI6MTczNzk3MDcyOSwiaXNzIjoidXJuOmFpNG1kZXN0dWRpbyIsImlhdCI6MTczNzk3MDcyOSwidWlkIjo0fQ.XYb8SHIaeErEy5KC7_eGGMgeOd_EzGdVJoxS5WwMTFw" \
-d '{
  "cls": {
    "namespace": "",
    "name": "Test Actor",
    "type": "actor",
    "role": "actor",
    "description": "Test actor description"
  }
}'
```

## Create usecase node
```json
curl -X POST "https://acc-api.ai4mde.org/api/v1/diagram/08910cf0-a4fb-4749-80d5-5ebdc31c6ee1/node/" \
-H "accept: application/json" \
-H "Content-Type: application/json" \
-H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MzgxNTMzNzgsIm5iZiI6MTczODA2Njk3OCwiaXNzIjoidXJuOmFpNG1kZXN0dWRpbyIsImlhdCI6MTczODA2Njk3OCwidWlkIjo0fQ.f0K0b9RbQtw6DG72UjwsjNQkQFmOkw5U1PKOkicRaP8" \
-d '{
  "cls": {
    "namespace": "",
    "name": "Test UC",
    "type": "usecase",
    "role": "control",
    "description": "Test UC description"
  }
}'
```


## Types of use cases
* actor
* usecase


# create edge
curl -X POST "https://acc-api.ai4mde.org/api/v1/diagram/6fc4cc8f-1cec-443f-8b11-dd7b72e20776/edge/" \
-H "accept: application/json" \
-H "Content-Type: application/json" \
-H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MzgwNTcxMjksIm5iZiI6MTczNzk3MDcyOSwiaXNzIjoidXJuOmFpNG1kZXN0dWRpbyIsImlhdCI6MTczNzk3MDcyOSwidWlkIjo0fQ.XYb8SHIaeErEy5KC7_eGGMgeOd_EzGdVJoxS5WwMTFw" \
-d '{
  "source": "d9066fd1-f5be-4939-83cd-5c559f2d39f6",
  "target": "8108eb3f-352c-4f6f-adf5-7960a3cdc679",
  "rel": {
    "type": "association",
    "label": ""
  }
}'

# Types of edges
# association - Used for connections between actors and use cases
# include - Used for include relationships between use cases
# extend - Used for extend relationships between use cases