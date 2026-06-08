import grpc
import clima_pb2
import clima_pb2_grpc

with grpc.insecure_channel("localhost:50052") as channel:
    stub = clima_pb2_grpc.ClimaServiceStub(channel)
    response_stream = stub.MonitorarTemperatura(
        clima_pb2.TemperaturaRequest(cidade="Brasília")
    )

    for response in response_stream:
        print(f"Temperatura: {response.temperatura}°C")