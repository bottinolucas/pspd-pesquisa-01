package biblioteca.b;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import co.elastic.clients.elasticsearch.core.SearchResponse;
import co.elastic.clients.elasticsearch.core.search.Hit;
import co.elastic.clients.elasticsearch.core.search.TotalHits;

import jakarta.inject.Inject;
import jakarta.ws.rs.DefaultValue;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.QueryParam;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import org.jboss.logging.Logger;

@Path("/api/busca")
@Produces(MediaType.APPLICATION_JSON)
public class BuscaRestResource {

    private static final Logger LOG = Logger.getLogger(BuscaRestResource.class);

    @Inject
    ElasticsearchIndexer indexer;

    @GET
    public Response buscarLivros(
            @QueryParam("q") String query,
            @QueryParam("pagina") @DefaultValue("0") int pagina,
            @QueryParam("tamanho") @DefaultValue("10") int tamanho) {
        
        LOG.infof("REST BuscarLivros query='%s' pagina=%d tamanho=%d", query, pagina, tamanho);

        try {
            @SuppressWarnings("rawtypes")
            SearchResponse<Map> result = indexer.search(query, pagina, tamanho);
            
            TotalHits total = result.hits().total();
            long totalHits = total != null ? total.value() : result.hits().hits().size();

            List<Map<String, Object>> resultados = new ArrayList<>();
            for (Hit<Map> hit : result.hits().hits()) {
                Map src = hit.source();
                if (src == null) {
                    continue;
                }
                Map<String, Object> livro = new HashMap<>();
                livro.put("isbn", str(src.get("isbn")));
                livro.put("titulo", str(src.get("titulo")));
                livro.put("autor", str(src.get("autor")));
                livro.put("ano", toInt(src.get("ano")));
                if (hit.score() != null) {
                    livro.put("score", hit.score());
                }
                resultados.add(livro);
            }

            Map<String, Object> response = new HashMap<>();
            response.put("total", totalHits);
            response.put("resultados", resultados);

            return Response.ok(response).build();
        } catch (Exception e) {
            LOG.error("Erro ao buscar no Elasticsearch (REST)", e);
            return Response.serverError().entity(Map.of("erro", e.getMessage())).build();
        }
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
