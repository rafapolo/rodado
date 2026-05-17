# Investigação de Empresas com CNPJ em Casos de Corrupção com o Estado

## Tabelas para investigar a partir de um CNPJ

### Layer 1 — Identidade e estrutura da empresa

| Tabela | Por quê |
|---|---|
| `br_me_cnpj.empresas` | Razão social, natureza jurídica, porte, capital social via `cnpj_basico` |
| `br_me_cnpj.estabelecimentos` | Todas as filiais (matriz + filiais), situação cadastral, CNAE, endereço, datas — via `cnpj` ou `cnpj_basico` |
| `br_me_cnpj.socios` | Quem controla a empresa — pivô para mapear redes de ownership via `cnpj_basico` |
| `br_me_cnpj.simples` | Status Simples Nacional / MEI — útil para sinalizar empresas de fachada |
| `br_bd_diretorios_brasil.empresa` | Diretório cruzado com campos enriquecidos |

### Layer 2 — Licitações e contratos federais

| Tabela | Por quê |
|---|---|
| `br_cgu_licitacao_contrato.licitacao` | Todos os processos licitatórios federais — filtre por `sigla_uf`, una a contratos |
| `br_cgu_licitacao_contrato.licitacao_participante` | **Chave** — quais CNPJs participaram de cada licitação |
| `br_cgu_licitacao_contrato.licitacao_item` | Itens adquiridos — detectar superfaturamento |
| `br_cgu_licitacao_contrato.contrato_compra` | Contratos firmados — tem `cnpj_contratado`, `valor_global`, `situacao_contrato` |
| `br_cgu_licitacao_contrato.contrato_item` | Breakdown itemizado do contrato |
| `br_cgu_licitacao_contrato.contrato_apostilamento` | Apostilamentos — sinaliza inflação de valor pós-adjudicação |
| `br_cgu_licitacao_contrato.contrato_termo_aditivo` | Termos aditivos — mesmo sinal de alerta |
| `br_cgu_licitacao_contrato.licitacao_empenho` | Liga licitação → empenho (comprometimento orçamentário) |

### Layer 3 — Licitações estaduais/municipais (dados World Bank MIDES)

| Tabela | Por quê |
|---|---|
| `world_wb_mides.licitacao` | Licitações estaduais (tem campos de vencedor com CNPJ) |
| `world_wb_mides.licitacao_participante` | Tem `documento` (CNPJ/CPF) e `razao_social` de cada participante |
| `world_wb_mides.licitacao_item` | Itens por licitação em nível estadual |
| `world_wb_mides.empenho` | Comprometimentos orçamentários ligados a licitações |
| `world_wb_mides.liquidacao` | Autorização de pagamento — confirma que o dinheiro se moveu |
| `world_wb_mides.pagamento` | Pagamentos efetivos — confirmação final do fluxo financeiro |
| `world_wb_mides.relacionamentos` | Vínculos explícitos empenho↔licitação |

### Layer 4 — Fluxos orçamentários e transferências

| Tabela | Por quê |
|---|---|
| `br_cgu_orcamento_publico.orcamento` | Dotações orçamentárias federais por órgão |
| `br_cgu_cartao_pagamento.microdados_governo_federal` | Gastos com cartão corporativo — frequentemente usado para burlar regras de licitação |
| `br_cgu_cartao_pagamento.microdados_compras_centralizadas` | Compras centralizadas via cartão governamental |
| `br_me_sic.transferencia` | Transferências federal→estadual/municipal — seguir o dinheiro a jusante |
| `br_me_siconfi.uf_despesas_orcamentarias` | Execução orçamentária estadual |
| `br_me_siconfi.municipio_despesas_orcamentarias` | Execução orçamentária municipal |
| `br_cgu_emendas_parlamentares.microdados` | Emendas parlamentares — vetor clássico de corrupção, liga políticos a contratadas |

### Layer 5 — Financiamento de campanha (conexão política)

| Tabela | Por quê |
|---|---|
| `br_tse_eleicoes.receitas_candidato` | Doações recebidas — verificar se o CNPJ doou a políticos |
| `br_tse_eleicoes.despesas_candidato` | Gastos — se a empresa recebeu pagamentos de campanhas |
| `br_tse_eleicoes.receitas_comite` / `receitas_orgao_partidario` | Financiamento partidário |
| `br_tse_eleicoes.candidatos` | Cruzar donos da empresa (sócios) com candidatos via CPF |
| `br_tse_filiacao_partidaria.microdados` | Os donos da empresa são filiados a partidos? |

### Layer 6 — Obras e imóveis

| Tabela | Por quê |
|---|---|
| `br_rf_cno.microdados` | Cadastro Nacional de Obras — empresas registradas como responsáveis por obra |
| `br_rf_cno.vinculos` | Vínculos entre CNO e entidade responsável |
| `br_rf_cno.cnaes` | CNAE declarado na obra |
| `br_rf_cafir.imoveis_rurais` | Registro de imóveis rurais — útil para rastreamento de ativos |

---

## Sequência de investigação sugerida

```
CNPJ → br_me_cnpj.estabelecimentos          (perfil, status, CNAE)
      → br_me_cnpj.socios                    (quem controla, obter CPFs)
      → br_cgu_licitacao_contrato.licitacao_participante  (todas as licitações que participou)
      → br_cgu_licitacao_contrato.contrato_compra         (contratos ganhos)
      → world_wb_mides.licitacao_participante             (licitações estaduais)
      → world_wb_mides.pagamento                          (dinheiro pago)
      → br_tse_eleicoes.receitas_candidato   (doações do CNPJ)
      → br_cgu_emendas_parlamentares         (qual político direcionou R$ à área)
```

---

## Lacunas conhecidas

**CEIS/CNEP** (listas federais de suspensão/sanção) e **achados de auditoria TCU/TCE** não estão presentes neste dataset. Devem ser cruzados de fontes externas. Todo o restante para uma cadeia completa de procurement→pagamento→financiamento-de-campanha está disponível.
