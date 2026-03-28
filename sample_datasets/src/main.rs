use duckdb::Connection;
use std::fs::OpenOptions;
use std::io::{BufWriter, Write};
use std::sync::{Arc, Mutex};

fn strip_scheme(url: &str) -> &str {
    url.strip_prefix("https://")
        .or_else(|| url.strip_prefix("http://"))
        .unwrap_or(url)
}

fn main() -> anyhow::Result<()> {
    dotenvy::dotenv().ok();

    let endpoint_url = std::env::var("HETZNER_S3_ENDPOINT")?;
    let access_key   = std::env::var("AWS_ACCESS_KEY_ID")?;
    let secret_key   = std::env::var("AWS_SECRET_ACCESS_KEY")?;
    let s3_endpoint  = strip_scheme(&endpoint_url).to_owned();

    let con = Connection::open("basedosdados.duckdb")?;
    con.execute_batch("INSTALL httpfs; LOAD httpfs;")?;
    con.execute_batch(&format!(
        "SET s3_endpoint='{s3_endpoint}';
         SET s3_access_key_id='{access_key}';
         SET s3_secret_access_key='{secret_key}';
         SET s3_url_style='path';
         SET enable_object_cache=true;
         SET threads=4;
         SET memory_limit='6GB';"
    ))?;

    let file = OpenOptions::new()
        .create(true)
        .append(true)
        .open("dataset_sample.txt")?;
    let out = Arc::new(Mutex::new(BufWriter::new(file)));

    let out_ctrlc = out.clone();
    ctrlc::set_handler(move || {
        eprintln!("\nCancelled.");
        if let Ok(mut w) = out_ctrlc.lock() {
            let _ = w.flush();
        }
        std::process::exit(0);
    })?;

    writeln!(out.lock().unwrap(), "# Dataset samples with Headers as column_name:column_type\n")?;

    let mut schemas: Vec<String> = {
        let mut stmt = con.prepare(
            "SELECT schema_name FROM information_schema.schemata \
             WHERE schema_name NOT IN ('main', 'information_schema', 'pg_catalog')"
        )?;
        stmt.query_map([], |row| row.get(0))?
            .filter_map(|r| r.ok())
            .collect()
    };
    schemas.sort();

    for schema in &schemas {
        let mut tables: Vec<String> = {
            let mut stmt = con.prepare(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = ?"
            )?;
            stmt.query_map([schema], |row| row.get(0))?
                .filter_map(|r| r.ok())
                .collect()
        };
        tables.sort();

        for table in &tables {
            let full = format!("{schema}.{table}");
            let result = (|| -> anyhow::Result<()> {
                let safe_cols: Vec<String> = {
                    let mut desc = con.prepare(&format!("DESCRIBE {full}"))?;
                    desc.query_map([], |row| {
                        let name: String = row.get(0)?;
                        let col_type: String = row.get(1)?;
                        Ok((name, col_type))
                    })?
                    .filter_map(|r| r.ok())
                    .filter(|(_, t)| !t.to_uppercase().contains("GEOMETRY"))
                    .map(|(n, _)| format!("\"{n}\""))
                    .collect()
                };

                if safe_cols.is_empty() {
                    return Ok(());
                }

                let col_list = safe_cols.join(", ");
                let mut stmt = con.prepare(&format!(
                    "SELECT {col_list} FROM {full} USING SAMPLE 2 ROWS"
                ))?;

                let batches: Vec<_> = stmt.query_arrow([])?.collect();

                if batches.is_empty() {
                    return Ok(());
                }

                let arrow_schema = batches[0].schema();
                let header: Vec<String> = arrow_schema.fields().iter()
                    .map(|f| format!("{}:{}", f.name(), f.data_type()))
                    .collect();

                let mut w = out.lock().unwrap();
                writeln!(w, "## {schema}/{table}/")?;
                writeln!(w, "{}", header.join(","))?;

                for batch in &batches {
                    for row_idx in 0..batch.num_rows() {
                        let vals: Vec<String> = batch.columns().iter().map(|col| {
                            use arrow::array::Array;
                            if col.is_null(row_idx) {
                                return String::new();
                            }
                            arrow::util::display::array_value_to_string(col, row_idx)
                                .unwrap_or_default()
                        }).collect();
                        writeln!(w, "{}", vals.join(","))?;
                    }
                }

                writeln!(w)?;
                w.flush()?;
                Ok(())
            })();

            match result {
                Ok(_) => println!("done: {full}"),
                Err(e) => {
                    let mut w = out.lock().unwrap();
                    writeln!(w, "## {schema}/{table}/")?;
                    writeln!(w, "[error: {e}]\n")?;
                    let _ = w.flush();
                    eprintln!("error: {full}: {e}");
                }
            }
        }
    }

    Ok(())
}
