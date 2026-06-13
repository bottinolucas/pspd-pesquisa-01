import asyncio
import logging
import os

import grpc
from grpc import aio
# pyrefly: ignore [missing-import]
import asyncpg
# pyrefly: ignore [missing-import]
import biblioteca_pb2
# pyrefly: ignore [missing-import]
import biblioteca_pb2_grpc

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [SERVICE-A] %(levelname)s %(message)s"
)
log = logging.getLogger(__name__)

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://biblioteca:biblioteca@postgres:5432/biblioteca"
)

pool: asyncpg.Pool = None


def row_to_livro(row) -> biblioteca_pb2.Livro:
    return biblioteca_pb2.Livro(
        isbn=row['isbn'], titulo=row['titulo'], autor=row['autor'], ano=row['ano']
    )


class CatalogoServicer(biblioteca_pb2_grpc.CatalogoServiceServicer):

    async def BuscarLivro(self, request, context):
        log.info("BuscarLivro isbn=%s", request.isbn)
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT isbn, titulo, autor, ano "
                "FROM catalogo.livros WHERE isbn = $1",
                request.isbn
            )
            if row:
                return biblioteca_pb2.LivroResponse(
                    sucesso=True,
                    mensagem="Livro encontrado",
                    livro=row_to_livro(row)
                )
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"ISBN {request.isbn} não encontrado")
            return biblioteca_pb2.LivroResponse(
                sucesso=False, mensagem="Livro não encontrado"
            )

    async def ListarLivros(self, request, context):
        log.info("ListarLivros filtro='%s'", request.filtro)
        async with pool.acquire() as conn:
            if request.filtro:
                f = f"%{request.filtro.lower()}%"
                rows = await conn.fetch(
                    "SELECT isbn, titulo, autor, ano "
                    "FROM catalogo.livros "
                    "WHERE LOWER(titulo) LIKE $1 OR LOWER(autor) LIKE $2 "
                    "ORDER BY titulo",
                    f, f
                )
            else:
                rows = await conn.fetch(
                    "SELECT isbn, titulo, autor, ano "
                    "FROM catalogo.livros ORDER BY titulo"
                )
            return biblioteca_pb2.ListaLivrosResponse(
                livros=[row_to_livro(r) for r in rows]
            )

    async def AdicionarLivro(self, request, context):
        log.info("AdicionarLivro isbn=%s titulo='%s'", request.isbn, request.titulo)
        async with pool.acquire() as conn:
            existing = await conn.fetchrow(
                "SELECT isbn FROM catalogo.livros WHERE isbn = $1",
                request.isbn
            )
            if existing:
                return biblioteca_pb2.LivroResponse(
                    sucesso=False,
                    mensagem=f"ISBN {request.isbn} já existe"
                )
            try:
                await conn.execute(
                    "INSERT INTO catalogo.livros (isbn, titulo, autor, ano) "
                    "VALUES ($1, $2, $3, $4)",
                    request.isbn, request.titulo, request.autor, request.ano
                )
                livro = biblioteca_pb2.Livro(
                    isbn=request.isbn, titulo=request.titulo,
                    autor=request.autor, ano=request.ano
                )
                return biblioteca_pb2.LivroResponse(
                    sucesso=True, mensagem="Livro adicionado com sucesso", livro=livro
                )
            except Exception as e:
                log.error("Erro ao adicionar: %s", e)
                return biblioteca_pb2.LivroResponse(sucesso=False, mensagem=str(e))

    async def AtualizarLivro(self, request, context):
        log.info("AtualizarLivro isbn=%s", request.isbn)
        async with pool.acquire() as conn:
            try:
                res = await conn.execute(
                    "UPDATE catalogo.livros SET titulo=$1, autor=$2, ano=$3 "
                    "WHERE isbn=$4",
                    request.titulo, request.autor, request.ano, request.isbn
                )
                # res é uma string do tipo "UPDATE 1" ou "UPDATE 0"
                if res == "UPDATE 0":
                    return biblioteca_pb2.LivroResponse(
                        sucesso=False, mensagem="ISBN não encontrado"
                    )
                livro = biblioteca_pb2.Livro(
                    isbn=request.isbn, titulo=request.titulo,
                    autor=request.autor, ano=request.ano
                )
                return biblioteca_pb2.LivroResponse(
                    sucesso=True, mensagem="Livro atualizado com sucesso", livro=livro
                )
            except Exception as e:
                return biblioteca_pb2.LivroResponse(sucesso=False, mensagem=str(e))

    async def DeletarLivro(self, request, context):
        log.info("DeletarLivro isbn=%s", request.isbn)
        async with pool.acquire() as conn:
            try:
                res = await conn.execute(
                    "DELETE FROM catalogo.livros WHERE isbn=$1",
                    request.isbn
                )
                if res == "DELETE 0":
                    return biblioteca_pb2.DeletarLivroResponse(
                        sucesso=False, mensagem="ISBN não encontrado"
                    )
                return biblioteca_pb2.DeletarLivroResponse(
                    sucesso=True, mensagem="Livro deletado com sucesso"
                )
            except Exception as e:
                return biblioteca_pb2.DeletarLivroResponse(sucesso=False, mensagem=str(e))


async def serve():
    global pool
    log.info("Inicializando pool de conexões asyncpg...")
    pool = await asyncpg.create_pool(dsn=DB_URL, min_size=2, max_size=100)

    port = int(os.getenv("GRPC_PORT", 50051))
    server = aio.server()
    biblioteca_pb2_grpc.add_CatalogoServiceServicer_to_server(
        CatalogoServicer(), server
    )
    server.add_insecure_port(f"[::]:{port}")
    await server.start()
    log.info("Serviço A (async) iniciado na porta %d", port)
    await server.wait_for_termination()
    await pool.close()

if __name__ == "__main__":
    asyncio.run(serve())
