use serde::{Deserialize, Serialize};
use std::collections::HashSet;
use std::fs;
use std::path::Path;

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Column {
    pub name: String,
    #[serde(rename = "type")]
    pub col_type: String,
    pub description: Option<String>,
}

pub type TableColumns = Vec<Column>;

#[derive(Debug, Clone, Deserialize)]
pub struct FullSchema {
    #[serde(flatten)]
    pub datasets:
        std::collections::HashMap<String, std::collections::HashMap<String, TableColumns>>,
}

pub struct SchemaFilter {
    schema: FullSchema,
}

impl SchemaFilter {
    pub fn new<P: AsRef<Path>>(schema_path: P) -> anyhow::Result<Self> {
        let content = fs::read_to_string(schema_path)?;
        let schema: FullSchema = serde_json::from_str(&content)?;
        Ok(Self { schema })
    }

    pub fn filter_tables(&self, table_ids: &[String]) -> String {
        let selected: HashSet<String> = table_ids.iter().cloned().collect();
        let mut lines = Vec::new();

        lines.push("# Base dos Dados — Filtered Schema".to_string());
        lines.push(
            "# Legend: V=VARCHAR I=INT D=DOUBLE Dt=DATE B=BOOLEAN Dec=DECIMAL Ts=TIMESTAMP Ti=TIME"
                .to_string(),
        );
        lines.push("# Format: dataset.table: col:TYPE description".to_string());
        lines.push(String::new());

        for (dataset, tables) in &self.schema.datasets {
            for (table, columns) in tables {
                let full_id = format!("{}.{}", dataset, table);
                if selected.contains(&full_id) {
                    let col_str = columns
                        .iter()
                        .map(|c| {
                            let desc = c.description.as_deref().unwrap_or("");
                            if desc.is_empty() {
                                format!("{}:{}", c.name, type_abbrev(&c.col_type))
                            } else {
                                format!("{}:{} {}", c.name, type_abbrev(&c.col_type), desc)
                            }
                        })
                        .collect::<Vec<_>>()
                        .join(" ");

                    lines.push(format!("{}: {}", full_id, col_str));
                }
            }
        }

        lines.join("\n")
    }

    pub fn full_schema_text(&self) -> String {
        let mut lines = Vec::new();

        lines.push("# Base dos Dados — Full Schema".to_string());
        lines.push(
            "# Legend: V=VARCHAR I=INT D=DOUBLE Dt=DATE B=BOOLEAN Dec=DECIMAL Ts=TIMESTAMP Ti=TIME"
                .to_string(),
        );
        lines.push("# Format: dataset.table: col:TYPE description".to_string());
        lines.push(String::new());

        for (dataset, tables) in &self.schema.datasets {
            for (table, columns) in tables {
                let full_id = format!("{}.{}", dataset, table);
                let col_str = columns
                    .iter()
                    .map(|c| {
                        let desc = c.description.as_deref().unwrap_or("");
                        if desc.is_empty() {
                            format!("{}:{}", c.name, type_abbrev(&c.col_type))
                        } else {
                            format!("{}:{} {}", c.name, type_abbrev(&c.col_type), desc)
                        }
                    })
                    .collect::<Vec<_>>()
                    .join(" ");

                lines.push(format!("{}: {}", full_id, col_str));
            }
        }

        lines.join("\n")
    }

    pub fn dataset_count(&self) -> usize {
        self.schema.datasets.len()
    }

    pub fn table_count(&self) -> usize {
        self.schema.datasets.values().map(|t| t.len()).sum()
    }
}

fn type_abbrev(full_type: &str) -> String {
    let upper = full_type.to_uppercase();
    if upper.contains("VARCHAR") || upper.contains("STRING") {
        "V".to_string()
    } else if upper.contains("INT") {
        "I".to_string()
    } else if upper.contains("DOUBLE") || upper.contains("FLOAT") {
        "D".to_string()
    } else if upper.contains("DATE") && !upper.contains("TIMESTAMP") {
        "Dt".to_string()
    } else if upper.contains("TIMESTAMP") {
        "Ts".to_string()
    } else if upper.contains("TIME") {
        "Ti".to_string()
    } else if upper.contains("BOOLEAN") {
        "B".to_string()
    } else if upper.contains("DECIMAL") {
        "Dec".to_string()
    } else {
        full_type.to_string()
    }
}
