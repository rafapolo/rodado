# Pesquisa: Desigualdade Fundiária, Raça e Espaço Urbano no Brasil

Baseado nos estudos da Fundação Heinrich Böll e artigo acadêmico sobre segregação urbana em Fortaleza-CE.

---

## Status Geral

| Categoria | Respondidas | Não Respondidas |
|-----------|-------------|-----------------|
| A. Fundiário | 0/5 | A1-A5 ❌ |
| B. Fortaleza | 0/5 | B1-B5 ❌ |
| C. Gênero/Terra | 1/4 | C1✅, C2-C4 ❌ |
| D. Evolução | 1/4 | D1-D3 ❌, D4✅ |
| E. Condições Vida | 3/4 | E1❌, E2-E4 ✅ |
| F. Interseccionalidade | 2/3 | F1⚠️, F2✅, F3❌ |
| **Total** | **7/36** | **29 ❌** |

**Arquivo de Respostas**: `respostas.md`

---

## Principais Descobertas

### Infraestrutura Urbana (Census 2010)

| Indicador | Valor |
|-----------|-------|
| Domicílios urbanos | 57,2 milhões |
| Com iluminação pública | 78,4% |
| Com esgoto a céu aberto | 77,4% |
| Com pavimentação | 66,5% |
| Sem pavimentação | 33,5% |
| Sem calçada | 43,7% |

### Responsáveis por Domicílio

| Sexo | Total | % |
|------|-------|---|
| Homens | 57.449.271 | 72,1% |
| Mulheres | 22.242.888 | 28,0% |

### Piores UFs em Pavimentação

| UF | % Sem Pavimentação |
|----|---------------------|
| RO | 42,1% |
| PA | 34,5% |
| AP | 33,8% |
| MT | 30,9% |

### Arquivos Disponíveis
- `respostas.md` - Respostas completas
- `dicionarios/setor_censitario_entorno_2010.md` - Dicionário de entorno

---

## A. Terra e Desigualdade Fundiária

### A1. Concentração de terras por cor/raça do produtor
**Encontrado no texto**: "90% dos estabelecimentos rurais acima de 2.500 hectares estão sob propriedade de brancos"

**Objetivo**: Verificar se a concentração fundiária segue padrão racial.

---

### A2. Área total por cor/raça
**Encontrado no texto**: "Produtores rurais brancos ocupam 208 milhões de hectares (59,4%) enquanto negros ocupam cerca de 99 milhões de hectares (28,3%)"

**Objetivo**: Quantificar a distribuição absoluta de terras por grupo racial.

---

### A3. Correlação tamanho do imóvel × cor do proprietário
**Encontrado no texto**: "Quanto maior a extensão do estabelecimento rural mais branco é o seu proprietário"

**Objetivo**: Testar se existe correlação positiva entre tamanho da propriedade e branquitude.

---

### A4. Produtores de soja por cor/raça
**Encontrado no texto**: "88,24% dos produtores de soja são brancos"

**Objetivo**: Identificar a correlação entre culturas de exportação e perfil racial dos produtores.

---

### A5. Índice de Gini fundiário brasileiro
**Encontrado no texto**: "O Índice de Gini da distribuição de terras no Brasil foi, em 2017, de 0,867"

**Objetivo**: Comparar com dados do census e trackar evolução histórica.

---

## B. Segregação Urbana em Fortaleza

### B1. Percentual de população negra por bairro em Fortaleza (2010)
**Encontrado no texto**: "Fortaleza possuía, em 2010, 1.514.103 pessoas autodeclaradas negras, o que corresponde a 61,8% da população"

**Objetivo**: Reproduzir a estatística e mapear distribuição por bairro/setor.

---

### B2. Comparação Meireles vs. Conjunto Palmeiras
**Encontrado no texto**: "No Meireles, bairro com maior renda média, o percentual [de negros] cai para 33,1%. O bairro de menor renda média é o Conjunto Palmeiras, no qual o percentual de pessoas negras soma 71,8%"

**Objetivo**: Comparar segregação racial entre bairros de alta e baixa renda.

---

### B3. Concentração de brancos em áreas de alta renda
**Encontrado no texto**: "Concentração de renda e de imóveis de alto padrão coincide com a concentração de pessoas brancas"

**Objetivo**: Mapear correlação entre renda, cor/raça e localização espacial.

---

### B4. Mapas de calor de população negra em áreas periféricas
**Encontrado no texto**: "Kernel density maps mostrando concentração de população negra em áreas periféricas"

**Objetivo**: Reproduzir análise espacial usando dados censitários.

---

### B5. Assentamentos precários e população negra
**Encontrado no texto**: "O Poço da Draga: ~85% negros; Pirambu, Lagamar, Mucuripe: ~70%; Campo do América: 64%"

**Objetivo**: Verificar se assentamentos precários têm composição racial distinta.

---

## C. Gênero, Raça e Acesso à Terra

### C1. Responsáveis por domicílios por sexo e cor/raça
**Encontrado no texto**: "Mulheres negras com menos direitos de acesso à terra e mais responsabilidades"

**Objetivo**: Quantificar desigualdade na titularidade de domicílios.

---

### C2. Evolução da inclusão de gênero no Censo Agropecuário
**Encontrado no texto**: "Apenas em 2006 o Censo Agropecuário introduziu a variável sexo do(a) produtor(a)"

**Objetivo**: Documentar evolução temporal da variável gênero nos censos.

---

### C3. Produtoras visibilizadas no Censo 2017
**Encontrado no texto**: "871 mil produtoras foram visibilizadas" em 2017

**Objetivo**: Verificar dados no dataset de censos agropecuários.

---

### C4. Participação de mulheres na agricultura familiar
**Encontrado no texto**: "70% do consumo da agricultura familiar vem das hortas e quintais administrados por mulheres"

**Nota**: Este dado vem do GT Mulheres da ANA, não diretamente do IBGE.

---

## D. Evolução Histórica (1970-2022)

### D1. Evolução do Gini fundiário
**Encontrado no texto**: "O Gini fundiário brasileiro era 0,854 em 2006, 0,856 em 1995/96, 0,857 em 1985"

**Objetivo**: Trackar evolução temporal da concentração fundiária.

---

### D2. Propriedade por tamanho (% acumulativa)
**Encontrado no texto**: "1% das maiores propriedades operam e controlam 70% da terra agrícola; 84% das propriedades com menos de 2 hectares disputam apenas 12%"

**Objetivo**: Calcular distribuição acumulativa de terras por tamanho.

---

### D3. Expansão da fronteira agrícola e concentração
**Encontrado no texto**: "Mato Grosso possui o maior número de estabelecimentos rurais acima de 10 mil hectares"

**Objetivo**: Analisar relação entre expansão agrícola e concentração fundiária.

---

### D4. Autodeclaração de cor/raça 2010 vs 2022
**Encontrado no texto**: "Previsão de aumento da autodeclaração de pessoas negras no Censo 2022"

**Objetivo**: Comparar distribuição racial entre censos.

---

## E. Condições de Vida e Domicílio

### E1. Renda média em áreas afetadas por desastres ambientais
**Encontrado no texto**: "A renda média em Córrego era de menos de 2 salários-mínimos" (área afetada por Mariana)

**Objetivo**: Identificar perfil socioeconômico de áreas vulneráveis.

---

### E2. Indicadores de infraestrutura por cor/raça e gênero
**Encontrado no texto**: "Domicílios de mulheres negras com piores indicadores de infraestrutura"

**Objetivo**: Tabular acesso a água, saneamento, energia por cruzamento de variáveis.

**Solução**: Usar `setor_censitario_entorno_2010` com dicionário disponível em:
`docs/pesquisa/dicionarios/setor_censitario_entorno_2010.md`

**Status**: ✅ Respondida - ver `respostas.md`

---

### E3. Taxa de alfabetização por cor/raça
**Encontrado no texto**: Desigualdade educacional entre grupos raciais

**Objetivo**: Medir gap de alfabetização usando dados de setor censitário.

**Status**: ✅ Respondida - disponível em `br_ibge_censo_2022.alfabetizacao_grupo_idade_sexo_raca`

---

### E4. Índice de envelhecimento por cor/raça
**Encontrado no texto**: Envelhecimento populacional diferenciado por grupo racial

**Objetivo**: Analisar estrutura etária por cor/raça.

**Status**: ✅ Respondida - disponível em `br_ibge_censo_2022.indice_envelhecimento_raca`

---

## F. Interseccionalidade

### F1. Análise multidimensional: Raça × Classe × Gênero
**Encontrado no texto**: "A interseccionalidade: raça, classe e gênero são eixos de opressão interligados"

**Objetivo**: Realizar análise multidimensional com todos os eixos simultaneamente.

**Status**: ⚠️ Parcialmente - cruzamento via setor censitário (sem cor/raça do responsável)

---

### F2. Domicílios em áreas de infraestrutura precária
**Encontrado no texto**: "Parcela da população em domicílios sem acesso a serviços básicos"

**Objetivo**: Quantificar carência infraestrutura por perfil racial.

**Status**: ✅ Respondida - ver `respostas.md` (77% com esgoto a céu aberto, 33% sem pavimentação)

---

### F3. População em domicílios coletivos por cor/raça
**Encontrado no texto**: Presença desproporcional de negros em domicílios coletivos

**Objetivo**: Analisar composição racial em domicílios coletivos (presídios, asilos, etc).

**Status**: ❌ Não disponível - Census 2022 não distingue domicílios coletivos por cor/raça

---

## Fontes dos Textos Base

1. **Raça, Gênero e Classe: As Interseccionalidades da Estrutura Fundiária Brasileira** (Fundação Heinrich Böll, 2022)
   - Autoras: Fabrina Furtado, Karina Kato, Orlando Aleixo de Barros Junior

2. **Raça e terra: Implicações do racismo fundiário na segregação urbana em Fortaleza-CE** (Revista Brasileira de Gestão Urbana, 2024)
   - Artigo acadêmico sobre segregação racial em Fortaleza

---

## Datasets Base dos Dados Utilizáveis

| Dataset | Anos | Variáveis Relevantes |
|---------|------|---------------------|
| `br_ibge_censo_2022` | 2022 | cor_raca, sexo, setor_censitario, domicílio |
| `br_ibge_censo_demografico` | 1970-2010 | cor_raca, sexo, setor_censitario |
| `br_ibge_pib.gini` | - | Gini de renda (não fundiário) |
| `br_ibge_populacao` | - | População por município/ano |
| `br_ibge_pam` | - | Produção agrícola por município |

---

### Arquivos de Resposta
- `respostas.md` - Respostas detalhadas com queries SQL
- `dicionarios/setor_censitario_entorno_2010.md` - Dicionário de entorno
- `dicionarios/setor_censitario_entorno_2010.json` - Dicionário em JSON
