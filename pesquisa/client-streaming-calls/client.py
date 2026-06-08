import grpc
import clima_pb2
import clima_pb2_grpc


def gerar_medicoes(cidade, temperaturas):
    for temp in temperaturas:
        print(f"Enviando temperatura: {temp}°C")
        yield clima_pb2.TemperaturaRequest(cidade=cidade, temperatura=temp)

with grpc.insecure_channel("localhost:50052") as channel:
    stub = clima_pb2_grpc.ClimaServiceStub(channel)
    temperaturas = [25, 26, 27, 26, 25]
    response = stub.MonitorarTemperatura(
        gerar_medicoes("Brasília", temperaturas)
    )

    print(
        f"Cidade: {response.cidade} | "
        f"Média: {response.media_temperatura:.2f}°C | "
        f"Total de medições: {response.total_medicoes}"
    )