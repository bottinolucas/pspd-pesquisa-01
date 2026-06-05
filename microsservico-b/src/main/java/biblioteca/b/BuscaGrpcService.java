package biblioteca.b;

import java.util.Map;

import co.elastic.clients.elasticsearch.core.SearchResponse;
import co.elastic.clients.elasticsearch.core.search.Hit;
import co.elastic.clients.elasticsearch.core.search.TotalHits;

import biblioteca.grpc.BuscaRequest;
import biblioteca.grpc.BuscaResponse;
import biblioteca.grpc.BuscaService;
import biblioteca.grpc.LivroBusca;
import io.quarkus.grpc.GrpcService;
import io.smallrye.common.annotation.Blocking;
import io.smallrye.mutiny.Uni;
import jakarta.inject.Inject;
import org.jboss.logging.Logger;

/**
 * Implementacao gRPC do servico de busca consumido pelo gateway P.
 * Delega a busca ao Elasticsearch.
 */
@GrpcService
public class BuscaGrpcService implements BuscaService {

    private static final Logger LOG = Logger.getLogger(BuscaGrpcService.class);

    @Inject
    ElasticsearchIndexer indexer;

    @Override
    @Blocking
    public Uni<BuscaResponse> buscarLivros(BuscaRequest request) {
        return Uni.createFrom().item(() -> doSearch(request));
    }

    @SuppressWarnings("rawtypes")
    private BuscaResponse doSearch(BuscaRequest request) {
        LOG.infof("BuscarLivros query='%s' pagina=%d tamanho=%d",
                request.getQuery(), request.getPagina(), request.getTamanho());

        BuscaResponse.Builder resp = BuscaResponse.newBuilder();
        try {
            SearchResponse<Map> result =
                    indexer.search(request.getQuery(), request.getPagina(), request.getTamanho());

            TotalHits total = result.hits().total();
            resp.setTotal(total != null ? total.value() : result.hits().hits().size());

            for (Hit<Map> hit : result.hits().hits()) {
                Map src = hit.source();
                if (src == null) {
                    continue;
                }
                LivroBusca.Builder livro = LivroBusca.newBuilder()
                        .setIsbn(str(src.get("isbn")))
                        .setTitulo(str(src.get("titulo")))
                        .setAutor(str(src.get("autor")))
                        .setAno(toInt(src.get("ano")));
                if (hit.score() != null) {
                    livro.setScore(hit.score());
                }
                resp.addResultados(livro.build());
            }
        } catch (Exception e) {
            LOG.error("Erro ao buscar no Elasticsearch", e);
        }
        return resp.build();
    }

    private static String str(Object o) {
        return o == null ? "" : o.toString();
    }

    private static int toInt(Object o) {
        if (o instanceof Number n) {
            return n.intValue();
        }
        if (o == null) {
            return 0;
        }
        try {
            return Integer.parseInt(o.toString());
        } catch (NumberFormatException e) {
            return 0;
        }
    }
}
