import time

import grpc

import chat_pb2
import chat_pb2_grpc


def gerar_mensagens():
    mensagens = [
        "Oi, servidor!",
        "Como funciona o streaming bidirecional?",
        "Cliente e servidor enviam mensagens ao mesmo tempo.",
        "Fim da conversa.",
    ]

    for texto in mensagens:
        print(f"Cliente enviando: {texto}")
        yield chat_pb2.ChatMessage(
            usuario="Cliente",
            texto=texto,
            timestamp=int(time.time()),
        )
        time.sleep(1)


with grpc.insecure_channel("localhost:50053") as channel:
    stub = chat_pb2_grpc.ChatServiceStub(channel)
    respostas = stub.Chat(gerar_mensagens())

    for resposta in respostas:
        print(f"{resposta.usuario}: {resposta.texto}")
