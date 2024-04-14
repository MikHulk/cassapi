FROM python:3.11

WORKDIR /usr/src/app

RUN mkdir /usr/local/cassapi

COPY ./requirements.txt .

RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY ./app ./app

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "80"]
