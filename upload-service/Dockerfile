FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

RUN mkdir -p /app/uploaded_files/stl /app/uploaded_files/streamlines

EXPOSE 8080

CMD ["python", "app.py"]
