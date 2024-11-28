FROM python:3.11

RUN python3 --version
RUN pip3 --version

WORKDIR /app
COPY ./app /app

RUN pip3 install --no-cache-dir -r requirements.txt
RUN apt-get install openssl

EXPOSE 8001

CMD ["gunicorn", "--bind", "0.0.0.0:8002", "app:app"]