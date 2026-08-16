use std::process::{Command, Stdio};
use std::path::{Path, PathBuf};
use std::fs;
use serde::{Serialize, Deserialize};
use tauri::Emitter;
use anyhow::Result;

#[derive(Debug, Serialize, Deserialize)]
struct ResearchInput {
    company: String,
    website: String,
    country: String,
    city: String,
    phone: String,
    email: String,
    industry: String,
    model: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct ReportMeta {
    name: String,
    path: String,
    date: String,
}

#[tauri::command]
fn get_app_root() -> Result<String, String> {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent().unwrap_or(Path::new("."))
        .to_str().unwrap_or(".")
        .to_string();
    Ok(root)
}

#[tauri::command]
async fn list_reports() -> Result<Vec<ReportMeta>, String> {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent().unwrap_or(Path::new("."));
    let reports_dir = root.join("reports");

    if !reports_dir.exists() {
        return Ok(vec![]);
    }

    let mut reports: Vec<ReportMeta> = Vec::new();

    for entry in fs::read_dir(&reports_dir).map_err(|e| e.to_string())? {
        let entry = entry.map_err(|e| e.to_string())?;
        let path = entry.path();
        if !path.is_file() {
            continue;
        }
        let name = path.file_stem()
            .map(|s| s.to_string_lossy().to_string())
            .unwrap_or_default();
        let full_path = path.to_string_lossy().to_string();

        // Extract date from filename: {name}_调研报告_{YYYYMMDD}.md
        let metadata = entry.metadata().map_err(|e| e.to_string())?;
        let date = if let Ok(mtime) = metadata.modified() {
            if let Ok(dt) = mtime.into_std() {
                format!("{}", dt.format("%Y-%m-%d %H:%M"))
            } else {
                "unknown".to_string()
            }
        } else {
            "unknown".to_string()
        };

        reports.push(ReportMeta { name, path: full_path, date });
    }

    reports.sort_by(|a, b| b.date.cmp(&a.date));
    Ok(reports)
}

#[tauri::command]
async fn read_report(path: String) -> Result<String, String> {
    fs::read_to_string(&path).map_err(|e| e.to_string())
}

#[tauri::command]
async fn delete_report(path: String) -> Result<(), String> {
    fs::remove_file(&path).map_err(|e| e.to_string())
}

#[tauri::command]
async fn do_research(
    _app: tauri::AppHandle,
    input: ResearchInput,
) -> Result<String, String> {
    // Build the Python command
    let venv_python = "python3"; // will be resolved from PATH
    let script_path = "src/reconbot/cli.py";

    let mut cmd = Command::new(venv_python);
    cmd.arg("-m").arg("reconbot.cli")
        .arg("research")
        .arg(&input.company);

    if !input.website.is_empty() {
        cmd.arg("--website").arg(&input.website);
    }
    if !input.country.is_empty() {
        cmd.arg("--country").arg(&input.country);
    }
    if !input.city.is_empty() {
        cmd.arg("--city").arg(&input.city);
    }
    if !input.phone.is_empty() {
        cmd.arg("--phone").arg(&input.phone);
    }
    if !input.email.is_empty() {
        cmd.arg("--email").arg(&input.email);
    }
    if !input.industry.is_empty() {
        cmd.arg("--industry").arg(&input.industry);
    }
    if !input.model.is_empty() {
        cmd.arg("--model").arg(&input.model);
    }

    // Redirect stdout and stderr to a temp file for progress capture
    let output = cmd
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .map_err(|e| e.to_string())?;

    let stdout = String::from_utf8_lossy(&output.stdout).to_string();
    let stderr = String::from_utf8_lossy(&output.stderr).to_string();

    if !output.status.success() {
        return Err(format!("Research failed: {}", stderr));
    }

    Ok(stdout)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .invoke_handler(tauri::generate_handler![
            get_app_root,
            list_reports,
            read_report,
            delete_report,
            do_research,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
