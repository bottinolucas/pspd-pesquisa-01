from concurrent import futures
import time

import grpc

import chat_pb2
import chat_pb2_grpc


class ChatService(chat_pb2_grpc.ChatServiceServicer):
    def Chat(self, request_iterator, context):
        for mensagem in request_iterator:
            print(f"Cliente {mensagem.usuario}: {mensagem.texto}")
            resposta = chat_pb2.ChatMessage(
                usuario="Servidor",
                texto=f"Mensagem recebida: {mensagem.texto}",
                timestamp=int(time.time()),
            )
            yield resposta


server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
chat_pb2_grpc.add_ChatServiceServicer_to_server(ChatService(), server)
server.add_insecure_port("[::]:50053")
server.start()

print("Servidor de chat iniciado em localhost:50053")
server.wait_for_termination()
