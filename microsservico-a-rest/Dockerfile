FROM python:3.12-slim
WORKDIR /app

COPY microsservico-a-rest/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY microsservico-a-rest/server.py .

ENV REST_PORT=5001
EXPOSE 5001
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "5001"]
