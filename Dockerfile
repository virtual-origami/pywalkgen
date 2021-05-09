FROM python:3.8.3-slim-buster AS base

# Dedicated Workdir for App
WORKDIR /pywalkgen

# Do not run as root
RUN useradd -m -r pywalkgen && \
    chown pywalkgen /pywalkgen

COPY requirements.txt /pywalkgen
RUN pip3 install -r requirements.txt

FROM base AS src
COPY . /pywalkgen
# install pywalkgen here as a python package
RUN pip3 install .

USER pywalkgen

COPY scripts/docker-entrypoint.sh /entrypoint.sh

# Use the `walk-generator` binary as Application
FROM src AS prod
ENTRYPOINT [ "/entrypoint.sh" ]
CMD ["walk-generator", "-c", "config.yaml"]
