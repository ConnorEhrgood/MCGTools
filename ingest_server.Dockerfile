##### Builder Image #####
FROM python:alpine as builder

COPY ingest_server /map

WORKDIR /map

# Install git, clone the repo, install the requirements
RUN apk update && pip install --target=/map/dependencies -r requirements.txt

##### Production Image ###
FROM python:alpine

COPY --from=builder     /map /map

ENV PYTHONPATH="${PYTHONPATH}:/map/dependencies"

# Install Uvicorn on the production container (Needs to do stuff, might be able to remove some day)
RUN pip install --ignore-installed uvicorn==0.22.0

WORKDIR /map

CMD uvicorn web_ui:api --host 0.0.0.0
