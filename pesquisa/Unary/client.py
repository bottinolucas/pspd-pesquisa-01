import grpc

import usuario_pb2
import usuario_pb2_grpc

with grpc.insecure_channel("localhost:50051") as channel:
    stub = usuario_pb2_grpc.UsuarioServiceStub(
            channel
    )

    try:
        response = stub.BuscarUsuario(
                usuario_pb2.UsuarioRequest(id=1),
                timeout=5
            )
        print(response.nome)
        print(response.idade)
    except grpc.RpcError as error:
        print(f"Erro gRPC: {error.code().name} - {error.details()}")


