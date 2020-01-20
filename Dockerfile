FROM python:3.7-buster

RUN apt update && apt install -y git

WORKDIR /usr/src

RUN git clone https://github.com/fabian-hk/nassl.git

WORKDIR /usr/src/nassl

RUN git checkout tls_profiler

RUN pip install requests mypy flake8 pytest twine invoke requests black==19.3b0

RUN invoke build.all

RUN pip install .

WORKDIR /usr/src/yesses

COPY requirements.txt ./
RUN apt update && apt install -y nmap
RUN pip install requests && pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT [ "python", "/usr/src/yesses/run.py" ]