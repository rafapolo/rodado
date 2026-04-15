use clap::{Parser, ValueEnum};
use std::io::{self, Read};

#[derive(Clone, ValueEnum)]
enum Method {
    Get,
    Post,
}

#[derive(Parser)]
#[command(about = "Query a db endpoint (always returns JSON)")]
struct Args {
    /// SQL query (if omitted, reads from stdin)
    query: Option<String>,

    /// Base server URL
    #[arg(short, long, default_value = "https://db.xn--2dk.xyz")]
    server: String,

    /// API password (or set BASIC_AUTH_PASSWORD env var)
    #[arg(short, long, env = "BASIC_AUTH_PASSWORD")]
    password: String,

    /// HTTP method: GET sends query as ?q= param, POST sends as body
    #[arg(short = 'X', long, value_enum, default_value = "post")]
    method: Method,
}

fn main() {
    let args = Args::parse();

    let query = match args.query {
        Some(q) => q,
        None => {
            let mut buf = String::new();
            io::stdin().read_to_string(&mut buf).expect("failed to read stdin");
            buf
        }
    };

    let base = format!("{}/query", args.server.trim_end_matches('/'));
    let client = reqwest::blocking::Client::new();

    let resp = match args.method {
        Method::Get => client
            .get(&base)
            .header("X-Password", &args.password)
            .query(&[("q", &query)])
            .send()
            .expect("request failed"),
        Method::Post => client
            .post(&base)
            .header("X-Password", &args.password)
            .body(query)
            .send()
            .expect("request failed"),
    };

    let status = resp.status();
    let body = resp.text().expect("failed to read response");

    if !status.is_success() {
        eprintln!("Error {status}: {body}");
        std::process::exit(1);
    }

    print!("{body}");
}
