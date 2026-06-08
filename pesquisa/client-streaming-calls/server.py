from concurrent import futures

import grpc

import clima_pb2
import clima_pb2_grpc

class ClimaService(
    clima_pb2_grpc.ClimaServiceServicer
):

    def MonitorarTemperatura(self, request_iterator, context):
        cidade = ""
        soma = 0
        total = 0

        for request in request_iterator:
            cidade = request.cidade
            soma += request.temperatura
            total += 1
            print(f"Recebida temperatura {request.temperatura} de {request.cidade}")

        media = (soma / total) if total else 0.0

        return clima_pb2.TemperaturaResponse(
            cidade=cidade,
            media_temperatura=media,
            total_medicoes=total
        )



server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10)
    )

clima_pb2_grpc.add_ClimaServiceServicer_to_server(
        ClimaService(),
        server
    )

server.add_insecure_port("[::]:50052")
server.start()

print("Servidor de clima iniciado em localhost:50052")
server.wait_for_termination()


