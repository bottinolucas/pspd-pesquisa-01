package biblioteca.b;

import java.io.File;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import java.util.Properties;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import io.debezium.engine.ChangeEvent;
import io.debezium.engine.DebeziumEngine;
import io.debezium.engine.format.Json;
import io.quarkus.runtime.ShutdownEvent;
import io.quarkus.runtime.StartupEvent;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.enterprise.event.Observes;
import jakarta.inject.Inject;
import org.eclipse.microprofile.config.inject.ConfigProperty;
import org.jboss.logging.Logger;

@ApplicationScoped
public class CdcService {

    private static final Logger LOG = Logger.getLogger(CdcService.class);

    @Inject
    ElasticsearchIndexer indexer;

    private final ObjectMapper mapper = new ObjectMapper();

    @ConfigProperty(name = "cdc.database.hostname") String dbHost;
    @ConfigProperty(name = "cdc.database.port")     String dbPort;
    @ConfigProperty(name = "cdc.database.user")     String dbUser;
    @ConfigProperty(name = "cdc.database.password") String dbPassword;
    @ConfigProperty(name = "cdc.database.dbname")   String dbName;
    @ConfigProperty(name = "cdc.table.include")     String tableInclude;
    @ConfigProperty(name = "cdc.offset.file")       String offsetFile;

    private DebeziumEngine<ChangeEvent<String, String>> engine;
    private ExecutorService executor;

    void onStart(@Observes StartupEvent ev) {
        indexer.ensureIndex();

        engine = DebeziumEngine.create(Json.class)
                .using(buildProperties())
                .notifying(this::handleEvent)
                .build();

        executor = Executors.newSingleThreadExecutor();
        executor.execute(engine);
        LOG.info("Motor CDC Debezium iniciado (Postgres -> Elasticsearch)");
    }

    void onStop(@Observes ShutdownEvent ev) {
        try {
            if (engine != null) {
                engine.close();
            }
            if (executor != null) {
                executor.shutdown();
                executor.awaitTermination(10, TimeUnit.SECONDS);
            }
        } catch (IOException | InterruptedException e) {
            LOG.warn("Erro ao encerrar o motor CDC", e);
            Thread.currentThread().interrupt();
        }
    }

    private Properties buildProperties() {
        File offset = new File(offsetFile);
        File parent = offset.getParentFile();
        if (parent != null) {
            parent.mkdirs();
        }

        Properties p = new Properties();
        p.setProperty("name", "biblioteca-cdc");
        p.setProperty("connector.class", "io.debezium.connector.postgresql.PostgresConnector");

        p.setProperty("offset.storage", "org.apache.kafka.connect.storage.FileOffsetBackingStore");
        p.setProperty("offset.storage.file.filename", offset.getAbsolutePath());
        p.setProperty("offset.flush.interval.ms", "5000");

        p.setProperty("topic.prefix", "biblioteca");
        p.setProperty("database.hostname", dbHost);
        p.setProperty("database.port", dbPort);
        p.setProperty("database.user", dbUser);
        p.setProperty("database.password", dbPassword);
        p.setProperty("database.dbname", dbName);

        p.setProperty("plugin.name", "pgoutput");
        p.setProperty("slot.name", "biblioteca_slot");
        p.setProperty("publication.name", "biblioteca_pub");
        p.setProperty("publication.autocreate.mode", "filtered");
        p.setProperty("table.include.list", tableInclude);
        p.setProperty("snapshot.mode", "initial");

        p.setProperty("key.converter", "org.apache.kafka.connect.json.JsonConverter");
        p.setProperty("key.converter.schemas.enable", "false");
        p.setProperty("value.converter", "org.apache.kafka.connect.json.JsonConverter");
        p.setProperty("value.converter.schemas.enable", "false");

        p.setProperty("transforms", "unwrap");
        p.setProperty("transforms.unwrap.type", "io.debezium.transforms.ExtractNewRecordState");
        p.setProperty("transforms.unwrap.delete.tombstone.handling.mode", "rewrite");

        return p;
    }

    private void handleEvent(ChangeEvent<String, String> event) {
        try {
            String key = event.key();
            if (key == null) {
                return;
            }
            JsonNode keyNode = mapper.readTree(key);
            String isbn = keyNode.path("isbn").asText(null);
            if (isbn == null || isbn.isEmpty()) {
                return;
            }

            String value = event.value();
            if (value == null) {
                indexer.delete(isbn);
                return;
            }

            JsonNode v = mapper.readTree(value);
            boolean deleted = "true".equalsIgnoreCase(v.path("__deleted").asText("false"));
            if (deleted) {
                indexer.delete(isbn);
                LOG.infof("CDC: livro removido %s", isbn);
            } else {
                Map<String, Object> doc = new HashMap<>();
                doc.put("isbn", v.path("isbn").asText());
                doc.put("titulo", v.path("titulo").asText());
                doc.put("autor", v.path("autor").asText());
                doc.put("ano", v.path("ano").asInt());
                indexer.index(isbn, doc);
                LOG.infof("CDC: livro indexado %s", isbn);
            }
        } catch (Exception e) {
            LOG.errorf(e, "Erro ao processar evento CDC: %s", event);
        }
    }
}
