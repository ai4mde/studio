FROM python:3.8

ARG project_name default
ARG runtime_file ./tests/runtime.json

WORKDIR /usr/src
RUN pip install django Jinja2
COPY . /usr/src
COPY $runtime_file /usr/src/tests
RUN bash ./generator.sh $project_name

WORKDIR /usr/src/generated_projects/${project_name}
CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]
