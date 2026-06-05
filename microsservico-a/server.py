from concurrent import futures
import logging
import os
import grpc
import psycopg2
import psycopg2.pool
import biblioteca_pb2
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

_pool = None

def get_pool():
    global _pool
    if _pool is None:
        _pool = psycopg2.pool.ThreadedConnectionPool(2, 10, DB_URL)
    return _pool

def get_conn():
    return get_pool().getconn()

def put_conn(conn):
    get_pool().putconn(conn)

def row_to_livro(row) -> biblioteca_pb2.Livro:
    return biblioteca_pb2.Livro(
        isbn=row[0], titulo=row[1], autor=row[2], ano=row[3]
    )

class CatalogoServicer(biblioteca_pb2_grpc.CatalogoServiceServicer):

    def BuscarLivro(self, request, context):
        log.info("BuscarLivro isbn=%s", request.isbn)
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT isbn, titulo, autor, ano "
                    "FROM catalogo.livros WHERE isbn = %s",
                    (request.isbn,)
                )
                row = cur.fetchone()
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
        finally:
            put_conn(conn)

    def ListarLivros(self, request, context):
        log.info("ListarLivros filtro='%s'", request.filtro)
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                if request.filtro:
                    f = f"%{request.filtro.lower()}%"
                    cur.execute(
                        "SELECT isbn, titulo, autor, ano "
                        "FROM catalogo.livros "
                        "WHERE LOWER(titulo) LIKE %s OR LOWER(autor) LIKE %s "
                        "ORDER BY titulo",
                        (f, f)
                    )
                else:
                    cur.execute(
                        "SELECT isbn, titulo, autor, ano "
                        "FROM catalogo.livros ORDER BY titulo"
                    )
                rows = cur.fetchall()
            return biblioteca_pb2.ListaLivrosResponse(
                livros=[row_to_livro(r) for r in rows]
            )
        finally:
            put_conn(conn)

    def AdicionarLivro(self, request, context):
        log.info("AdicionarLivro isbn=%s titulo='%s'", request.isbn, request.titulo)
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT isbn FROM catalogo.livros WHERE isbn = %s",
                    (request.isbn,)
                )
                if cur.fetchone():
                    return biblioteca_pb2.LivroResponse(
                        sucesso=False,
                        mensagem=f"ISBN {request.isbn} já existe"
                    )
                cur.execute(
                    "INSERT INTO catalogo.livros (isbn, titulo, autor, ano) "
                    "VALUES (%s, %s, %s, %s)",
                    (request.isbn, request.titulo, request.autor, request.ano)
                )
            conn.commit()
            livro = biblioteca_pb2.Livro(
                isbn=request.isbn, titulo=request.titulo,
                autor=request.autor, ano=request.ano
            )
            return biblioteca_pb2.LivroResponse(
                sucesso=True, mensagem="Livro adicionado com sucesso", livro=livro
            )
        except Exception as e:
            conn.rollback()
            log.error("Erro ao adicionar: %s", e)
            return biblioteca_pb2.LivroResponse(sucesso=False, mensagem=str(e))
        finally:
            put_conn(conn)

    def AtualizarLivro(self, request, context):
        log.info("AtualizarLivro isbn=%s", request.isbn)
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE catalogo.livros SET titulo=%s, autor=%s, ano=%s "
                    "WHERE isbn=%s",
                    (request.titulo, request.autor, request.ano, request.isbn)
                )
                if cur.rowcount == 0:
                    return biblioteca_pb2.LivroResponse(
                        sucesso=False, mensagem="ISBN não encontrado"
                    )
            conn.commit()
            livro = biblioteca_pb2.Livro(
                isbn=request.isbn, titulo=request.titulo,
                autor=request.autor, ano=request.ano
            )
            return biblioteca_pb2.LivroResponse(
                sucesso=True, mensagem="Livro atualizado com sucesso", livro=livro
            )
        except Exception as e:
            conn.rollback()
            return biblioteca_pb2.LivroResponse(sucesso=False, mensagem=str(e))
        finally:
            put_conn(conn)

    def DeletarLivro(self, request, context):
        log.info("DeletarLivro isbn=%s", request.isbn)
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM catalogo.livros WHERE isbn=%s",
                    (request.isbn,)
                )
                if cur.rowcount == 0:
                    return biblioteca_pb2.DeletarLivroResponse(
                        sucesso=False, mensagem="ISBN não encontrado"
                    )
            conn.commit()
            return biblioteca_pb2.DeletarLivroResponse(
                sucesso=True, mensagem="Livro deletado com sucesso"
            )
        except Exception as e:
            conn.rollback()
            return biblioteca_pb2.DeletarLivroResponse(sucesso=False, mensagem=str(e))
        finally:
            put_conn(conn)


def serve():
    port = int(os.getenv("GRPC_PORT", 50051))
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    biblioteca_pb2_grpc.add_CatalogoServiceServicer_to_server(
        CatalogoServicer(), server
    )
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    log.info("Serviço A iniciado na porta %d", port)
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
