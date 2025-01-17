# SVG server

- This container hosts a simple Node JS API with one endpoint.
- This endpoint returns an SVG format of diagrams that are rendered in the frontend.
- The API can be accessed via `svg.ai4mde.localhost`
- The API can be run locally: `npm start`

## Endpoints
- `/svg?diagram_id={diagram_id}`
    - Returns the SVG format of a diagram with id `diagram_id`
- AI4MDE's Django backend can also be used: `/api/v1/diagram/{diagram_id}/svg`

## How it works
1. When a GET request is sent to the endpoint, a chromium browser instance is run using `Puppeteer`. This instance authenticates and navigates to the diagram editor page.
2. At this page, a message handler from the frontend is called that returns the content of the ReactFlow component in svg format.
3. This SVG format is returned as a string.

## Current bugs & TODO
- The server fails to authenticate when the chromium browser is launched, because the frontend container is not fully booted yet.
- For some reason, the first request that is sent to the server always results in an `Internal Server Error`
- The server uses multiple `setTimeout` calls in order for the chromium browser to work properly. This causes delays in the endpoint.