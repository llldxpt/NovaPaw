# -*- coding: utf-8 -*-
"""Tauri sidecar environment variable helpers.

Keep this dependency-light: the Tauri entry imports it before novapaw.constant
has read import-time environment variables.
"""

import os

DESKTOP_APP_ENV = "NOVAPAW_DESKTOP_APP"
DESKTOP_CORS_ORIGINS_ENV = "NOVAPAW_CORS_ORIGINS"
DESKTOP_SHUTDOWN_TOKEN_ENV = "NOVAPAW_DESKTOP_SHUTDOWN_TOKEN"
DESKTOP_MANAGED_PLAYWRIGHT_ENV = "NOVAPAW_DESKTOP_MANAGED_PLAYWRIGHT"
DESKTOP_READY_PREFIX = "NOVAPAW_BACKEND_READY"

DESKTOP_CORS_ORIGINS = (
    "tauri://localhost",
    "https://tauri.localhost",
    "http://tauri.localhost",
)


def ensure_desktop_cors_origins() -> None:
    origins = [
        origin.strip()
        for origin in os.environ.get(DESKTOP_CORS_ORIGINS_ENV, "").split(",")
        if origin.strip()
    ]
    for origin in DESKTOP_CORS_ORIGINS:
        if origin not in origins:
            origins.append(origin)
    os.environ[DESKTOP_CORS_ORIGINS_ENV] = ",".join(origins)
