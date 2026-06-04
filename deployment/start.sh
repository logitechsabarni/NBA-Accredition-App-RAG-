#!/bin/bash

echo "Starting NBA Enterprise AI Platform..."

uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
