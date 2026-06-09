package main

import (
	"fmt"
	"net/http"
	"net/url"

	"github.com/gin-gonic/gin"
)

type RestH struct {
	clientA *RestClient
	clientB *RestClient
}

// GET /api/v2/livros?filtro=xxx
func (h *RestH) ListarLivros(c *gin.Context) {
	filtro := c.DefaultQuery("filtro", "")
	path := "/api/livros"
	if filtro != "" {
		path += "?filtro=" + url.QueryEscape(filtro)
	}

	var resp struct {
		Livros []struct {
			ISBN   string `json:"isbn"`
			Titulo string `json:"titulo"`
			Autor  string `json:"autor"`
			Ano    int32  `json:"ano"`
		} `json:"livros"`
	}

	if err := h.clientA.get(path, &resp); err != nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"erro": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"livros": resp.Livros})
}

// GET /api/v2/livros/:isbn
func (h *RestH) BuscarLivro(c *gin.Context) {
	isbn := c.Param("isbn")
	path := "/api/livros/" + url.PathEscape(isbn)

	var resp struct {
		Sucesso  bool   `json:"sucesso"`
		Mensagem string `json:"mensagem"`
		Livro    struct {
			ISBN   string `json:"isbn"`
			Titulo string `json:"titulo"`
			Autor  string `json:"autor"`
			Ano    int32  `json:"ano"`
		} `json:"livro"`
	}

	if err := h.clientA.get(path, &resp); err != nil {
		c.JSON(http.StatusNotFound, gin.H{"erro": "Livro não encontrado"})
		return
	}

	if !resp.Sucesso {
		c.JSON(http.StatusNotFound, gin.H{"erro": "Livro não encontrado"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"isbn":   resp.Livro.ISBN,
		"titulo": resp.Livro.Titulo,
		"autor":  resp.Livro.Autor,
		"ano":    resp.Livro.Ano,
	})
}

// GET /api/v2/busca?q=xxx&pagina=0&tamanho=10
func (h *RestH) Busca(c *gin.Context) {
	q := c.Query("q")
	pagina := c.DefaultQuery("pagina", "0")
	tamanho := c.DefaultQuery("tamanho", "10")

	path := fmt.Sprintf("/api/busca?q=%s&pagina=%s&tamanho=%s",
		url.QueryEscape(q), url.QueryEscape(pagina), url.QueryEscape(tamanho))

	var resp struct {
		Total      int64 `json:"total"`
		Resultados []struct {
			ISBN   string  `json:"isbn"`
			Titulo string  `json:"titulo"`
			Autor  string  `json:"autor"`
			Ano    int32   `json:"ano"`
			Score  float64 `json:"score"`
		} `json:"resultados"`
	}

	if err := h.clientB.get(path, &resp); err != nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"erro": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"total": resp.Total, "resultados": resp.Resultados})
}

// POST /api/v2/livros
func (h *RestH) AdicionarLivro(c *gin.Context) {
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

	path := "/api/livros"

	var resp struct {
		Sucesso  bool   `json:"sucesso"`
		Mensagem string `json:"mensagem"`
	}

	if err := h.clientA.post(path, body, &resp); err != nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"erro": err.Error()})
		return
	}
	
	if !resp.Sucesso {
		c.JSON(http.StatusConflict, gin.H{"erro": resp.Mensagem})
		return
	}
	
	c.JSON(http.StatusCreated, gin.H{"mensagem": resp.Mensagem})
}
