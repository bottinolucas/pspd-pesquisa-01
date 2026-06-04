FROM python:3.12-slim
WORKDIR /app

COPY microsservico-a/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY proto/biblioteca.proto .
RUN python -m grpc_tools.protoc \
    -I. \
    --python_out=. \
    --grpc_python_out=. \
    biblioteca.proto

COPY microsservico-a/server.py .

ENV GRPC_PORT=50051
EXPOSE 50051
CMD ["python", "server.py"]
