#!/usr/bin/env python3
"""
Script để kiểm tra xem MCP server có thể chạy được không
"""

import subprocess
import sys
import time

def check_npx_available():
    """Kiểm tra xem npx có sẵn không"""
    try:
        result = subprocess.run(["npx", "--version"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"[OK] npx co san: {result.stdout.strip()}")
            return True
        else:
            print(f"[ERROR] npx khong hoat dong: {result.stderr}")
            return False
    except Exception as e:
        print(f"[ERROR] Loi khi kiem tra npx: {e}")
        return False

def check_package_available(package_name):
    """Kiem tra xem mot npm package co the duoc npx chay khong"""
    try:
        print(f"[INFO] Dang kiem tra {package_name}...")
        # Thuc chay npx voi --yes de tu dong xac nhan
        result = subprocess.run(
            ["npx", "--yes", package_name, "--version"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print(f"[OK] {package_name} co san: {result.stdout.strip()}")
            return True
        else:
            print(f"[ERROR] {package_name} khong the chay: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"[WARN] {package_name} timeout khi kiem tra (co the dang khoi dong)")
        return False
    except Exception as e:
        print(f"[ERROR] Loi khi kiem tra {package_name}: {e}")
        return False

def main():
    print("[INFO] Kiem tra moi truong cho MCP Server...\n")

    # Kiem tra npx
    if not check_npx_available():
        print("\n[SOLUTION] Cai dat Node.js va npm")
        print("   Tai tu: https://nodejs.org/")
        return

    print()

    # Kiem tra playwright-mcp-server package
    package_ok = check_package_available("@executeautomation/playwright-mcp-server")

    print("\n" + "="*50)
    if package_ok:
        print("[OK] MCP Server dường như co san")
        print("[SOLUTION] Loi trong test_mcp.py co the do:")
        print("   - Mat ket noi mang khi khoi dong server")
        print("   - Timeout qua ngan trong cau hinh")
        print("   - Truy cap website muc dich bi chan")
    else:
        print("[ERROR] MCP Server khong the truy cap duoc")
        print("[SOLUTION]")
        print("   1. Kiem tra ket noi internet")
        print("   2. Thu cai dat thu cong: npm install -g @executeautomation/playwright-mcp-server")
        print("   3. Hoac su dung agent-browser thay the (da co san va hoat dong)")
    print("="*50)

if __name__ == "__main__":
    main()