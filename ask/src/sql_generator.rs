use anyhow::{Context, Result};
use serde_json::Value;
use std::env;

pub trait SqlGenerator: Send + Sync {
    fn generate(&self, question: &str, schema: &str, prompt_template: &str) -> Result<String>;
}

pub fn create_sql_generator() -> Result<Box<dyn SqlGenerator>> {
    let generator_type = env::var("SQL_GENERATOR").unwrap_or_else(|_| "gemini".to_string());

    match generator_type.as_str() {
        "sqlcoder" => Ok(Box::new(SqlCoderGenerator::new()?)),
        "openrouter" => Ok(Box::new(OpenRouterGenerator::new()?)),
        "gemini" => Ok(Box::new(GeminiGenerator::new()?)),
        _ => anyhow::bail!(
            "Unknown SQL_GENERATOR: {}. Use: sqlcoder, gemini, or openrouter",
            generator_type
        ),
    }
}

pub struct GeminiGenerator {
    model: String,
    api_key: String,
}

impl GeminiGenerator {
    pub fn new() -> Result<Self> {
        let model = env::var("GEMINI_MODEL").unwrap_or_else(|_| "gemini-flash-latest".to_string());
        let api_key = env::var("GEMINI_API_KEY").context("GEMINI_API_KEY not defined")?;
        Ok(Self { model, api_key })
    }
}

impl SqlGenerator for GeminiGenerator {
    fn generate(&self, question: &str, schema: &str, prompt_template: &str) -> Result<String> {
        let url = format!(
            "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent",
            self.model
        );

        let system_prompt = format!("{}\n\nSchema DDL:\n\n{}", prompt_template.trim(), schema);

        let payload = serde_json::json!({
            "system_instruction": { "parts": [{ "text": system_prompt }] },
            "contents": [{ "parts": [{ "text": question }] }]
        });

        let client = reqwest::blocking::Client::builder()
            .timeout(std::time::Duration::from_secs(300))
            .build()?;

        let resp = client
            .post(&url)
            .header("Content-Type", "application/json")
            .header("X-goog-api-key", &self.api_key)
            .json(&payload)
            .send()
            .context("Gemini HTTP request failed")?;

        let status = resp.status();
        let body: Value = resp.json().context("Failed to parse Gemini response")?;

        if !status.is_success() {
            anyhow::bail!("Gemini API error {}: {}", status, body);
        }

        let text = body["candidates"][0]["content"]["parts"][0]["text"]
            .as_str()
            .context("Unexpected Gemini response format")?
            .trim()
            .to_string();

        Ok(strip_fences(&text))
    }
}

pub struct OpenRouterGenerator {
    model: String,
    api_key: String,
}

impl OpenRouterGenerator {
    pub fn new() -> Result<Self> {
        let model =
            env::var("OPENROUTER_MODEL").unwrap_or_else(|_| "openai/gpt-4o-mini".to_string());
        let api_key = env::var("OPENROUTER_API_KEY").context("OPENROUTER_API_KEY not defined")?;
        Ok(Self { model, api_key })
    }
}

impl SqlGenerator for OpenRouterGenerator {
    fn generate(&self, question: &str, schema: &str, prompt_template: &str) -> Result<String> {
        let url = "https://openrouter.ai/api/v1/chat/completions";

        let system_prompt = format!("{}\n\nSchema DDL:\n\n{}", prompt_template.trim(), schema);

        let payload = serde_json::json!({
            "model": self.model,
            "messages": [
                { "role": "system", "content": system_prompt },
                { "role": "user", "content": question }
            ]
        });

        let client = reqwest::blocking::Client::builder()
            .timeout(std::time::Duration::from_secs(300))
            .build()?;

        let resp = client
            .post(url)
            .header("Content-Type", "application/json")
            .header("Authorization", format!("Bearer {}", self.api_key))
            .header("HTTP-Referer", "https://basedosdados.org")
            .header("X-Title", "Base dos Dados Ask")
            .json(&payload)
            .send()
            .context("OpenRouter HTTP request failed")?;

        let status = resp.status();
        let body: Value = resp.json().context("Failed to parse OpenRouter response")?;

        if !status.is_success() {
            anyhow::bail!("OpenRouter API error {}: {}", status, body);
        }

        let text = body["choices"][0]["message"]["content"]
            .as_str()
            .context("Unexpected OpenRouter response format")?
            .trim()
            .to_string();

        Ok(strip_fences(&text))
    }
}

pub struct SqlCoderGenerator {
    model: String,
    host: String,
}

impl SqlCoderGenerator {
    pub fn new() -> Result<Self> {
        let model = env::var("OLLAMA_MODEL").unwrap_or_else(|_| "sqlcoder".to_string());
        let host = env::var("OLLAMA_HOST").unwrap_or_else(|_| "http://localhost:11434".to_string());
        Ok(Self { model, host })
    }
}

impl SqlGenerator for SqlCoderGenerator {
    fn generate(&self, question: &str, schema: &str, prompt_template: &str) -> Result<String> {
        let url = format!("{}/api/generate", self.host);

        let full_prompt = format!(
            "{}\n\nSchema DDL:\n\n{}\n\nQuestion: {}\n\nSQL:",
            prompt_template.trim(),
            schema,
            question
        );

        let payload = serde_json::json!({
            "model": self.model,
            "prompt": full_prompt,
            "stream": false
        });

        let client = reqwest::blocking::Client::builder()
            .timeout(std::time::Duration::from_secs(300))
            .build()?;

        let resp = client
            .post(&url)
            .header("Content-Type", "application/json")
            .json(&payload)
            .send()
            .context("Ollama HTTP request failed")?;

        let status = resp.status();
        let body: Value = resp.json().context("Failed to parse Ollama response")?;

        if !status.is_success() {
            anyhow::bail!("Ollama API error {}: {}", status, body);
        }

        let text = body["response"]
            .as_str()
            .context("Unexpected Ollama response format")?
            .trim()
            .to_string();

        Ok(strip_fences(&text))
    }
}

fn strip_fences(text: &str) -> String {
    let text = text.trim();
    if text.starts_with("```sql") {
        let end = text.find("```").unwrap_or(text.len());
        text[5..end].trim().to_string()
    } else if text.starts_with("```") {
        let end = text[3..].find("```").map(|i| i + 3).unwrap_or(text.len());
        text[3..end].trim().to_string()
    } else {
        text.to_string()
    }
}
