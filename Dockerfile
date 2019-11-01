FROM python:3.7
ENV PYTHONUNBUFFERED 1
RUN mkdir /app /tmp/tanf
WORKDIR /app
COPY requirements.txt /app/
RUN pip3 install -r requirements.txt
COPY . /app/
