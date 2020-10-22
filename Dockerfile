FROM ubuntu:19.10
WORKDIR /srv
COPY requirements.txt .
RUN apt-get update && apt-get install python3-pip -y
RUN python3 -m pip install -r requirements.txt
COPY xolon xolon/
COPY bin/ bin/
EXPOSE 4001
CMD ["/srv/bin/prod-container"]
