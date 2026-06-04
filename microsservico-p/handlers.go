package main

import (
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	pb "biblioteca/service-p/proto"
)

type H struct {
	catalogo pb.CatalogoServiceClient
}

// GET /api/v1/livros?filtro=xxx
func (h *H) ListarLivros(c *gin.Context) {
	ctx, cancel := withTimeout(5 * time.Second)
	defer cancel()

	resp, err := h.catalogo.ListarLivros(ctx, &pb.ListarLivrosRequest{
		Filtro: c.DefaultQuery("filtro", ""),
	})
	if err != nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"erro": err.Error()})
		return
	}

	type Livro struct {
		ISBN   string `json:"isbn"`
		Titulo string `json:"titulo"`
		Autor  string `json:"autor"`
		Ano    int32  `json:"ano"`
	}

	livros := make([]Livro, 0, len(resp.Livros))
	for _, l := range resp.Livros {
		livros = append(livros, Livro{
			ISBN: l.Isbn, Titulo: l.Titulo,
			Autor: l.Autor, Ano: l.Ano,
		})
	}
	c.JSON(http.StatusOK, gin.H{"livros": livros})
}

// GET /api/v1/livros/:isbn
func (h *H) BuscarLivro(c *gin.Context) {
	ctx, cancel := withTimeout(5 * time.Second)
	defer cancel()

	resp, err := h.catalogo.BuscarLivro(ctx, &pb.BuscarLivroRequest{
		Isbn: c.Param("isbn"),
	})
	if err != nil || !resp.Sucesso {
		c.JSON(http.StatusNotFound, gin.H{"erro": "Livro não encontrado"})
		return
	}
	c.JSON(http.StatusOK, gin.H{
		"isbn":   resp.Livro.Isbn,
		"titulo": resp.Livro.Titulo,
		"autor":  resp.Livro.Autor,
		"ano":    resp.Livro.Ano,
	})
}

// POST /api/v1/livros
func (h *H) AdicionarLivro(c *gin.Context) {
	var body struct {
		ISBN   string `json:"isbn"   binding:"required"`
		Titulo string `json:"titulo" binding:"required"`
		Autor  string `json:"autor"  binding:"required"`
		Ano    int32  `json:"ano"    binding:"required"`
	}
	if err := c.ShouldBindJSON(&body); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"erro": err.Error()})
		return
	}

	ctx, cancel := withTimeout(5 * time.Second)
	defer cancel()

	resp, err := h.catalogo.AdicionarLivro(ctx, &pb.AdicionarLivroRequest{
		Isbn: body.ISBN, Titulo: body.Titulo,
		Autor: body.Autor, Ano: body.Ano,
	})
	if err != nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"erro": err.Error()})
		return
	}
	if !resp.Sucesso {
		c.JSON(http.StatusConflict, gin.H{"erro": resp.Mensagem})
		return
	}
	c.JSON(http.StatusCreated, gin.H{"mensagem": resp.Mensagem})
}
