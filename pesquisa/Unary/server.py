from concurrent import futures
import grpc

import usuario_pb2
import usuario_pb2_grpc


class UsuarioService(
    usuario_pb2_grpc.UsuarioServiceServicer
):

    def BuscarUsuario(self, request, context):
        print("Chamada Buscar Usuario")


        return usuario_pb2.UsuarioResponse(
            nome="João",
            idade=22
        )



server = grpc.server(
    futures.ThreadPoolExecutor(max_workers=10)
)

usuario_pb2_grpc.add_UsuarioServiceServicer_to_server(
        UsuarioService(),
        server
    )

server.add_insecure_port("[::]:50051")
server.start()

print("Servidor iniciado em localhost:50051")
    

try:
    server.wait_for_termination()
except KeyboardInterrupt:
    server.stop(grace=1)


