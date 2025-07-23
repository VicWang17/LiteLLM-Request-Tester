#!/usr/bin/env python3
import uvicorn
from app import app

if __name__ == "__main__":
    print("启动 Request Tester 服务...")
    uvicorn.run(app, host="0.0.0.0", port=8002, reload=False)