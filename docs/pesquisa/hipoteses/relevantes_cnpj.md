# Achados de CNPJ sem cobertura online

De [`achados_cnpj.md`](achados_cnpj.md) (7 combinações curadas do espaço de
trincas/quadras/quintuplas de papel de CNPJ), 6 sobrevivem aqui — busca
online (`WebSearch`, 2026-09-08) não achou equivalente publicado.

**N3 saiu** (doador de campanha × autuado pelo IBAMA): é achado já bem
coberto — Repórter Brasil, ClimaInfo, Desacato e InfoAmazonia já cruzam
exatamente essas duas bases (267 doadores com auto de infração do IBAMA,
R$ 6,6 milhões doados a 136 candidatos). Vale registrar que isso **valida**
o método deste pipeline: o par `doador_campanha × ibama_autuado` (lift 26,2)
apareceu no topo do ranking por conta própria, sem nenhuma pista externa —
o mesmo sinal que jornalismo investigativo dedicado já havia encontrado por
outro caminho.

| # | Achado | O que significa | Por que importa | Cobertura (por quê) |
|---|---|---|---|---|
| N1 | Fornecedor da Câmara + registro ambiental (IBAMA) + revenda de combustível + fornecedor do Senado — 5.397 empresas, 6 pares internos todos positivos (lift 4,7 a 56,7) | Um grupo de ~5.400 empresas vende combustível e fornece para as duas casas do Congresso ao mesmo tempo — provável mercado de abastecimento de frota legislativa | Primeira medida do tamanho desse cluster; nenhum dos 6 pares que o compõem é definicional | Não encontrado — cobertura de imprensa sobre cota parlamentar/combustível existe, mas não esse cruzamento de cadastro de fornecedor |
| N2 | Licitante federal + fornecedor do PNCP + contratado do TCE-RJ — 5.154 empresas (lift 6,1 / 11,5 / 14,5) | ~5.150 empresas disputam licitação federal, vendem via PNCP e têm contrato com prefeitura fluminense auditada pelo TCE-RJ | Estende o achado "maior lift da corrida" do h3 (fornecedor do Banco de Preços em Saúde × TCE-RJ) para um terceiro cadastro de compra pública | Não encontrado — PNCP é descrito como cadastro unificado em tese, mas a sobreposição real medida com licitante federal e TCE-RJ não aparece |
| N4 | Licitante federal + geração distribuída solar + fornecedor do PNCP — 8.554 empresas (lift 2,6 / 6,1 / 2,2, sinal moderado) | 8.554 empresas que disputam licitação federal e vendem ao governo via PNCP também têm sistema de geração solar próprio no CNPJ | Ponte com os achados de energia solar como marcador de classe (B4/h2 em `relevantes-bio.md`) — agora do lado da empresa fornecedora, não do domicílio | Não encontrado — cobertura de geração distribuída é sobre consumidor residencial/comercial, não sobre o perfil de fornecedor do governo |
| N5 | Cartão corporativo do governo + licitante federal + fornecedor do PNCP — 5.617 empresas (lift 7,1 / 2,7 / 6,1) | 5.617 empresas usam cartão corporativo governamental, disputam licitação federal e vendem via PNCP ao mesmo tempo | Perfil de "empresa que vive de contrato público" com três pontas de evidência administrativa independentes | Parcial — existe preocupação pública documentada sobre cartão corporativo driblar licitação (licitacao.net), mas não essa métrica de sobreposição de cadastro específica |
| N-ext1 | Penalidade do BC + BNDES não-automático + autuado IBAMA + outorga de lançamento de água + patrocinador Rouanet — 50 empresas | Um grupo de 50 empresas acumula multa do Banco Central, crédito BNDES não-automático, autuação ambiental, outorga de lançamento de efluente e patrocínio cultural na mesma raiz de CNPJ | Cinco chapéus regulatórios muito diferentes na mesma empresa — perfil de risco composto que nenhum cadastro isolado mostra | Não encontrado — nenhuma combinação desses cinco cadastros específicos aparece cruzada |
| N-ext2 | Penalidade do BC + BNDES não-automático + sócio-holding + outorga de lançamento de água + patrocinador Rouanet — 44 empresas | Variante do grupo acima trocando autuação IBAMA por estrutura societária em holding | Mesmo padrão de acúmulo de papéis regulatórios distintos, com estrutura societária como quinta perna em vez de multa ambiental | Não encontrado |

Como em `relevantes.md`: um 🟢 aqui é candidato a ângulo inédito, não
confirmação — fontes pagas e teses fora do índice de busca não aparecem em
nenhuma varredura.
