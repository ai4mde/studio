FROM python:3.8

ARG PROTOTYPE_NAME
ARG METADATA

ENV PROTOTYPE_NAME=${PROTOTYPE_NAME}
ENV METADATA=${METADATA}

WORKDIR /usr/src
RUN pip install django Jinja2
COPY . /usr/src
RUN bash ./generator.sh ${PROTOTYPE_NAME} ${METADATA}