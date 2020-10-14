FROM balenalib/raspberry-pi-python:3.7.4

ENV DEBIAN_FRONTEND noninteractive

RUN mkdir /code

WORKDIR /code

RUN apt-get update && \
    apt-get install -y build-essential git make python3-dev python3-pillow && \
    rm -rf /var/lib/apt/lists/*

RUN cd /opt && \
    git clone https://github.com/hzeller/rpi-rgb-led-matrix.git && \
    cd rpi-rgb-led-matrix && \
    make build-python PYTHON=$(which python3) && \
    make install-python PYTHON=$(which python3)

COPY ./requirements.txt /code/requirements.txt

RUN pip3 install -r requirements.txt

COPY . /code/

ENTRYPOINT python3 ticker.py
