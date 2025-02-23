FROM python:3.10.10-slim-bullseye
ENV PYTHONUNBUFFERED=1
WORKDIR /code
COPY . /code/
RUN pip install -r requirements.txt
# CMD ["sleep", "infinity"]