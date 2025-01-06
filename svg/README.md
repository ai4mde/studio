# SVG server

- This container hosts a simple Node JS API with one endpoint.
- This endpoint retrieves SVG formats of diagrams in the frontend.
- The API can be accessed via `svg.ai4mde.localhost`
- The API can be run locally: `npm start`

# Endpoints
- `/svg?=diagram_id={diagram_id}`
    - Returns the SVG format of a diagram with id `diagram_id`

# TODO
As of now, the endpoint only works when the Node server is run locally. When the server is run inside the docker container, there are networking problems when the API is trying to connect to the frontend container. The API manages to connect to the frontend when the frontend is running, but after authentication is done diagrams are not loaded into the browser. This is probably happening due to unresolved communication errors between the frontend and the backend when a browser instance is run inside Docker.