#!/usr/bin/env python
import os
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5432/flashorder"

import uvicorn
uvicorn.run("app.main:app", host="0.0.0.0", port=8002, reload=False)
