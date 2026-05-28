FROM python:3.11-slim
WORKDIR /app
COPY demos/openapi/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY demos/openapi /app
EXPOSE 8080
ENV PYTHONUNBUFFERED=1
CMD ["python", "app.py"]
