#############################
# First Stage
FROM python:3.11-alpine AS builder

### Set up and activate virtual environment
ENV VIRTUAL_ENV="/venv"
RUN python3 -m venv $VIRTUAL_ENV && ${VIRTUAL_ENV}/bin/pip install -U pip
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY requirements.txt .

# install dependencies
RUN ${VIRTUAL_ENV}/bin/pip install -r requirements.txt --no-cache-dir

#############################
# Second Stage
FROM python:3.11-alpine

ENV VIRTUAL_ENV="/venv"
RUN mkdir /app

### Copy only the dependencies installation from the 1st stage image
COPY --from=builder $VIRTUAL_ENV $VIRTUAL_ENV
COPY ./src /app


# update PATH environment variable
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV PYTHONPATH="${VIRTUAL_ENV}/lib/python3.11/site-packages/"

EXPOSE 502/tcp

WORKDIR /app
ENTRYPOINT ["/venv/bin/python3", "-m", "gateway"]