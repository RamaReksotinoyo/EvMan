FROM python:3.10.10-slim-bullseye
ENV PYTHONUNBUFFERED=1
WORKDIR .
COPY requirements.txt /.
RUN pip install -r requirements.txt
# CMD ["sleep", "infinity"]