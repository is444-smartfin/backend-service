FROM python:latest
WORKDIR /usr/src/deployment
COPY ./ ./
RUN pip install --no-cache-dir -r requirements.txt