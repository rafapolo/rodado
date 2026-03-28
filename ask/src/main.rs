use anyhow::{Context, Result};
use crossterm::{
    event::{
        DisableBracketedPaste, DisableMouseCapture, EnableBracketedPaste, EnableMouseCapture,
        Event, KeyCode, KeyEventKind, KeyModifiers, MouseEventKind,
    },
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use duckdb::Connection;
use ratatui::{
    buffer::Buffer,
    layout::{Constraint, Direction, Layout, Rect},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, Gauge, Paragraph, Row, Table, TableState, Wrap},
    Frame, Terminal,
};
use serde_json::{json, Value};
use std::{
    env, fs,
    io::{stdout, IsTerminal, Write},
    sync::mpsc,
    time::{Duration, Instant},
};
use syntect::easy::HighlightLines;
use syntect::highlighting::ThemeSet;
use syntect::parsing::SyntaxSet;
use syntect::util::as_24_bit_terminal_escaped;
use tui_textarea::{Input, Key, TextArea};

// ── constants ─────────────────────────────────────────────────────────────────

const SPINNER: &[&str] = &["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"];
const MAX_RETRIES: usize = 3;

// ── TUI types ─────────────────────────────────────────────────────────────────

#[derive(Clone)]
struct Config {
    model: String,
    schema: String,
    db_file: String,
    prompt_file: String,
}

enum Phase {
    Input,
    GeneratingSQL {
        started: Instant,
    },
    RunningQuery {
        sql: String,
        gen_time: Duration,
        started: Instant,
    },
    Retrying {
        sql: String,
        attempt: usize,
        gen_time: Duration,
        started: Instant,
        prev_error: String,
    },
    Done {
        sql: String,
        gen_time: Duration,
        run_time: Duration,
        cols: Vec<String>,
        rows: Vec<Vec<String>>,
        table_state: TableState,
        n_rows: usize,
    },
    Error {
        message: String,
    },
}

enum WorkerMsg {
    SqlReady(String),
    SqlError(String),
    QueryOk(Vec<String>, Vec<Vec<String>>),
    QueryError(String),
}

struct App {
    config: Config,
    phase: Phase,
    textarea: TextArea<'static>,
    history: Vec<String>,
    history_index: usize,
    tick: usize,
    rx: Option<mpsc::Receiver<WorkerMsg>>,
    current_question: String,
    last_sql: String,
    attempt: usize,
    mouse_capture: bool,
}

// ── helpers ───────────────────────────────────────────────────────────────────

fn extract_table_names(schema: &str) -> Vec<&str> {
    schema
        .lines()
        .filter(|l| !l.starts_with('#') && !l.trim().is_empty())
        .filter_map(|l| l.split(':').next())
        .map(str::trim)
        .filter(|s| !s.is_empty())
        .collect()
}

fn spinner_char(tick: usize) -> &'static str {
    SPINNER[tick % SPINNER.len()]
}

fn fmt_duration(d: Duration) -> String {
    let secs = d.as_secs();
    if secs >= 60 {
        format!("{}m {}s", secs / 60, secs % 60)
    } else {
        format!("{}.{:02}s", secs, (d.subsec_millis() / 10) % 100)
    }
}

fn fmt_timer(d: Duration) -> String {
    format!("{:02}:{:02}s", d.as_secs() / 60, d.as_secs() % 60)
}

fn wrap_text(text: &str, max_width: usize) -> Vec<String> {
    if max_width == 0 {
        return vec![text.to_string()];
    }
    let mut lines = Vec::new();
    for paragraph in text.split('\n') {
        if paragraph.is_empty() {
            lines.push(String::new());
            continue;
        }
        let mut current_line = String::new();
        for word in paragraph.split_whitespace() {
            let test_line = if current_line.is_empty() {
                word.to_string()
            } else {
                format!("{} {}", current_line, word)
            };
            if test_line.chars().count() > max_width {
                if !current_line.is_empty() {
                    lines.push(current_line.clone());
                }
                current_line = word.to_string();
            } else {
                current_line = test_line;
            }
        }
        if !current_line.is_empty() {
            lines.push(current_line);
        }
    }
    if lines.is_empty() {
        lines.push(String::new());
    }
    lines
}

fn build_textarea() -> TextArea<'static> {
    let mut ta = TextArea::default();
    ta.set_block(
        Block::default()
            .title("  Pergunta  ")
            .borders(Borders::ALL)
            .border_style(Style::default().fg(Color::Cyan)),
    );
    ta.set_placeholder_text("Digite sua pergunta em português…");
    ta
}

/// Highlight SQL with syntect, returning ratatui Lines.
fn highlight_sql_lines(sql: &str) -> Vec<Line<'static>> {
    let ps = SyntaxSet::load_defaults_newlines();
    let ts = ThemeSet::load_defaults();
    let syntax = ps
        .find_syntax_by_extension("sql")
        .unwrap_or_else(|| ps.find_syntax_plain_text());
    let mut h = HighlightLines::new(syntax, &ts.themes["base16-ocean.dark"]);
    sql.lines()
        .map(|line| {
            let ranges = h.highlight_line(line, &ps).unwrap_or_default();
            let spans: Vec<Span<'static>> = ranges
                .iter()
                .map(|(style, text)| {
                    let fg = Color::Rgb(style.foreground.r, style.foreground.g, style.foreground.b);
                    Span::styled(text.to_string(), Style::default().fg(fg))
                })
                .collect();
            Line::from(spans)
        })
        .collect()
}

// ── worker ────────────────────────────────────────────────────────────────────

fn spawn_worker(
    question: String,
    schema: String,
    model: String,
    prompt_file: String,
    db_file: String,
) -> mpsc::Receiver<WorkerMsg> {
    let (tx, rx) = mpsc::channel::<WorkerMsg>();
    std::thread::spawn(
        move || match ask_model(&question, &schema, &model, &prompt_file) {
            Err(e) => {
                tx.send(WorkerMsg::SqlError(format!("{:#}", e))).ok();
            }
            Ok(sql) => {
                tx.send(WorkerMsg::SqlReady(sql.clone())).ok();
                match run_query(&db_file, &sql) {
                    Ok((cols, rows)) => {
                        tx.send(WorkerMsg::QueryOk(cols, rows)).ok();
                    }
                    Err(e) => {
                        tx.send(WorkerMsg::QueryError(format!("{:#}", e))).ok();
                    }
                }
            }
        },
    );
    rx
}

fn spawn_retry_worker(
    question: &str,
    error: &str,
    failed_sql: &str,
    schema: String,
    model: String,
    prompt_file: String,
    db_file: String,
) -> mpsc::Receiver<WorkerMsg> {
    let retry_q = format!(
        "{}\n\nO SQL que você gerou falhou com este erro DuckDB:\n```\n{}\n```\n\n\
         SQL que falhou:\n```sql\n{}\n```\n\n\
         Corrija o SQL. Retorne APENAS o SQL corrigido, sem explicação.",
        question, error, failed_sql
    );
    spawn_worker(retry_q, schema, model, prompt_file, db_file)
}

// ── event handling ────────────────────────────────────────────────────────────

impl App {
    fn new(config: Config) -> Self {
        App {
            config,
            phase: Phase::Input,
            textarea: build_textarea(),
            history: Vec::new(),
            history_index: 0,
            tick: 0,
            rx: None,
            current_question: String::new(),
            last_sql: String::new(),
            attempt: 0,
            mouse_capture: true,
        }
    }

    fn is_loading(&self) -> bool {
        matches!(
            self.phase,
            Phase::GeneratingSQL { .. } | Phase::RunningQuery { .. } | Phase::Retrying { .. }
        )
    }

    fn submit(&mut self) {
        let q = self.textarea.lines().join(" ").trim().to_string();
        if q.is_empty() || self.is_loading() {
            return;
        }
        if !self.history.contains(&q) {
            self.history.push(q.clone());
        }
        self.history_index = self.history.len();
        self.current_question = q.clone();
        self.attempt = 0;
        self.last_sql.clear();
        self.phase = Phase::GeneratingSQL {
            started: Instant::now(),
        };
        self.rx = Some(spawn_worker(
            q,
            self.config.schema.clone(),
            self.config.model.clone(),
            self.config.prompt_file.clone(),
            self.config.db_file.clone(),
        ));
    }

    fn clear(&mut self) {
        self.phase = Phase::Input;
        self.rx = None;
        self.textarea = build_textarea();
    }

    fn handle_worker_msg(&mut self, msg: WorkerMsg) {
        match msg {
            WorkerMsg::SqlReady(sql) => {
                let gen_time = match &self.phase {
                    Phase::GeneratingSQL { started } => started.elapsed(),
                    Phase::Retrying { started, .. } => started.elapsed(),
                    _ => Duration::ZERO,
                };
                self.last_sql = sql.clone();
                self.phase = Phase::RunningQuery {
                    sql,
                    gen_time,
                    started: Instant::now(),
                };
            }
            WorkerMsg::SqlError(e) => {
                self.phase = Phase::Error {
                    message: format!("Erro ao gerar SQL:\n{}", e),
                };
            }
            WorkerMsg::QueryOk(cols, rows) => {
                let (sql, gen_time, run_time) = match &self.phase {
                    Phase::RunningQuery {
                        sql,
                        gen_time,
                        started,
                    } => (sql.clone(), *gen_time, started.elapsed()),
                    _ => (self.last_sql.clone(), Duration::ZERO, Duration::ZERO),
                };
                let n = rows.len();
                self.phase = Phase::Done {
                    sql,
                    gen_time,
                    run_time,
                    cols,
                    rows,
                    table_state: TableState::default().with_selected(Some(0)),
                    n_rows: n,
                };
            }
            WorkerMsg::QueryError(error) => {
                self.attempt += 1;
                if self.attempt <= MAX_RETRIES {
                    let gen_time = match &self.phase {
                        Phase::RunningQuery { gen_time, .. } => *gen_time,
                        _ => Duration::ZERO,
                    };
                    self.phase = Phase::Retrying {
                        sql: self.last_sql.clone(),
                        attempt: self.attempt,
                        gen_time,
                        started: Instant::now(),
                        prev_error: error.clone(),
                    };
                    self.rx = Some(spawn_retry_worker(
                        &self.current_question,
                        &error,
                        &self.last_sql,
                        self.config.schema.clone(),
                        self.config.model.clone(),
                        self.config.prompt_file.clone(),
                        self.config.db_file.clone(),
                    ));
                    self.last_sql.clear();
                } else {
                    self.phase = Phase::Error {
                        message: format!(
                            "✗ Falhou após {} tentativas.\nÚltimo erro: {}",
                            MAX_RETRIES + 1,
                            error
                        ),
                    };
                }
            }
        }
    }

    fn scroll_table(&mut self, delta: i32) {
        if let Phase::Done {
            table_state,
            n_rows,
            ..
        } = &mut self.phase
        {
            if *n_rows == 0 {
                return;
            }
            let i = table_state.selected().unwrap_or(0) as i32;
            let new_i = (i + delta).clamp(0, *n_rows as i32 - 1) as usize;
            table_state.select(Some(new_i));
        }
    }

    /// Returns true if the app should quit.
    fn handle_key(&mut self, input: Input) -> bool {
        match input {
            // Quit
            Input {
                key: Key::Char('q'),
                ..
            } if !self.is_loading() && self.textarea.is_empty() => return true,

            // Ctrl+L — clear
            Input {
                key: Key::Char('l'),
                ctrl: true,
                ..
            } => self.clear(),

            // Enter — submit
            Input {
                key: Key::Enter, ..
            } if !self.is_loading() => self.submit(),

            // ↑↓ — scroll table (Done) or history (Input)
            Input { key: Key::Up, .. } if !self.is_loading() => {
                if matches!(self.phase, Phase::Done { .. }) {
                    self.scroll_table(-1);
                } else {
                    self.navigate_history(-1);
                }
            }
            Input { key: Key::Down, .. } if !self.is_loading() => {
                if matches!(self.phase, Phase::Done { .. }) {
                    self.scroll_table(1);
                } else {
                    self.navigate_history(1);
                }
            }

            // All other keys → textarea (only when not loading)
            other if !self.is_loading() => {
                self.textarea.input(other);
            }

            _ => {}
        }
        false
    }

    fn navigate_history(&mut self, dir: i32) {
        if self.history.is_empty() {
            return;
        }
        let new_index =
            (self.history_index as i32 + dir).clamp(0, self.history.len() as i32) as usize;
        if new_index == self.history_index {
            return;
        }
        self.history_index = new_index;
        self.textarea.select_all();
        self.textarea.delete_line_by_head();
        if new_index < self.history.len() {
            self.textarea.insert_str(&self.history[new_index]);
        }
    }
}

// ── draw ──────────────────────────────────────────────────────────────────────

fn draw(f: &mut Frame, app: &mut App) {
    let area = f.area();

    // Layout: header(1) | spacer(1) | textarea(3) | content(*) | footer(1)
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(1),
            Constraint::Length(1),
            Constraint::Length(3),
            Constraint::Min(0),
            Constraint::Length(1),
        ])
        .split(area);

    // Header: model name
    let header = Paragraph::new(format!(" ◆ basedosdados ask  ─  {} ", app.config.model))
        .style(Style::default().fg(Color::Cyan));
    f.render_widget(header, chunks[0]);

    // chunks[1] is a blank spacer line

    // Textarea
    f.render_widget(&app.textarea, chunks[2]);

    // Content
    draw_content(f, app, chunks[3]);

    // Footer
    let mouse_hint = if app.mouse_capture {
        "[Ctrl+M] selecionar texto"
    } else {
        "[Ctrl+M] restaurar mouse"
    };
    let footer_text = match &app.phase {
        Phase::Input => format!("[Enter] perguntar  [↑↓] histórico  [Ctrl+L] limpar  [q] sair  {mouse_hint}"),
        Phase::Done { .. } => format!("[↑↓/scroll] rolar tabela  [Enter] nova pergunta  [Ctrl+L] limpar  [q] sair  {mouse_hint}"),
        Phase::Error { .. } => format!("[Enter] nova pergunta  [Ctrl+L] limpar  [q] sair  {mouse_hint}"),
        _ => format!("[Ctrl+C] cancelar  {mouse_hint}"),
    };
    f.render_widget(
        Paragraph::new(footer_text).style(Style::default().fg(Color::DarkGray)),
        chunks[4],
    );
}

fn draw_content(f: &mut Frame, app: &mut App, area: Rect) {
    let tick = app.tick;

    match &mut app.phase {
        Phase::Input => {
            let msg = Paragraph::new(" Digite sua pergunta e pressione Enter.")
                .style(Style::default().fg(Color::DarkGray));
            f.render_widget(msg, area);
        }

        Phase::GeneratingSQL { started } => {
            let elapsed = started.elapsed();
            let spinner_line = Line::from(vec![
                Span::styled(
                    format!("{} ", spinner_char(tick)),
                    Style::default().fg(Color::Cyan),
                ),
                Span::raw(format!("Gerando SQL…  {}", fmt_timer(elapsed))),
            ]);
            let n_tables = extract_table_names(&app.config.schema).len();
            let count_line = Line::from(Span::styled(
                format!("Gerando SQL considerando {} datasets…", n_tables),
                Style::default().fg(Color::DarkGray),
            ));
            f.render_widget(Paragraph::new(vec![spinner_line, count_line]), area);
        }

        Phase::RunningQuery {
            sql,
            gen_time,
            started,
        } => {
            let elapsed = started.elapsed();
            let gen_s = fmt_duration(*gen_time);
            let sql_lines = highlight_sql_lines(sql);
            let sql_h = (sql_lines.len() as u16 + 2).min(area.height.saturating_sub(2));

            let chunks = Layout::default()
                .direction(Direction::Vertical)
                .constraints([
                    Constraint::Length(1),
                    Constraint::Length(sql_h),
                    Constraint::Length(1),
                    Constraint::Min(0),
                ])
                .split(area);

            f.render_widget(
                Paragraph::new(format!("✓ SQL gerado em {}", gen_s))
                    .style(Style::default().fg(Color::Green)),
                chunks[0],
            );
            f.render_widget(
                Paragraph::new(sql_lines)
                    .block(Block::default().borders(Borders::ALL).title(" SQL ")),
                chunks[1],
            );
            let spinner_line = Line::from(vec![
                Span::styled(
                    format!("{} ", spinner_char(tick)),
                    Style::default().fg(Color::Cyan),
                ),
                Span::raw(format!("Executando consulta…  {}", fmt_timer(elapsed))),
            ]);
            f.render_widget(Paragraph::new(vec![spinner_line]), chunks[2]);
        }

        Phase::Retrying {
            sql,
            attempt,
            gen_time,
            started,
            prev_error,
        } => {
            let elapsed = started.elapsed();
            let gen_s = fmt_duration(*gen_time);
            let attempt = *attempt;
            let sql_lines = highlight_sql_lines(sql);
            let sql_h = (sql_lines.len() as u16 + 2).min(area.height.saturating_sub(5));
            let err_preview: String = prev_error.chars().take(120).collect();

            let chunks = Layout::default()
                .direction(Direction::Vertical)
                .constraints([
                    Constraint::Length(1),
                    Constraint::Length(sql_h),
                    Constraint::Length(2),
                    Constraint::Length(1),
                    Constraint::Length(1),
                    Constraint::Min(0),
                ])
                .split(area);

            f.render_widget(
                Paragraph::new(format!("✓ SQL gerado em {}", gen_s))
                    .style(Style::default().fg(Color::Green)),
                chunks[0],
            );
            f.render_widget(
                Paragraph::new(sql_lines)
                    .block(Block::default().borders(Borders::ALL).title(" SQL ")),
                chunks[1],
            );
            f.render_widget(
                Paragraph::new(format!("⚠ Erro DuckDB: {}", err_preview))
                    .style(Style::default().fg(Color::Red))
                    .wrap(Wrap { trim: true }),
                chunks[2],
            );
            f.render_widget(
                Gauge::default()
                    .gauge_style(Style::default().fg(Color::Yellow))
                    .ratio(attempt as f64 / MAX_RETRIES as f64)
                    .label(format!("tentativa {}/{}", attempt, MAX_RETRIES)),
                chunks[3],
            );
            let spinner_line = Line::from(vec![
                Span::styled(
                    format!("{} ", spinner_char(tick)),
                    Style::default().fg(Color::Yellow),
                ),
                Span::raw(format!("Regenerando SQL…  {}", fmt_timer(elapsed))),
            ]);
            f.render_widget(Paragraph::new(vec![spinner_line]), chunks[4]);
        }

        Phase::Done {
            sql,
            gen_time,
            run_time,
            cols,
            rows,
            table_state,
            n_rows,
        } => {
            let gen_s = fmt_duration(*gen_time);
            let run_s = fmt_duration(*run_time);
            let n = *n_rows;
            let sql_lines = highlight_sql_lines(sql);
            let sql_h = (sql_lines.len() as u16 + 2).min(area.height.saturating_sub(6));

            let chunks = Layout::default()
                .direction(Direction::Vertical)
                .constraints([
                    Constraint::Length(1),
                    Constraint::Length(sql_h),
                    Constraint::Min(5),
                ])
                .split(area);

            // Status bar
            f.render_widget(
                Paragraph::new(format!(
                    "✓ gen: {}   consulta: {}   {} linha(s)",
                    gen_s, run_s, n
                ))
                .style(Style::default().fg(Color::Green)),
                chunks[0],
            );

            // SQL box
            f.render_widget(
                Paragraph::new(sql_lines)
                    .block(Block::default().borders(Borders::ALL).title(" SQL ")),
                chunks[1],
            );

            // Results table with wrapped content
            let col_count = cols.len();
            if col_count == 0 {
                let empty = Paragraph::new("(nenhuma coluna)")
                    .style(Style::default().fg(Color::DarkGray))
                    .block(Block::default().borders(Borders::ALL).title(" Resultados "));
                f.render_widget(empty, chunks[2]);
            } else {
                let available_width = chunks[2].width.saturating_sub(col_count as u16 + 3);
                let min_col_width = 8u16;

                let col_max_widths: Vec<usize> = (0..col_count)
                    .map(|i| {
                        let header_len = cols[i].len();
                        let data_len = rows.iter().filter_map(|r| r.get(i)).map(|c| c.len()).max().unwrap_or(0);
                        (header_len.max(data_len)).max(min_col_width as usize)
                    })
                    .collect();

                let total_needed: usize = col_max_widths.iter().sum();
                let use_wrap = total_needed > available_width as usize;

                if use_wrap {
                    let wrap_width = (available_width as usize / col_count).max(min_col_width as usize);
                    let header_lines: Vec<Line> = cols.iter()
                        .enumerate()
                        .map(|(i, c)| {
                            let wrapped = wrap_text(c, wrap_width);
                            Line::from(wrapped)
                        })
                        .collect();

                    let max_header_lines = header_lines.iter().map(|l| l.len()).max().unwrap_or(1);

                    let mut all_row_lines: Vec<Vec<Line>> = Vec::new();
                    for row in rows {
                        let row_lines: Vec<Line> = (0..col_count)
                            .map(|i| {
                                let cell = row.get(i).map(|s| s.as_str()).unwrap_or("");
                                let wrapped = wrap_text(cell, wrap_width);
                                Line::from(wrapped)
                            })
                            .collect();
                        let max_lines = row_lines.iter().map(|l| l.len()).max().unwrap_or(1);
                        all_row_lines.push(row_lines);
                    }

                    let selected_idx = table_state.selected().unwrap_or(0);
                    let table_title = format!(" Resultados  ({}/{}) ", selected_idx + 1, n);

                    let block = Block::default()
                        .borders(Borders::ALL)
                        .title(table_title);

                    let area = chunks[2];
                    f.render_widget(block, area);

                    let inner_area = Rect {
                        x: area.x + 1,
                        y: area.y + 1,
                        width: area.width.saturating_sub(2),
                        height: area.height.saturating_sub(2),
                    };

                    let row_height = max_header_lines.max(1) as u16;
                    let visible_rows = inner_area.height / row_height;

                    let start_row = if n > visible_rows as usize {
                        let scroll = selected_idx as i32 - visible_rows as i32 / 2;
                        scroll.max(0) as usize.min(n.saturating_sub(visible_rows as usize))
                    } else {
                        0
                    };

                    let header_bg = Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD);
                    for (col_idx, header_line) in header_lines.iter().enumerate() {
                        let col_x = inner_area.x + (col_idx as u16) * (wrap_width as u16 + 1);
                        let col_width = wrap_width as u16;
                        for (line_idx, line) in header_line.iter().enumerate() {
                            let y = inner_area.y + line_idx as u16;
                            if y >= inner_area.y + inner_area.height {
                                break;
                            }
                            let spans: Vec<Span> = line.spans.iter().map(|s| {
                                Span::styled(s.content.clone(), header_bg)
                            }).collect();
                            f.render_widget(Paragraph::new(Line::from(spans)), Rect {
                                x: col_x,
                                y,
                                width: col_width,
                                height: 1,
                            });
                        }
                    }

                    for (row_offset, row_idx) in (start_row..n).enumerate() {
                        let y = inner_area.y + max_header_lines as u16 + row_offset as u16;
                        if y >= inner_area.y + inner_area.height {
                            break;
                        }
                        let is_selected = row_idx == selected_idx;
                        let row_style = if is_selected {
                            Style::default().bg(Color::DarkGray).add_modifier(Modifier::BOLD)
                        } else {
                            Style::default()
                        };
                        let row_lines = &all_row_lines[row_idx];

                        for (col_idx, cell_lines) in row_lines.iter().enumerate() {
                            let col_x = inner_area.x + (col_idx as u16) * (wrap_width as u16 + 1);
                            let col_width = wrap_width as u16;
                            for (line_idx, line) in cell_lines.iter().enumerate() {
                                let cell_y = y + line_idx as u16;
                                if cell_y >= inner_area.y + inner_area.height {
                                    break;
                                }
                                let spans: Vec<Span> = line.spans.iter().map(|s| {
                                    Span::styled(s.content.clone(), row_style)
                                }).collect();
                                f.render_widget(Paragraph::new(Line::from(spans)), Rect {
                                    x: col_x,
                                    y: cell_y,
                                    width: col_width,
                                    height: 1,
                                });
                            }
                        }

                        if is_selected {
                            f.render_widget(
                                Paragraph::new("▶ ").style(Style::default().fg(Color::Cyan)),
                                Rect {
                                    x: inner_area.x,
                                    y,
                                    width: 2,
                                    height: 1,
                                },
                            );
                        }
                    }
                } else {
                    let col_widths: Vec<Constraint> = cols.iter()
                        .enumerate()
                        .map(|(i, _)| {
                            let w = col_max_widths[i] as u16;
                            Constraint::Length(w)
                        })
                        .collect();

                    let header = Row::new(cols.iter().map(|c| c.as_str())).style(
                        Style::default()
                            .fg(Color::Yellow)
                            .add_modifier(Modifier::BOLD),
                    );

                    let data_rows: Vec<Row> = rows
                        .iter()
                        .map(|r| Row::new(r.iter().map(|c| c.as_str())))
                        .collect();

                    let selected_idx = table_state.selected().unwrap_or(0);
                    let table_title = format!(" Resultados  ({}/{}) ", selected_idx + 1, n);

                    let table = Table::new(data_rows, col_widths)
                        .header(header)
                        .block(Block::default().borders(Borders::ALL).title(table_title))
                        .row_highlight_style(
                            Style::default()
                                .bg(Color::DarkGray)
                                .add_modifier(Modifier::BOLD),
                        )
                        .highlight_symbol("▶ ");

                    f.render_stateful_widget(table, chunks[2], table_state);
                }
            }
        }

        Phase::Error { message } => {
            let msg = message.clone();
            f.render_widget(
                Paragraph::new(msg)
                    .style(Style::default().fg(Color::Red))
                    .block(
                        Block::default()
                            .borders(Borders::ALL)
                            .title(" Erro ")
                            .border_style(Style::default().fg(Color::Red)),
                    )
                    .wrap(Wrap { trim: true }),
                area,
            );
        }
    }
}

// ── TUI entry point ───────────────────────────────────────────────────────────

fn run_tui(config: Config) -> Result<()> {
    enable_raw_mode()?;
    let mut out = stdout();
    execute!(
        out,
        EnterAlternateScreen,
        EnableMouseCapture,
        EnableBracketedPaste
    )?;
    let backend = ratatui::backend::CrosstermBackend::new(out);
    let mut terminal = Terminal::new(backend)?;

    let mut app = App::new(config);
    let mut last_tick = Instant::now();
    let tick_rate = Duration::from_millis(80);

    let result: Result<()> = loop {
        terminal.draw(|f| draw(f, &mut app))?;

        // Check worker messages
        let msgs: Vec<WorkerMsg> = app
            .rx
            .as_ref()
            .map(|rx| rx.try_iter().collect())
            .unwrap_or_default();
        for msg in msgs {
            app.handle_worker_msg(msg);
        }

        // Poll events
        let timeout = tick_rate.saturating_sub(last_tick.elapsed());
        if crossterm::event::poll(timeout)? {
            match crossterm::event::read()? {
                Event::Key(key) if key.kind == KeyEventKind::Press => {
                    // Ctrl+C always quits
                    if key.code == KeyCode::Char('c')
                        && key.modifiers.contains(KeyModifiers::CONTROL)
                    {
                        break Ok(());
                    }
                    // Ctrl+M — toggle mouse capture (enable/disable text selection)
                    if key.code == KeyCode::Char('m')
                        && key.modifiers.contains(KeyModifiers::CONTROL)
                    {
                        app.mouse_capture = !app.mouse_capture;
                        if app.mouse_capture {
                            execute!(terminal.backend_mut(), EnableMouseCapture)?;
                        } else {
                            execute!(terminal.backend_mut(), DisableMouseCapture)?;
                        }
                        continue;
                    }
                    if app.handle_key(Input::from(key)) {
                        break Ok(());
                    }
                }
                Event::Paste(s) if !app.is_loading() => {
                    app.textarea.insert_str(&s);
                }
                Event::Mouse(mouse) => match mouse.kind {
                    MouseEventKind::ScrollUp => app.scroll_table(-1),
                    MouseEventKind::ScrollDown => app.scroll_table(1),
                    _ => {}
                },
                _ => {}
            }
        }

        if last_tick.elapsed() >= tick_rate {
            app.tick = app.tick.wrapping_add(1);
            last_tick = Instant::now();
        }
    };

    disable_raw_mode()?;
    execute!(
        terminal.backend_mut(),
        LeaveAlternateScreen,
        DisableMouseCapture,
        DisableBracketedPaste
    )?;
    terminal.show_cursor()?;
    result
}

// ── provider routing ──────────────────────────────────────────────────────────

fn ask_model(question: &str, schema: &str, model: &str, prompt_file: &str) -> Result<String> {
    let prompt_template = fs::read_to_string(prompt_file)
        .with_context(|| format!("Não foi possível ler o prompt: {}", prompt_file))?;
    let system_prompt = format!("{}\n\nSchema DDL:\n\n{}", prompt_template.trim(), schema);

    let sql = if model.contains('/') {
        ask_openrouter(question, &system_prompt, model)?
    } else {
        ask_gemini(question, &system_prompt, model)?
    };

    Ok(ensure_sql(&sql))
}

fn ask_gemini(question: &str, system_prompt: &str, model: &str) -> Result<String> {
    let key = env::var("GEMINI_API_KEY").context("GEMINI_API_KEY não definida")?;
    let url = format!(
        "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent",
        model
    );
    let payload = json!({
        "system_instruction": { "parts": [{ "text": system_prompt }] },
        "contents": [{ "parts": [{ "text": question }] }]
    });
    let client = reqwest::blocking::Client::builder()
        .timeout(Duration::from_secs(300))
        .build()?;
    let resp = client
        .post(&url)
        .header("Content-Type", "application/json")
        .header("X-goog-api-key", &key)
        .json(&payload)
        .send()
        .context("Requisição HTTP ao Gemini falhou")?;
    let status = resp.status();
    let body: Value = resp.json().context("Falha ao parsear resposta do Gemini")?;
    if !status.is_success() {
        anyhow::bail!("Gemini API error {}: {}", status, body);
    }
    let text = body["candidates"][0]["content"]["parts"][0]["text"]
        .as_str()
        .context("Formato de resposta Gemini inesperado")?
        .trim()
        .to_string();
    Ok(strip_fences(&text))
}

fn ask_openrouter(question: &str, system_prompt: &str, model: &str) -> Result<String> {
    let key = env::var("OPENROUTER_API_KEY").context("OPENROUTER_API_KEY não definida")?;
    let payload = json!({
        "model": model,
        "messages": [
            { "role": "system", "content": system_prompt },
            { "role": "user",   "content": question }
        ]
    });
    let client = reqwest::blocking::Client::builder()
        .timeout(Duration::from_secs(300))
        .build()?;
    let resp = client
        .post("https://openrouter.ai/api/v1/chat/completions")
        .header("Content-Type", "application/json")
        .header("Authorization", format!("Bearer {}", key))
        .json(&payload)
        .send()
        .context("Requisição HTTP ao OpenRouter falhou")?;
    let status = resp.status();
    let body: Value = resp
        .json()
        .context("Falha ao parsear resposta do OpenRouter")?;
    if !status.is_success() {
        anyhow::bail!("OpenRouter API error {}: {}", status, body);
    }
    let text = body["choices"][0]["message"]["content"]
        .as_str()
        .context("Formato de resposta OpenRouter inesperado")?
        .trim()
        .to_string();
    Ok(strip_fences(&text))
}

// ── SQL cleaning ──────────────────────────────────────────────────────────────

fn strip_fences(s: &str) -> String {
    let s = regex_strip_think(s.trim());
    let s = s.trim();
    let sql = if let Some(start) = s.find("```sql") {
        let after = &s[start + 6..];
        let end = after.find("```").unwrap_or(after.len());
        after[..end].trim().to_string()
    } else if let Some(start) = s.find("```") {
        let after = &s[start + 3..];
        let end = after.find("```").unwrap_or(after.len());
        after[..end].trim().to_string()
    } else {
        s.to_string()
    };
    sql.trim_end_matches(';').trim().to_string()
}

fn regex_strip_think(s: &str) -> String {
    let mut out = s.to_string();
    for tag in &["think", "thinking"] {
        let open = format!("<{}>", tag);
        let close = format!("</{}>", tag);
        while let (Some(a), Some(b)) = (out.find(&open), out.find(&close)) {
            if a < b {
                out = format!("{}\n{}", &out[..a], &out[b + close.len()..]);
            } else {
                break;
            }
        }
    }
    out
}

/// If the LLM returned prose instead of SQL, wrap it so it runs as a table.
fn ensure_sql(s: &str) -> String {
    let upper = s.trim_start().to_uppercase();
    let sql_starts = [
        "SELECT", "WITH", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER", "SHOW",
        "EXPLAIN", "DESCRIBE", "PRAGMA", "CALL", "ATTACH",
    ];
    if sql_starts.iter().any(|kw| upper.starts_with(kw)) {
        s.to_string()
    } else {
        format!("SELECT '{}' AS resposta", s.replace('\'', "''"))
    }
}

// ── DuckDB ────────────────────────────────────────────────────────────────────

fn run_query(db_file: &str, sql: &str) -> Result<(Vec<String>, Vec<Vec<String>>)> {
    let conn = Connection::open(db_file).context("Falha ao abrir DuckDB")?;
    let meta_sql = format!("SELECT * FROM ({}) __q LIMIT 0", sql);
    let mut meta = conn
        .prepare(&meta_sql)
        .context("Failed to prepare metadata query")?;
    let _ = meta.query([]).context("Failed to execute metadata query")?;
    let col_count = meta.column_count();
    let cols: Vec<String> = (0..col_count)
        .map(|i| meta.column_name(i).map_or("?", |v| v).to_string())
        .collect();
    drop(meta);

    let mut stmt = conn.prepare(sql).context("Failed to prepare SQL")?;
    let mut duckrows = stmt.query([]).context("Failed to execute SQL")?;
    let mut rows: Vec<Vec<String>> = Vec::new();
    while let Some(row) = duckrows.next()? {
        let vals: Vec<String> = (0..col_count)
            .map(|i| {
                row.get::<_, duckdb::types::Value>(i)
                    .map(|v| format_value(&v))
                    .unwrap_or_else(|_| "NULL".to_string())
            })
            .collect();
        rows.push(vals);
    }
    Ok((cols, rows))
}

fn format_value(v: &duckdb::types::Value) -> String {
    use duckdb::types::Value::*;
    match v {
        Null => "NULL".to_string(),
        Boolean(b) => b.to_string(),
        TinyInt(n) => n.to_string(),
        SmallInt(n) => n.to_string(),
        Int(n) => n.to_string(),
        BigInt(n) => n.to_string(),
        HugeInt(n) => n.to_string(),
        UTinyInt(n) => n.to_string(),
        USmallInt(n) => n.to_string(),
        UInt(n) => n.to_string(),
        UBigInt(n) => n.to_string(),
        Float(f) => f.to_string(),
        Double(f) => f.to_string(),
        Decimal(d) => d.to_string(),
        Text(s) => s.clone(),
        Blob(b) => format!("<blob {} bytes>", b.len()),
        Date32(d) => d.to_string(),
        Time64(_, t) => t.to_string(),
        Timestamp(_, t) => t.to_string(),
        Interval {
            months,
            days,
            nanos,
        } => format!("{}mo {}d {}ns", months, days, nanos),
        List(items) => {
            let inner: Vec<String> = items.iter().map(format_value).collect();
            format!("[{}]", inner.join(", "))
        }
        _ => format!("{:?}", v),
    }
}

// ── CLI helpers ───────────────────────────────────────────────────────────────

fn is_tty() -> bool {
    std::io::stderr().is_terminal()
}

fn colorize_sql(sql: &str) -> String {
    let ps = SyntaxSet::load_defaults_newlines();
    let ts = ThemeSet::load_defaults();
    let syntax = ps
        .find_syntax_by_extension("sql")
        .unwrap_or_else(|| ps.find_syntax_plain_text());
    let mut h = HighlightLines::new(syntax, &ts.themes["base16-ocean.dark"]);
    let mut out = String::new();
    for line in sql.lines() {
        let ranges = h.highlight_line(line, &ps).unwrap_or_default();
        out.push_str(&as_24_bit_terminal_escaped(&ranges, false));
        out.push('\n');
    }
    out
}

fn print_sql_box(sql: &str) {
    let sql_width = sql.lines().map(|l| l.chars().count()).max().unwrap_or(0);
    let border: String = "─".repeat(sql_width + 2);
    eprintln!("┌{}┐", border);
    if is_tty() {
        let colored = colorize_sql(sql);
        for line in colored.lines() {
            eprintln!("│ {}", line);
        }
    } else {
        for line in sql.lines() {
            let pad = sql_width - line.chars().count();
            eprintln!("│ {}{} │", line, " ".repeat(pad));
        }
    }
    eprintln!("└{}┘", border);
}

fn print_box(cols: &[String], rows: &[Vec<String>]) {
    if rows.is_empty() {
        println!("(nenhuma linha retornada)");
        return;
    }
    let mut widths: Vec<usize> = cols.iter().map(|c| c.len()).collect();
    for row in rows {
        for (i, val) in row.iter().enumerate() {
            widths[i] = widths[i].max(val.len());
        }
    }
    let bar = |l: &str, m: &str, r: &str| -> String {
        let inner: Vec<String> = widths.iter().map(|&w| "─".repeat(w + 2)).collect();
        format!("{}{}{}", l, inner.join(m), r)
    };
    let row_line = |cells: &[String]| -> String {
        let inner: Vec<String> = cells
            .iter()
            .zip(&widths)
            .map(|(v, &w)| format!(" {:w$} ", v, w = w))
            .collect();
        format!("│{}│", inner.join("│"))
    };
    println!("{}", bar("┌", "┬", "┐"));
    println!("{}", row_line(cols));
    println!("{}", bar("├", "┼", "┤"));
    for row in rows {
        println!("{}", row_line(row));
    }
    println!("{}", bar("└", "┴", "┘"));
    println!("\n{} linha(s)", rows.len());
}

// ── main ──────────────────────────────────────────────────────────────────────

fn main() -> Result<()> {
    dotenvy::dotenv().ok();

    let raw_args: Vec<String> = env::args().collect();
    let mut model_override: Option<String> = None;
    let mut rest: Vec<String> = Vec::new();
    let mut i = 1;
    while i < raw_args.len() {
        if raw_args[i] == "--model" && i + 1 < raw_args.len() {
            model_override = Some(raw_args[i + 1].clone());
            i += 2;
        } else {
            rest.push(raw_args[i].clone());
            i += 1;
        }
    }

    let wants_help = rest.iter().any(|a| a == "-h" || a == "--help");
    if wants_help {
        eprintln!(
            r#"ask — linguagem natural → SQL sobre a Base dos Dados

USO
  ask [OPÇÕES]                             # modo TUI (interativo)
  ask [OPÇÕES] "<pergunta em português>"   # modo CLI

OPÇÕES
  --model <nome>   Modelo LLM (padrão: gemini-flash-latest)
  -h, --help       Exibe esta ajuda

MODELOS
  Gemini  (GEMINI_API_KEY)
    gemini-flash-latest
    gemini-2.5-flash-preview-04-17

  OpenRouter  (OPENROUTER_API_KEY) — qualquer nome com '/'
    nvidia/nemotron-3-super-120b-a12b:free
    qwen/qwen3-coder:free

VARIÁVEIS DE AMBIENTE
  GEMINI_API_KEY       necessária para modelos Gemini
  OPENROUTER_API_KEY   necessária para modelos OpenRouter
  GEMINI_MODEL         modelo padrão (sobrescrito por --model)
  SCHEMA_FILE          DDL do schema  [context/schema_compact_inline.txt]
  PROMPT_FILE          prompt do sistema  [ask/system_prompt.md]
  DB_FILE              banco DuckDB  [basedosdados.duckdb]
"#
        );
        std::process::exit(0);
    }

    let model = model_override.unwrap_or_else(|| {
        env::var("GEMINI_MODEL").unwrap_or_else(|_| "gemini-flash-latest".into())
    });
    let schema_file =
        env::var("SCHEMA_FILE").unwrap_or_else(|_| "context/schema_compact_inline.txt".into());
    let db_file = env::var("DB_FILE").unwrap_or_else(|_| "basedosdados.duckdb".into());
    let prompt_file = env::var("PROMPT_FILE").unwrap_or_else(|_| "ask/system_prompt.md".into());
    let schema = fs::read_to_string(&schema_file)
        .with_context(|| format!("Não foi possível ler o schema: {}", schema_file))?;

    // TUI mode (no question on CLI)
    if rest.is_empty() {
        return run_tui(Config {
            model,
            schema,
            db_file,
            prompt_file,
        });
    }

    // CLI mode
    let question = rest.join(" ");
    eprintln!("\nModel:    {}\nPergunta: {}\n", model, question);

    let t0 = Instant::now();
    let sql = ask_model(&question, &schema, &model, &prompt_file)?;
    eprintln!("=> SQL gerado em {}", fmt_duration(t0.elapsed()));
    print_sql_box(&sql);

    let mut current_sql = sql;
    let mut attempt = 0;

    let (cols, rows) = loop {
        let t1 = Instant::now();
        let (tx, rx) = mpsc::channel();
        let db = db_file.clone();
        let s = current_sql.clone();
        std::thread::spawn(move || {
            tx.send(run_query(&db, &s)).ok();
        });

        let msg = if attempt == 0 {
            "executando consulta…".to_string()
        } else {
            format!("tentativa {}/{}…", attempt, MAX_RETRIES)
        };
        let mut stick = 0usize;
        let result = loop {
            if let Ok(r) = rx.try_recv() {
                break r;
            }
            eprint!("\r{} {} ", SPINNER[stick % SPINNER.len()], msg);
            stdout().flush().ok();
            stick += 1;
            std::thread::sleep(Duration::from_millis(80));
        };
        eprint!("\r                                        \r");

        match result {
            Ok((cols, rows)) => {
                eprintln!(
                    "=> SQL respondido em {} / {} linha(s)\n",
                    fmt_duration(t1.elapsed()),
                    rows.len()
                );
                break (cols, rows);
            }
            Err(e) if attempt < MAX_RETRIES => {
                attempt += 1;
                eprintln!("⚠  Erro DuckDB: {:#}", e);
                eprintln!(
                    "↻  Regenerando SQL (tentativa {}/{})…\n",
                    attempt, MAX_RETRIES
                );
                let retry_q = format!(
                    "{}\n\nO SQL que você gerou falhou com este erro DuckDB:\n```\n{:#}\n```\n\n\
                     SQL que falhou:\n```sql\n{}\n```\n\n\
                     Corrija o SQL. Retorne APENAS o SQL corrigido, sem explicação.",
                    question, e, current_sql
                );
                let tr = Instant::now();
                current_sql = ask_model(&retry_q, &schema, &model, &prompt_file)?;
                eprintln!("=> SQL regenerado em {}", fmt_duration(tr.elapsed()));
                print_sql_box(&current_sql);
            }
            Err(e) => {
                eprintln!("✗  Falhou após {} tentativas.\n  {:#}", MAX_RETRIES + 1, e);
                std::process::exit(1);
            }
        }
    };

    print_box(&cols, &rows);
    Ok(())
}
