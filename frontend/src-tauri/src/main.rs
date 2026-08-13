#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::{fs, sync::Mutex};

use tauri::{Manager, RunEvent};
use tauri_plugin_shell::{process::CommandChild, ShellExt};

struct ApiSidecar(Mutex<Option<CommandChild>>);

fn main() {
    let app = tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            let app_data_dir = app.path().app_data_dir()?;
            fs::create_dir_all(&app_data_dir)?;

            let (_events, child) = app
                .shell()
                .sidecar("pathlight-api")?
                .env("PATHLIGHT_DATA_DIR", &app_data_dir)
                .env("PATHLIGHT_API_PORT", "8001")
                .spawn()?;
            app.manage(ApiSidecar(Mutex::new(Some(child))));
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building Pathlight");

    app.run(|app, event| {
        if let RunEvent::ExitRequested { .. } = event {
            if let Some(child) = app.state::<ApiSidecar>().0.lock().ok().and_then(|mut sidecar| sidecar.take()) {
                let _ = child.kill();
            }
        }
    });
}
