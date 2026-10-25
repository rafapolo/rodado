-- Cadastro atual (09/2026): estabelecimentos com o telefone 61 3131-3131, com o telefone da própria
-- Voga (61 3964-0691) e com e-mail @vogasc — quantos têm cada combinação
WITH f AS (
  SELECT cnpj,
    coalesce((ddd_1 = '61' AND telefone_1 = '31313131') OR (ddd_2 = '61' AND telefone_2 = '31313131'), false) AS tel_3131,
    coalesce((ddd_1 = '61' AND telefone_1 = '39640691') OR (ddd_2 = '61' AND telefone_2 = '39640691'), false) AS tel_voga,
    coalesce(lower(email) LIKE '%vogasc%', false) AS email_voga
  FROM br_me_cnpj.estabelecimentos
  WHERE telefone_1 IN ('31313131', '39640691') OR telefone_2 IN ('31313131', '39640691') OR lower(email) LIKE '%vogasc%'
)
SELECT tel_3131, tel_voga, email_voga, count(*) AS estabelecimentos
FROM f WHERE tel_3131 OR tel_voga OR email_voga
GROUP BY ALL ORDER BY estabelecimentos DESC;
