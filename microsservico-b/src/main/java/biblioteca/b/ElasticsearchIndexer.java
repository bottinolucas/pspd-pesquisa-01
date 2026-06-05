package biblioteca.b;

import java.io.IOException;
import java.util.Map;

import co.elastic.clients.elasticsearch.ElasticsearchClient;
import co.elastic.clients.elasticsearch._types.query_dsl.Query;
import co.elastic.clients.elasticsearch.core.SearchResponse;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import org.eclipse.microprofile.config.inject.ConfigProperty;
import org.jboss.logging.Logger;

@ApplicationScoped
public class ElasticsearchIndexer {

    private static final Logger LOG = Logger.getLogger(ElasticsearchIndexer.class);

    @Inject
    ElasticsearchClient client;

    @ConfigProperty(name = "es.index")
    String index;

    public void ensureIndex() {
        final int maxTentativas = 30;
        for (int i = 1; i <= maxTentativas; i++) {
            try {
                boolean existe = client.indices().exists(e -> e.index(index)).value();
                if (!existe) {
                    client.indices().create(c -> c
                            .index(index)
                            .mappings(m -> m
                                    .properties("isbn", p -> p.keyword(k -> k))
                                    .properties("titulo", p -> p.text(t -> t.analyzer("standard")))
                                    .properties("autor", p -> p.text(t -> t.analyzer("standard")))
                                    .properties("ano", p -> p.integer(in -> in))));
                    LOG.infof("Indice '%s' criado no Elasticsearch", index);
                } else {
                    LOG.infof("Indice '%s' ja existe", index);
                }
                return;
            } catch (Exception e) {
                LOG.warnf("Elasticsearch indisponivel (tentativa %d/%d): %s", i, maxTentativas, e.getMessage());
                try {
                    Thread.sleep(2000);
                } catch (InterruptedException ie) {
                    Thread.currentThread().interrupt();
                    return;
                }
            }
        }
        throw new IllegalStateException("Nao foi possivel preparar o indice no Elasticsearch");
    }

    public void index(String isbn, Map<String, Object> doc) throws IOException {
        client.index(i -> i.index(index).id(isbn).document(doc));
        LOG.debugf("Indexado livro %s", isbn);
    }

    public void delete(String isbn) throws IOException {
        client.delete(d -> d.index(index).id(isbn));
        LOG.debugf("Removido livro %s", isbn);
    }

    @SuppressWarnings("rawtypes")
    public SearchResponse<Map> search(String termo, int pagina, int tamanho) throws IOException {
        int size = tamanho > 0 ? tamanho : 10;
        int from = Math.max(0, pagina) * size;

        Query query;
        if (termo == null || termo.isBlank()) {
            query = Query.of(q -> q.matchAll(m -> m));
        } else {
            query = Query.of(q -> q.multiMatch(mm -> mm
                    .query(termo)
                    .fields("titulo^3", "autor^2", "isbn")
                    .fuzziness("AUTO")));
        }

        return client.search(s -> s
                .index(index)
                .from(from)
                .size(size)
                .query(query), Map.class);
    }
}
