#!/usr/bin/env python3
"""
Setup verification script for vCon Load Test Application
"""

import asyncio
import json
import sys
from pathlib import Path

import httpx
from vcon import Vcon


async def test_conserver_connection(url: str, token: str) -> bool:
    """Test connection to conserver"""
    try:
        async with httpx.AsyncClient() as client:
            # Try the /vcon endpoint without auth first
            response = await client.get(f"{url}/vcon", timeout=5.0)
            if response.status_code == 405:
                print("✅ Conserver is running (no auth required)")
                return True
            
            # Try with auth
            response = await client.get(
                f"{url}/vcon",
                headers={"x-conserver-api-token": token},
                timeout=5.0
            )
            if response.status_code == 405:
                print("✅ Conserver is running (auth working)")
                return True
            elif response.status_code == 403:
                print("⚠️  Conserver is running but token may be invalid")
                return True  # Server is up, just auth issue
            else:
                print(f"⚠️  Conserver responded with status {response.status_code}")
                return True  # Server is responding
                
    except Exception as e:
        print(f"❌ Conserver connection failed: {e}")
        return False


def test_sample_vcons(path: str) -> bool:
    """Test if sample vCons are available and valid"""
    try:
        sample_dir = Path(path)
        if not sample_dir.exists():
            print(f"❌ Sample vCon directory not found: {path}")
            return False
        
        vcon_files = list(sample_dir.glob("*.vcon"))
        if not vcon_files:
            print(f"❌ No vCon files found in {path}")
            return False
        
        # Test loading a sample vCon
        sample_file = vcon_files[0]
        try:
            vcon = Vcon.load_from_file(str(sample_file))
            # For load testing, we just need to be able to load the vCon
            # Minor validation issues are acceptable
            print(f"✅ Found {len(vcon_files)} vCon files (sample loaded successfully)")
            return True
        except Exception as e:
            print(f"❌ Error loading vCon file {sample_file}: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking sample vCons: {e}")
        return False


def test_dependencies() -> bool:
    """Test if all required dependencies are available"""
    try:
        import fastapi
        import uvicorn
        import httpx
        import click
        import rich
        import yaml
        import vcon
        print("✅ All dependencies available")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False


async def main():
    """Run all setup tests"""
    print("🔍 Testing vCon Load Test Setup...")
    print()
    
    # Test dependencies
    print("Testing dependencies...")
    deps_ok = test_dependencies()
    print()
    
    # Test sample vCons
    print("Testing sample vCons...")
    print("Note: Sample vCon files are not included in this repository.")
    print("You need to provide your own sample vCon files for testing.")
    vcons_ok = test_sample_vcons("./sample_data")
    print()
    
    # Test conserver connection
    print("Testing conserver connection...")
    conserver_ok = await test_conserver_connection("http://localhost:8000", "ZTg2ZWM3Mjg4MzdhMzQ2YWYxODExNzZkN")
    print()
    
    # Summary
    print("📊 Setup Test Summary:")
    print(f"  Dependencies: {'✅' if deps_ok else '❌'}")
    print(f"  Sample vCons: {'✅' if vcons_ok else '❌'}")
    print(f"  Conserver: {'✅' if conserver_ok else '❌'}")
    print()
    
    if deps_ok and vcons_ok and conserver_ok:
        print("🎉 All tests passed! Ready to run load tests.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
