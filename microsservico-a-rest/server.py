import os
import logging
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import asyncpg

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [SERVICE-A-REST] %(levelname)s %(message)s"
)
log = logging.getLogger(__name__)

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://biblioteca:biblioteca@postgres:5432/biblioteca"
)

# Async connection pool
pool: asyncpg.Pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global pool
    log.info("Inicializando pool de conexões asyncpg...")
    pool = await asyncpg.create_pool(dsn=DB_URL, min_size=2, max_size=10)
    yield
    log.info("Fechando pool de conexões...")
    await pool.close()

app = FastAPI(title="Catálogo REST API", lifespan=lifespan)

# Modelos Pydantic
class Livro(BaseModel):
    isbn: str
    titulo: str
    autor: str
    ano: int

class LivroRequest(BaseModel):
    isbn: str
    titulo: str
    autor: str
    ano: int

class LivroResponse(BaseModel):
    sucesso: bool
    mensagem: str
    livro: Optional[Livro] = None

class ListaLivrosResponse(BaseModel):
    livros: List[Livro]

@app.get("/api/livros", response_model=ListaLivrosResponse)
async def listar_livros(filtro: Optional[str] = Query(None)):
    log.info(f"ListarLivros filtro='{filtro}'")
    async with pool.acquire() as conn:
        if filtro:
            f = f"%{filtro.lower()}%"
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
        
        livros = [Livro(isbn=r['isbn'], titulo=r['titulo'], autor=r['autor'], ano=r['ano']) for r in rows]
        return ListaLivrosResponse(livros=livros)

@app.get("/api/livros/{isbn}", response_model=LivroResponse)
async def buscar_livro(isbn: str):
    log.info(f"BuscarLivro isbn={isbn}")
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT isbn, titulo, autor, ano "
            "FROM catalogo.livros WHERE isbn = $1",
            isbn
        )
        if row:
            livro = Livro(isbn=row['isbn'], titulo=row['titulo'], autor=row['autor'], ano=row['ano'])
            return LivroResponse(sucesso=True, mensagem="Livro encontrado", livro=livro)
        
        raise HTTPException(status_code=404, detail="Livro não encontrado")

@app.post("/api/livros", response_model=LivroResponse, status_code=201)
async def adicionar_livro(request: LivroRequest):
    log.info(f"AdicionarLivro isbn={request.isbn} titulo='{request.titulo}'")
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT isbn FROM catalogo.livros WHERE isbn = $1",
            request.isbn
        )
        if row:
            # Em conformidade com a assinatura gRPC que retorna erro graciosamente
            # No REST vamos retornar 409 Conflict
            raise HTTPException(status_code=409, detail=f"ISBN {request.isbn} já existe")
        
        try:
            await conn.execute(
                "INSERT INTO catalogo.livros (isbn, titulo, autor, ano) "
                "VALUES ($1, $2, $3, $4)",
                request.isbn, request.titulo, request.autor, request.ano
            )
            livro = Livro(isbn=request.isbn, titulo=request.titulo, autor=request.autor, ano=request.ano)
            return LivroResponse(sucesso=True, mensagem="Livro adicionado com sucesso", livro=livro)
        except Exception as e:
            log.error(f"Erro ao adicionar: {e}")
            raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/livros/{isbn}", response_model=LivroResponse)
async def atualizar_livro(isbn: str, request: LivroRequest):
    log.info(f"AtualizarLivro isbn={isbn}")
    async with pool.acquire() as conn:
        try:
            res = await conn.execute(
                "UPDATE catalogo.livros SET titulo=$1, autor=$2, ano=$3 "
                "WHERE isbn=$4",
                request.titulo, request.autor, request.ano, isbn
            )
            # res é uma string do tipo "UPDATE 1" ou "UPDATE 0"
            if res == "UPDATE 0":
                raise HTTPException(status_code=404, detail="ISBN não encontrado")
            
            livro = Livro(isbn=isbn, titulo=request.titulo, autor=request.autor, ano=request.ano)
            return LivroResponse(sucesso=True, mensagem="Livro atualizado com sucesso", livro=livro)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/livros/{isbn}")
async def deletar_livro(isbn: str):
    log.info(f"DeletarLivro isbn={isbn}")
    async with pool.acquire() as conn:
        try:
            res = await conn.execute(
                "DELETE FROM catalogo.livros WHERE isbn=$1",
                isbn
            )
            if res == "DELETE 0":
                raise HTTPException(status_code=404, detail="ISBN não encontrado")
            
            return {"sucesso": True, "mensagem": "Livro deletado com sucesso"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("REST_PORT", 5001))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)
