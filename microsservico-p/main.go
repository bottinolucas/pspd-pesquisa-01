package main

import (
	"log"
	"net/http"
	"os"
	"time"

	"github.com/gin-gonic/gin"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"

	pb "biblioteca/service-p/proto"
)

func getEnv(k, d string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return d
}

func dialGRPC(addr string) *grpc.ClientConn {
	ctx, cancel := withTimeout(15 * time.Second)
	defer cancel()
	conn, err := grpc.DialContext(ctx, addr,
		grpc.WithTransportCredentials(insecure.NewCredentials()),
		grpc.WithBlock(),
	)
	if err != nil {
		log.Fatalf("[P] falha ao conectar em %s: %v", addr, err)
	}
	return conn
}

func main() {
	addrA    := getEnv("SERVICE_A_ADDR", "microsservico-a:50051")
	httpPort := getEnv("HTTP_PORT", "8080")

	log.Printf("[P] conectando Serviço A (%s)...", addrA)
	connA := dialGRPC(addrA)
	defer connA.Close()

	h := &H{catalogo: pb.NewCatalogoServiceClient(connA)}

	r := gin.Default()
	r.Use(cors())

	api := r.Group("/api/v1")
	{
		api.GET("/health",       func(c *gin.Context) { c.JSON(http.StatusOK, gin.H{"status": "ok"}) })
		api.GET("/livros",       h.ListarLivros)
		api.GET("/livros/:isbn", h.BuscarLivro)
		api.POST("/livros",      h.AdicionarLivro)
	}

	log.Printf("[P] HTTP escutando :%s", httpPort)
	r.Run(":" + httpPort)
}

func cors() gin.HandlerFunc {
	return func(c *gin.Context) {
		c.Header("Access-Control-Allow-Origin", "*")
		c.Header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
		c.Header("Access-Control-Allow-Headers", "Content-Type")
		if c.Request.Method == http.MethodOptions {
			c.AbortWithStatus(http.StatusNoContent)
			return
		}
		c.Next()
	}
}
