# ─── Build ──────────────────────────────────────────────────────────────────
FROM maven:3.9-eclipse-temurin-21 AS builder
WORKDIR /build

# Cache de dependencias
COPY microsservico-b/pom.xml ./pom.xml
RUN mvn -q -B dependency:go-offline

# Codigo + proto canonico (sobrescreve a copia local para garantir fonte unica)
COPY microsservico-b/src ./src
COPY proto/biblioteca.proto ./src/main/proto/biblioteca.proto

RUN mvn -B -DskipTests clean package

# ─── Runtime ────────────────────────────────────────────────────────────────
FROM eclipse-temurin:21-jre-jammy
WORKDIR /app

COPY --from=builder /build/target/quarkus-app/lib/      ./lib/
COPY --from=builder /build/target/quarkus-app/*.jar     ./
COPY --from=builder /build/target/quarkus-app/app/      ./app/
COPY --from=builder /build/target/quarkus-app/quarkus/  ./quarkus/

# Diretorio persistente para os offsets do Debezium
RUN mkdir -p /data
VOLUME /data

ENV GRPC_PORT=50052
EXPOSE 50052

CMD ["java", "-jar", "quarkus-run.jar"]
