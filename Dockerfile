FROM python:3.10

WORKDIR /stream_downlaoder

COPY . .

RUN pip install -r requirements.txt

ENV PORT=8000

EXPOSE 8000

CMD [ "python", "app/stream_direct_link.py"]