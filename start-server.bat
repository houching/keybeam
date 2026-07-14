@echo off
title KeyBeam Barcode Bridge Server
echo Starting KeyBeam Server...
cd server
uv run app.py --interactive
pause
