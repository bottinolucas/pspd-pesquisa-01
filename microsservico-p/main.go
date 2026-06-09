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
	addrB    := getEnv("SERVICE_B_ADDR", "microsservico-b:50052")
	addrARest := getEnv("SERVICE_A_REST_ADDR", "microsservico-a-rest:5001")
	addrBRest := getEnv("SERVICE_B_REST_ADDR", "microsservico-b:8081")
	httpPort := getEnv("HTTP_PORT", "8080")

	log.Printf("[P] conectando Serviço A gRPC (%s)...", addrA)
	connA := dialGRPC(addrA)
	defer connA.Close()

	log.Printf("[P] conectando Serviço B gRPC (%s)...", addrB)
	connB := dialGRPC(addrB)
	defer connB.Close()

	h := &H{
		catalogo: pb.NewCatalogoServiceClient(connA),
		busca:    pb.NewBuscaServiceClient(connB),
	}

	restH := &RestH{
		clientA: NewRestClient(addrARest),
		clientB: NewRestClient(addrBRest),
	}

	r := gin.Default()
	r.Use(cors())

	// gRPC Path
	apiV1 := r.Group("/api/v1")
	{
		apiV1.GET("/health",       func(c *gin.Context) { c.JSON(http.StatusOK, gin.H{"status": "ok", "protocol": "grpc"}) })
		apiV1.GET("/livros",       h.ListarLivros)
		apiV1.GET("/livros/:isbn", h.BuscarLivro)
		apiV1.POST("/livros",      h.AdicionarLivro)
		apiV1.GET("/busca",        h.Busca)
	}

	// REST Path
	apiV2 := r.Group("/api/v2")
	{
		apiV2.GET("/health",       func(c *gin.Context) { c.JSON(http.StatusOK, gin.H{"status": "ok", "protocol": "rest"}) })
		apiV2.GET("/livros",       restH.ListarLivros)
		apiV2.GET("/livros/:isbn", restH.BuscarLivro)
		apiV2.POST("/livros",      restH.AdicionarLivro)
		apiV2.GET("/busca",        restH.Busca)
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
