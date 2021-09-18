FROM python:3.8.3-slim-buster AS base

RUN apt update && apt install libgeos-dev

# Dedicated Workdir for App
WORKDIR /pywalkgen

# Do not run as root
RUN useradd -m -r pywalkgen && \
    chown pywalkgen /pywalkgen

COPY requirements.txt /pywalkgen
# RUN pip3 install -r requirements.txt

FROM base AS src
COPY . /pywalkgen

# install pywalkgen here as a python package
RUN pip3 install .

# USER pywalkgen is commented to fix the bug related to permission
# USER pywalkgen

COPY scripts/docker-entrypoint.sh /entrypoint.sh

# Use the `pywalkgen` binary as Application
FROM src AS prod

# this is add to fix the bug related to permission
RUN chmod +x /entrypoint.sh

ENTRYPOINT [ "/entrypoint.sh" ]

CMD ["walk-generator", "-c", "config.yaml"]
