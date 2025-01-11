# SVG server

- This container hosts a simple Node JS API with one endpoint.
- This endpoint returns an SVG format of diagrams that are rendered in the frontend.
- The API can be accessed via `localhost:3000`
- The API can be run locally: `npm start`

## Endpoints
- `/svg?=diagram_id={diagram_id}`
    - Returns the SVG format of a diagram with id `diagram_id`

## How it works
1. When the container is run, a chromium browser instance is launched using `Puppeteer`, which navigates to the frontend and authenticates.
2. When a GET request is sent to the endpoint, the chromium instance navigates to the diagram editor page.
3. At this page, a message handler from the frontend is called that returns the content of the ReactFlow component in svg format.
4. This SVG format is returned as a string.

## Current bugs & TODO
- Currently, this container is set on the host machine's network: `network_mode: host`
    - This has security concerns.
    - Due to this, the user can only use the API through `localhost:3000` instead of using a subdomain like `svg.ai4mde.localhost` when Traefik is used.
    - It was chosen to do this because of communication issues between the React frontend and Django backend when this SVG container is connected to Traefik. If the SVG container is conntected to the Traefik network, the frontend cannot send HTTP requests to the backend when the chromium instance perfoms actions on pages.
    - Preferable, the SVG container is added to the Traefik network when these communication issues are resolved.
- The server fails to authenticate when the chromium browser is launched, because the frontend container is not fully booted yet.
- For some reason, the first request that is sent to the server always results in an `Internal Server Error`
- The server uses multiple `setTimeout` calls in order for the chromium browser to work properly. This causes delays in the endpoint.