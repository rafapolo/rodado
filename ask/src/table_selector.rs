use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;

const DEFAULT_SIMILARITY_THRESHOLD: f32 = 0.35;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TableEmbedding {
    pub id: String,
    pub text: String,
    pub embedding: Vec<f32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EmbeddingsIndex {
    pub tables: Vec<TableEmbedding>,
    pub model: String,
}

pub struct TableSelector {
    tables: Vec<TableEmbedding>,
    threshold: f32,
}

impl TableSelector {
    pub fn new<P: AsRef<Path>>(embeddings_path: P, threshold: f32) -> anyhow::Result<Self> {
        let content = fs::read_to_string(embeddings_path)?;
        let index: EmbeddingsIndex = serde_json::from_str(&content)?;
        Ok(Self {
            tables: index.tables,
            threshold,
        })
    }

    pub fn select_tables(
        &self,
        question: &str,
        model: &dyn QuestionEmbedder,
    ) -> anyhow::Result<Vec<String>> {
        let question_embedding = model.embed(question)?;

        let mut similarities: Vec<(usize, f32)> = self
            .tables
            .iter()
            .enumerate()
            .map(|(i, table)| {
                let sim = cosine_similarity(&question_embedding, &table.embedding);
                (i, sim)
            })
            .collect();

        similarities.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));

        let selected: Vec<String> = similarities
            .into_iter()
            .filter(|(_, sim)| *sim >= self.threshold)
            .map(|(i, sim)| {
                eprintln!("  {} (similarity: {:.3})", self.tables[i].id, sim);
                self.tables[i].id.clone()
            })
            .collect();

        Ok(selected)
    }

    pub fn get_table_texts(&self, table_ids: &[String]) -> Vec<String> {
        table_ids
            .iter()
            .filter_map(|id| self.tables.iter().find(|t| &t.id == id))
            .map(|t| t.text.clone())
            .collect()
    }

    pub fn table_count(&self) -> usize {
        self.tables.len()
    }
}

pub trait QuestionEmbedder: Send + Sync {
    fn embed(&self, text: &str) -> anyhow::Result<Vec<f32>>;
}

pub struct LocalEmbedder {
    model_path: String,
}

impl LocalEmbedder {
    pub fn new(model_path: String) -> Self {
        Self { model_path }
    }
}

impl QuestionEmbedder for LocalEmbedder {
    fn embed(&self, text: &str) -> anyhow::Result<Vec<f32>> {
        use std::process::Command;

        let output = Command::new("python3")
            .args([
                "-c",
                &format!(
                    r#"
import json
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('{}')
emb = model.encode('{}', convert_to_numpy=True)
print(json.dumps([float(x) for x in emb]))
"#,
                    self.model_path,
                    text.replace("'", "\\'")
                ),
            ])
            .output()?;

        if !output.status.success() {
            let err = String::from_utf8_lossy(&output.stderr);
            anyhow::bail!("Embedding generation failed: {}", err);
        }

        let output_str = String::from_utf8_lossy(&output.stdout);
        let floats: Vec<f32> = serde_json::from_str(&output_str)?;

        Ok(floats)
    }
}

fn cosine_similarity(a: &[f32], b: &[f32]) -> f32 {
    let dot_product: f32 = a.iter().zip(b.iter()).map(|(x, y)| x * y).sum();
    let norm_a: f32 = a.iter().map(|x| x * x).sum::<f32>().sqrt();
    let norm_b: f32 = b.iter().map(|x| x * x).sum::<f32>().sqrt();

    if norm_a == 0.0 || norm_b == 0.0 {
        0.0
    } else {
        dot_product / (norm_a * norm_b)
    }
}

pub fn select_tables_from_question(
    question: &str,
    embeddings_path: &str,
    threshold: f32,
) -> anyhow::Result<Vec<String>> {
    let selector = TableSelector::new(embeddings_path, threshold)?;
    let embedder = LocalEmbedder::new("all-MiniLM-L6-v2".to_string());
    selector.select_tables(question, &embedder)
}
