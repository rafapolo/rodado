//! Tier 1: resolve a question to a named metric before spending an LLM call.
//!
//! The pipeline used to have one path — embed the question, take the top-K
//! tables, prompt the model. That is the right tool for an open question and
//! the wrong one for "quantos habitantes tem SP?", which has a single correct
//! answer that `docs/context/metrics.yaml` already states.
//!
//! Matching is exact after normalization, over metric names and their pt-BR
//! synonyms — never similarity. A score is a poor proxy for whether a metric
//! *can* answer: "população de São Paulo" and "população carcerária" sit close
//! together in embedding space and want completely different tables.
//!
//! Two outcomes, and the second matters as much as the first:
//!   - a metric matched and the question carries nothing but an optional UF and
//!     year → build the SQL here, no model involved
//!   - anything else → hand the definition to the LLM as context, so even the
//!     fall-through gets the verified expression instead of re-deriving it

use anyhow::{Context, Result};
use serde::Deserialize;
use std::fs;

#[derive(Debug, Deserialize, Clone)]
pub struct Metric {
    pub name: String,
    pub description: String,
    pub unit: String,
    pub source_table: String,
    pub expression: String,
    #[serde(default)]
    pub required_filters: Vec<String>,
    #[serde(default)]
    pub synonyms: Vec<String>,
    #[serde(default)]
    pub caveat: String,
    #[serde(default)]
    pub needs_join: Option<serde_json::Value>,
}

#[derive(Debug, Deserialize)]
struct MetricsFile {
    metrics: Vec<Metric>,
}

pub struct Resolution {
    pub metric: Metric,
    /// Deterministic SQL, when the question was simple enough to build it.
    pub sql: Option<String>,
    /// Always present: what to tell the model when we fall through.
    pub context: String,
}

const UFS: [&str; 27] = [
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG",
    "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
];

fn normalize(s: &str) -> String {
    s.chars()
        .map(|c| match c {
            'á' | 'à' | 'â' | 'ã' | 'ä' => 'a',
            'é' | 'ê' | 'ë' => 'e',
            'í' | 'ï' => 'i',
            'ó' | 'ô' | 'õ' | 'ö' => 'o',
            'ú' | 'ü' => 'u',
            'ç' => 'c',
            c => c,
        })
        .filter(|c| c.is_alphanumeric() || c.is_whitespace())
        .collect::<String>()
        .to_lowercase()
}

pub fn load(path: &str) -> Result<Vec<Metric>> {
    let raw = fs::read_to_string(path)
        .with_context(|| format!("Não foi possível ler as métricas: {}", path))?;
    let parsed: MetricsFile = serde_json::from_str(&raw)
        .with_context(|| format!("JSON de métricas inválido: {}", path))?;
    Ok(parsed.metrics)
}

/// Longest match wins, so "populacao carceraria" never resolves as "populacao".
fn find<'a>(metrics: &'a [Metric], question: &str) -> Option<&'a Metric> {
    let q = format!(" {} ", normalize(question));
    let mut best: Option<(usize, &Metric)> = None;
    for m in metrics {
        for term in std::iter::once(&m.name).chain(m.synonyms.iter()) {
            let t = normalize(term);
            if t.is_empty() || !q.contains(&format!(" {} ", t)) {
                continue;
            }
            if best.map_or(true, |(len, _)| t.len() > len) {
                best = Some((t.len(), m));
            }
        }
    }
    best.map(|(_, m)| m)
}

fn find_year(question: &str) -> Option<i32> {
    let bytes: Vec<char> = question.chars().collect();
    let mut i = 0;
    while i + 4 <= bytes.len() {
        if bytes[i..i + 4].iter().all(|c| c.is_ascii_digit()) {
            let before_ok = i == 0 || !bytes[i - 1].is_ascii_digit();
            let after_ok = i + 4 == bytes.len() || !bytes[i + 4].is_ascii_digit();
            if before_ok && after_ok {
                let year: i32 = bytes[i..i + 4].iter().collect::<String>().parse().ok()?;
                if (1900..=2100).contains(&year) {
                    return Some(year);
                }
            }
        }
        i += 1;
    }
    None
}

fn find_uf(question: &str) -> Option<&'static str> {
    let q = format!(" {} ", question.to_uppercase());
    UFS.iter().find(|uf| q.contains(&format!(" {} ", uf))).copied()
}

/// Words that carry no meaning for metric resolution. Anything left over after
/// stripping these is a qualifier we cannot honour deterministically, so we
/// fall through rather than answer a narrower question than the one asked.
const FILLER: [&str; 34] = [
    "qual", "quais", "quanto", "quantos", "quantas", "e", "o", "a", "os", "as",
    "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas", "um", "uma",
    "por", "para", "com", "foi", "era", "tem", "teve", "ha", "the", "total",
    "me", "diga",
];

fn leftover_terms(question: &str, metric: &Metric, year: Option<i32>, uf: Option<&str>) -> Vec<String> {
    let mut consumed: Vec<String> = vec![normalize(&metric.name)];
    consumed.extend(metric.synonyms.iter().map(|s| normalize(s)));
    if let Some(y) = year {
        consumed.push(y.to_string());
    }
    if let Some(u) = uf {
        consumed.push(normalize(u));
    }
    let q = normalize(question);
    let mut rest = q.clone();
    // Strip the longest consumed phrases first so multi-word synonyms go whole.
    let mut sorted = consumed.clone();
    sorted.sort_by_key(|s| std::cmp::Reverse(s.len()));
    for c in sorted {
        if !c.is_empty() {
            rest = rest.replace(&c, " ");
        }
    }
    rest.split_whitespace()
        .filter(|w| !FILLER.contains(w) && w.len() > 1)
        .map(|w| w.to_string())
        .collect()
}

pub fn resolve(metrics: &[Metric], question: &str) -> Option<Resolution> {
    let metric = find(metrics, question)?.clone();
    let year = find_year(question);
    let uf = find_uf(question);
    let leftover = leftover_terms(question, &metric, year, uf);

    let mut context = format!(
        "Métrica reconhecida: {} — {}\n  unidade: {}\n  tabela: {}\n  expressão: {}\n  filtros obrigatórios: {}",
        metric.name,
        metric.description,
        metric.unit,
        metric.source_table,
        metric.expression,
        metric.required_filters.join(", ")
    );
    if !metric.caveat.is_empty() {
        context.push_str(&format!("\n  atenção: {}", metric.caveat));
    }
    if metric.needs_join.is_some() {
        context.push_str("\n  precisa de join — veja needs_join em metrics.yaml");
    }

    // Only build SQL when nothing in the question is left unexplained, the
    // metric needs no join, and every required filter can be satisfied.
    let can_build = leftover.is_empty()
        && metric.needs_join.is_none()
        && metric
            .required_filters
            .iter()
            .all(|f| f != "ano" || year.is_some());

    let sql = if can_build {
        let mut wheres: Vec<String> = Vec::new();
        if let Some(y) = year {
            wheres.push(format!("ano = {}", y));
        }
        if let Some(u) = uf {
            wheres.push(format!("sigla_uf = '{}'", u));
        }
        let clause = if wheres.is_empty() {
            String::new()
        } else {
            format!("\nWHERE {}", wheres.join("\n  AND "))
        };
        // No trailing semicolon: the caller wraps this in `SELECT … FROM (…) __q`
        // to probe the result metadata, and a `;` inside that parenthesis is a
        // parse error.
        Some(format!(
            "SELECT {} AS {}\nFROM {}{}",
            metric.expression, metric.name, metric.source_table, clause
        ))
    } else {
        None
    };

    Some(Resolution { metric, sql, context })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn fixtures() -> Vec<Metric> {
        vec![
            Metric {
                name: "populacao".into(),
                description: "população residente".into(),
                unit: "pessoas".into(),
                source_table: "br_ibge_populacao.municipio".into(),
                expression: "SUM(populacao)".into(),
                required_filters: vec!["ano".into()],
                synonyms: vec!["habitantes".into(), "pop".into()],
                caveat: String::new(),
                needs_join: None,
            },
            Metric {
                name: "pib_per_capita".into(),
                description: "PIB por habitante".into(),
                unit: "BRL".into(),
                source_table: "br_ibge_pib.municipio".into(),
                expression: "SUM(pib) / NULLIF(SUM(populacao), 0)".into(),
                required_filters: vec!["ano".into()],
                synonyms: vec!["pib per capita".into()],
                caveat: String::new(),
                needs_join: Some(serde_json::json!({"table": "x"})),
            },
        ]
    }

    #[test]
    fn builds_sql_for_a_bare_metric_question() {
        let r = resolve(&fixtures(), "quantos habitantes em SP em 2022?").unwrap();
        let sql = r.sql.expect("should resolve deterministically");
        assert!(sql.contains("SUM(populacao)"));
        assert!(sql.contains("ano = 2022"));
        assert!(sql.contains("sigla_uf = 'SP'"));
        assert!(!sql.contains(';'), "the caller wraps this in a subquery");
    }

    #[test]
    fn accents_and_case_do_not_matter() {
        assert!(resolve(&fixtures(), "População em 2022").is_some());
    }

    #[test]
    fn falls_through_when_the_required_year_is_missing() {
        let r = resolve(&fixtures(), "quantos habitantes em SP?").unwrap();
        assert!(r.sql.is_none(), "no year means no deterministic answer");
        assert!(r.context.contains("SUM(populacao)"));
    }

    #[test]
    fn falls_through_when_the_question_asks_for_more() {
        // "por município" is a grouping we did not honour — answering the
        // aggregate would silently answer a different question
        let r = resolve(&fixtures(), "populacao por municipio em 2022").unwrap();
        assert!(r.sql.is_none());
    }

    #[test]
    fn falls_through_when_the_metric_needs_a_join() {
        let r = resolve(&fixtures(), "pib per capita em 2021").unwrap();
        assert!(r.sql.is_none());
        assert!(r.context.contains("precisa de join"));
    }

    #[test]
    fn unknown_question_resolves_to_nothing() {
        assert!(resolve(&fixtures(), "quais escolas fecharam").is_none());
    }

    #[test]
    fn longest_match_wins() {
        let r = resolve(&fixtures(), "pib per capita em 2021").unwrap();
        assert_eq!(r.metric.name, "pib_per_capita");
    }

    #[test]
    fn year_must_be_a_standalone_four_digit_number() {
        assert_eq!(find_year("populacao em 2022"), Some(2022));
        assert_eq!(find_year("cnpj 123456789012"), None);
    }
}
