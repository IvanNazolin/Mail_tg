FROM python:3.10.19-trixie
WORKDIR /app
COPY main.py /app/m2.py
COPY config.py /app/config.py
COPY requirements.txt /app/requirements.txt
RUN pip3 install -r requirements.txt
ENTRYPOINT [ "python3","m2.py"]