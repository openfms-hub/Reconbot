use std::process::{Command, Stdio};
use std::path::{Path, PathBuf};
use std::fs;
use serde::{Serialize, Deserialize};

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

/// Extract YYYY-MM-DD from filename like "Company_调研报告_20260816.md"
fn extract_date(filename: &str) -> String {
    let parts: Vec<&str> = filename.split('_').collect();
    if let Some(last) = parts.last() {
        if last.len() == 8 && last.chars().all(|c| c.is_ascii_digit()) {
            return format!("{}-{}-{}", &last[0..4], &last[4..6], &last[6..8]);
        }
    }
    "unknown".to_string()
}

#[tauri::command]
fn get_app_root() -> String {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent().unwrap_or(Path::new("."))
        .to_str().unwrap_or(".")
        .to_string();
    root
}

#[tauri::command]
async fn list_reports() -> Vec<ReportMeta> {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent().unwrap_or(Path::new("."));
    let reports_dir = root.join("reports");

    if !reports_dir.exists() {
        return vec![];
    }

    let mut reports: Vec<ReportMeta> = Vec::new();

    let entries = match fs::read_dir(&reports_dir) {
        Ok(e) => e,
        Err(_) => return vec![],
    };

    for entry in entries.flatten() {
        let path = entry.path();
        if !path.is_file() {
            continue;
        }
        let filename = path.file_stem()
            .map(|s| s.to_string_lossy().to_string())
            .unwrap_or_default();
        let full_path = path.to_string_lossy().to_string();
        let date = extract_date(&filename);

        reports.push(ReportMeta { name: filename, path: full_path, date });
    }

    reports.sort_by(|a, b| b.date.cmp(&a.date));
    reports
}

#[tauri::command]
async fn read_report(path: String) -> String {
    fs::read_to_string(&path).unwrap_or_default()
}

#[tauri::command]
async fn delete_report(path: String) -> bool {
    fs::remove_file(&path).is_ok()
}

#[tauri::command]
async fn do_research(input: ResearchInput) -> String {
    let project_root = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent().unwrap_or(Path::new("."))
        .to_path_buf();

    // Try venv python first
    let venv_python = project_root.join(".venv").join("bin").join("python3");
    let python = if venv_python.exists() {
        venv_python
    } else {
        PathBuf::from("python3")
    };

    let mut cmd = Command::new(&python);
    cmd.current_dir(&project_root)
        .arg("-m").arg("reconbot.cli")
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

    match cmd.stdout(Stdio::piped()).stderr(Stdio::piped()).output() {
        Ok(output) => {
            let stdout = String::from_utf8_lossy(&output.stdout).to_string();
            let stderr = String::from_utf8_lossy(&output.stderr).to_string();
            if output.status.success() {
                stdout
            } else {
                format!("Error (exit {}): {}", output.status.code().unwrap_or(-1), stderr)
            }
        }
        Err(e) => format!("Failed to start research: {}", e),
    }
}

#[tauri::command]
fn write_file(path: String, content: String) -> bool {
    fs::write(&path, content).is_ok()
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
            write_file,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
