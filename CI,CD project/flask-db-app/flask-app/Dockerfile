FROM python:3.11-slim
WORKDIR /app
COPY app.py .
RUN pip install flask mysql-connector-python
EXPOSE 5000
CMD ["python3", "app.py"]
