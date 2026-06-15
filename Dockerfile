FROM python:3.12-slim
WORKDIR /opt/mywebapp
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
EXPOSE 5200
