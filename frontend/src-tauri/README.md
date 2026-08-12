# Pathlight Desktop Shell

This directory contains the minimal Tauri v2 shell for the Vue workbench.

The Python FastAPI service stays local on `127.0.0.1:8000`; the desktop shell loads the Vite workbench during development and bundled static assets in release builds. Rust/Tauri dependencies are project-local, while Cargo cache and build output are configured to live on `D:` during development.
