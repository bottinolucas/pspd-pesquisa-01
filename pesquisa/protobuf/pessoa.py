import pessoa_pb2

# Exemplo de como é montado o objeto da mensagem
pessoa = pessoa_pb2.Pessoa()
pessoa.nome = "João"
pessoa.idade = 22

print("objeto da mensagem definido:")
print(pessoa)

# Serialização dos dados
dados_binarios = pessoa.SerializeToString()
print("Dados serializados:")
print(dados_binarios)

# Desserialização dos dados

# obs: na pratica, isso aqui seria feito em outro arquivo, 
# no momento em que recebesse os dados serializados
nova_pessoa = pessoa_pb2.Pessoa()

nova_pessoa.ParseFromString(dados_binarios)

print('\nDados após desserialização:')
print(nova_pessoa)