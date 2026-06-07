from concurrent import futures
import time

import grpc

import clima_pb2
import clima_pb2_grpc

class ClimaService(
    clima_pb2_grpc.ClimaServiceServicer
):

    def MonitorarTemperatura(self, request, context):

        temperaturas = [25, 26, 27, 26, 25]

        for temp in temperaturas:
            print( "Enviando Temperatura")

            yield clima_pb2.TemperaturaResponse(
                temperatura=temp
            )

            time.sleep(1)


def serve():
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


if __name__ == "__main__":
    serve()