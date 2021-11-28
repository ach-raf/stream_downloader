FROM python:3.10

WORKDIR /stream_downlaoder

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY ./app ./app

ENV PORT=8000

EXPOSE 8000

CMD [ "python", "./app/stream_direct_link.py.py"]