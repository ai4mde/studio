<p align="center">
    <img
        src="https://avatars.githubusercontent.com/u/155311177"
        alt="AI4MDE studio"
        width="64"
    />
</p>

<h1 align="center">
  AI4MDE &middot; <b>Architecture</b>
</h1>

<br/>

For a tutorial on how to install AI4MDE, see: [setup.md](./setup.md)

## 1. Overview

AI4MDE is a web-based application designed for AI-enhanced Model-Driven Engineering. Users can design UML Class, Activity, and Use Case Diagrams either via the frontend editor or by chatting with a chatbot. The platform currently generates fully functional Django software prototypes from these diagrams. AI4MDE is seperated in the following five main components, which all run in a seperate Docker container:

- **Frontend**: A React-based interface for users to interact with the system.
- **API**: A Django Ninja API server that handles diagram mutations and metadata logic and that processes user requests.
- **Database**: A PostgreSQL database for storing the system's data.
- **Prototypes**: A container with simple Flask server that handles request for the generation of Django prototypes, and that stores and runs generated prototypes.
- **Chatbot**: A container that runs a Flowise chatbot.

The application uses Traefik to route incoming traffic to the appropriate Docker container. When the project is run, you can connect to the containers via the following URLs:
- **Frontend:** [ai4mde.localhost](ai4mde.localhost)
- **API:** [api.ai4mde.localhost](api.ai4mde.localhost)
- **Prototypes**:
    - **API:** [prototypes_api.ai4mde.localhost](prototypes_api.ai4mde.localhost)
    - **Running prototype:** [prototype.ai4mde.localhost](prototype.ai4mde.localhost)
- **Chatbot:** TODO


## 2. Components
### API

#### Endpoints
A Django Ninja API is implemented for management and mutations on models that are specified in Django. Documentation on the metadata model can be found in [metadata.md](./metadata.md). Documentation for all API endpoints can be found using Swagger UI: [api.ai4mde.localhost/api/v1/docs](api.ai4mde.localhost/api/v1/docs)

The Ninja API consists of the following routers:
- **Metadata:**
    - Endpoints related to management mutations (projects, systems & releases)
    - Endpoints related to metadata mutations (classifiers, relations, interfaces & smart defaulting)
- **Diagram:**
    - Endpoints related to diagram mutations (diagrams, nodes & edges)
- **Generator:**
    - Endpoints relates to prototype management & generation
- **Prose:**
    - Endpoints related to AI pipelines that build metadata from requirements
- **Auth:**
    - Endpoints related to user authentication

#### Pydantic
Pydantic is a library for data validation using Python type annotations. In this API, Pydantic ensures request and response data adheres to defined schemas, providing automatic validation and serialization. Schema definitions can be found for all routers, under the `/api/model/{router}/api/schemas` directory. Dependency management is done using Poetry, and dependencies are specified in `/api/pyproject.toml`

#### Endpoint example
The following endpoint can be found under `/api/model/metadata/api/views/projects.py`

```python
@projects.post("/", response=ReadProject)
def create_project(request, project: CreateProject):
    return Project.objects.create(
        name=project.name,
        description=project.description,
    )
```
- **Annotation:** `@projects.post("/", response=ReadProject)`
    - A HTTP POST requests made to the `"/"` endpoint of the `projects` API router.
    - `response=ReadProject` specifies the Pydantic schema used to serialize the response data. It ensures that the output adheres to the structure defined in the `ReadProject` schema.
- **Function definition:** `def create_project(request, project: CreateProject):`
    - `request` represents the incoming HTTP request. It's passed automatically by Ninja.
    - `project: CreateProject` is the body of the POST request, expected to match the `CreateProject` Pydantic schema. This is parsed and validated by Ninja.
- **Function body:**
    - The endpoint's logic is performed here. Ninja serializes the return value using the `ReadProject` schema to generate the response.

### Database
As a database, the official PostgreSQL Docker image is used (see: [https://hub.docker.com/_/postgres/](https://hub.docker.com/_/postgres/)). The database is exposed to `port 5432`, which the Django backend can connect to (see `DATABASES` at [/api/model/model/settings.py](../api/model/model/settings.py)):

```python

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": environ.get(
            "POSTGRES_HOST", "postgres"
        ),
        "PORT": environ.get("POSTGRES_PORT", "5432"),
        "NAME": environ.get("POSTGRES_DB", "ai4mdestudio"),
        "USER": environ.get("POSTGRES_USER", "ai4mdestudio"),
        "PASSWORD": environ.get("POSTGRES_PASSWORD", "ai4mdestudio"),
    }
}
```

### Frontend
A React frontend is implemented in which end users can directly and intuitively manage and edit UML diagrams, and generate and manage software prototypes. This frontend can be accessed via [ai4mde.localhost](ai4mde.localhost)

#### Tech stack
- `npm` for depedency management ([https://docs.npmjs.com/](https://docs.npmjs.com/))
- `vite` for a development server ([https://vite.dev/guide/](https://vite.dev/guide/]))
- `React` and `TypeScript` for development ([https://react.dev/learn](https://react.dev/learn))
- `Tailwind CSS` for styling ([https://tailwindcss.com/docs](https://tailwindcss.com/docs))
- `Axios` for API calls ([https://axios-http.com/docs/intro](https://axios-http.com/docs/intro))

#### Directory structure

- `public/`
    - public images such as logo's
- `src/routes/`
    - routes the user can navigate to, e.g. `src/routes/diagram/{diagram_id}` specifies what the user will see when navigated to `http://ai4mde.localhost/diagram/{diagram_id}`
    - the routes are split into the following 4 categories:
        - diagram
        - projects
        - systems
        - build (legacy)
- `src/lib/`
    - this directory specifies reusable components that can be used in routes

### Prototypes
Currently, Django software prototypes can be generated using the metadata of a system. For this generation, a small Flask API runs inside the `prototypes` Docker container. This API can invoke the generation architecture, which will generate output Django files.

#### Flask API
The Flask API can be found under `/prototypes/backend/api.py`. It has the following endpoints:
- `generate_prototype` invokes the generation architecture with a JSON string of the metadata that is to be used for generation.
- `remove_prototype` removes all files corresponding to a Django prototype.
- `run_prototype` runs a prototype in the Docker container. A running prototype can be accessed via [prototype.ai4mde.localhost](prototype.ai4mde.localhost)
- `stop_prototypes` stops the currently running prototypes.
- `status_prototype` returns whether a prototype is currently running.

#### Generation architecture
At the core of the generation architecture is a `generator.sh` shell script. This script is responsible for initiating the process of creating a new Django project within the Docker container. It performs the following key tasks:

##### 1. Project initialization:
- A new, empty Django project is created inside the container.

##### 2. Python script invocation:
- A series of Python scripts are called to populate the new Django project with generated output files.

##### 3. File generation using Jinja2:
- These Python generation scripts use the Jinja2 templating engine to generate output files.
- How it works:
    - Predefined Jinja2 templates serve as blueprints.
    - Metadata from the prototype is merged with these templates.
    - The combination of templates and metadata produces the necessary output files for the Django project.

#### Shell script
`generator.sh` is invoked when a new prototype is generated. It does the following:
##### 1. Create a new empty Django project
- This is done by running the `django startproject` command.
##### 2. Update the global settings of the project
- All hosts are allowed. This is done such that running prototypes can be reached by other Docker containers.
- The authentication model is specified.
##### 3. Create a `shared_models` Django app
- In this app, Django models are generated based on the UML Class Diagram metadata.
- `generate_models.py` is invoked to generate Django models.
- All Django models are specified in this `shared_models` app such that they can be reached easily by all other apps that will be generated.
##### 4. Create an `authentication` Django app
- This app is only generated if specified in the metadata.
- This app is responsible for handling user authentication in the prototype.
- `generate_authentication.py` is invoked to generate authentication logic.
- If no authentication is specified in the metadata, a basic home page is generated for the prototype.

##### 5. Create a Django app for each interface in the metadata
- This is done by running the `django startapp` command.
- `generate_application.py` is invoked to generate the app's Models, Views & Templates (MVT) files.

##### 6. The database is migrated
- Finally, the prototype's database is migrated with migrations corresponding to the new `shared_models` definitions.

Additionally, two other, smaller shell scripts are written for specific purposes:
- `remover.sh` is responsible for removing all files corresponding to a prototype.
- `copy_database.sh` is responsible for re-using the database from a previous prototype.

#### Python generation scripts
Django adheres a MVT-architecture (Model-View-Template). This means, that prototypes should have `models.py` and `views.py` files, and (multiple) HTML templates that are used for user interaction. Python scripts are written to generate such files. This is done in the following order:

##### 1. `generate_models.py` generates a shared models file

##### 2. `generate_application.py` parses the prototype's interface metadata into intermediary Python objects
- More information on these intermediary objects can be found in the metadata model documentation: [metadata.md](./metadata.md) 

##### 3. These intermediary objects are used in the following scripts:
- `view_generation.py`: responsible for generating a `views.py` file
- `url_generation.py`: responsible for generating a `urls.py` file
- `template_generation.py`: responsible for generating HTML templates

#### Jinja2 templates
The Jinja2 templates that are filled by the Python scripts can be found under `/prototypes/backend/generation/templates`. The following templates are written:
- `models.py.jinja2`: used for the specification of models in the `shared_models` app
- `views.py.jinja2`: used for the generation of `views.py`
- `urls.py.jinja2`: used for the generation of `urls.py`
- `home.html.jinja2`: used for the generation of a basic home page
- `base.html.jinja2`: used for the generation of reusable page components, such as a header and navigation
- `page.html.jinja2`: used for the generation of individual HTML templates
- Additional basic templates for authentication


### Chatbot
Work in progress..
