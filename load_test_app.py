#!/usr/bin/env python3
"""
vCon Server Load Test Application

A comprehensive load testing tool for the vCon Server that:
1. Sets up a configuration with an ingress list that adds random tags to vCons
2. Saves processed vCons to a test directory
3. Webhooks results back to the test framework
4. Validates processing results and measures performance
"""

import asyncio
import json
import logging
import os
import random
import string
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

import click
import httpx
import yaml
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
from vcon import Vcon

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

console = Console()


class TestConfig(BaseModel):
    """Configuration for load testing"""
    conserver_url: str = "http://localhost:8000"
    conserver_token: str = "test-token"
    test_directory: str = "./test_results"
    webhook_port: int = 8080
    rate: int = 10  # requests per second
    amount: int = 100  # total requests
    duration: int = 60  # test duration in seconds
    sample_vcon_path: str = "./sample_vcons"


class WebhookData(BaseModel):
    """Data received from webhook"""
    vcon_id: str
    timestamp: str
    processing_time: float
    tags: Dict[str, str]
    file_saved: bool


class LoadTester:
    """Main load testing class"""
    
    def __init__(self, config: TestConfig):
        self.config = config
        self.webhook_data: List[WebhookData] = []
        self.test_results: List[Dict[str, Any]] = []
        self.app = FastAPI(title="vCon Load Test Webhook Server")
        self.setup_webhook_routes()
        
    def setup_webhook_routes(self):
        """Setup FastAPI routes for webhook server"""
        
        @self.app.post("/webhook")
        async def webhook_endpoint(request: Request):
            """Receive webhook data from conserver"""
            try:
                logger.info("Webhook endpoint called!")
                data = await request.json()
                logger.info(f"Webhook data received: {data}")
                webhook_data = WebhookData(**data)
                self.webhook_data.append(webhook_data)
                logger.info(f"Received webhook for vCon {webhook_data.vcon_id}")
                return {"status": "received"}
            except Exception as e:
                logger.error(f"Error processing webhook: {e}")
                raise HTTPException(status_code=400, detail=str(e))
    
    async def setup_conserver_config(self) -> bool:
        """Setup conserver configuration with ingress list and webhook"""
        try:
            # Ensure test directory exists
            test_dir = Path(self.config.test_directory)
            test_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Test directory: {test_dir.resolve()}")
            
            # Create test configuration
            config = {
                "links": {
                    "random_tag": {
                        "module": "links.tag",
                        "ingress-lists": ["load_test_list"],
                        "egress-lists": [],
                        "options": {
                            "tags": {
                                "load_test": "true",
                                "test_id": self.generate_test_id(),
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            }
                        }
                    },
                    "webhook": {
                        "module": "links.webhook",
                        "options": {
                            "webhook-urls": [f"http://webhook-server:{self.config.webhook_port}/webhook"]
                        }
                    }
                },
                "storages": {
                    "file_storage": {
                        "module": "storage.file",
                        "options": {
                            "path": "/app/test_results",
                            "add_timestamp_to_filename": True,
                            "filename": "vcon",
                            "extension": "json"
                        }
                    }
                },
                "chains": {
                    "load_test_chain": {
                        "links": ["random_tag", "webhook"],
                        "ingress_lists": ["load_test_list"],
                        "storages": ["file_storage"],
                        "enabled": 1
                    }
                }
            }
            
            # Save configuration
            config_path = Path(self.config.test_directory) / "load_test_config.yml"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            # Post configuration to conserver
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.config.conserver_url}/config",
                    json=config,
                    headers={"x-conserver-api-token": self.config.conserver_token}
                )
                
                if response.status_code in [200, 204]:
                    logger.info("Successfully configured conserver")
                    return True
                else:
                    logger.error(f"Failed to configure conserver: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error setting up conserver config: {e}")
            return False
    
    def generate_test_id(self) -> str:
        """Generate a unique test ID"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    
    def load_sample_vcon(self) -> Optional[Vcon]:
        """Load a random sample vCon"""
        try:
            sample_dir = Path(self.config.sample_vcon_path)
            if not sample_dir.exists():
                logger.error(f"Sample vCon directory not found: {sample_dir}")
                return None
            
            vcon_files = list(sample_dir.glob("*.vcon"))
            if not vcon_files:
                logger.error("No sample vCon files found")
                return None
            
            # Select random vCon file
            selected_file = random.choice(vcon_files)
            logger.info(f"Loading sample vCon: {selected_file.name}")
            
            return Vcon.load_from_file(str(selected_file))
            
        except Exception as e:
            logger.error(f"Error loading sample vCon: {e}")
            return None
    
    async def send_vcon(self, vcon: Vcon, test_id: str) -> Tuple[bool, float, str]:
        """Send vCon to conserver and add to ingress list for processing"""
        start_time = time.time()
        
        try:
            # Add test metadata to vCon
            vcon.add_tag("load_test_id", test_id)
            vcon.add_tag("test_timestamp", datetime.now(timezone.utc).isoformat())
            
            async with httpx.AsyncClient() as client:
                # First, create the vCon
                response = await client.post(
                    f"{self.config.conserver_url}/vcon",
                    json=vcon.to_dict(),
                    headers={"x-conserver-api-token": self.config.conserver_token}
                )
                
                if response.status_code not in [200, 201]:
                    end_time = time.time()
                    response_time = end_time - start_time
                    logger.error(f"Failed to create vCon: {response.status_code} - {response.text}")
                    return False, response_time, response.text
                
                # Extract vCon UUID from response
                vcon_response = response.json()
                vcon_uuid = vcon_response.get("uuid")
                
                if not vcon_uuid:
                    end_time = time.time()
                    response_time = end_time - start_time
                    logger.error("No UUID returned from vCon creation")
                    return False, response_time, "No UUID returned"
                
                # Now add the vCon to the ingress list for processing
                ingress_response = await client.post(
                    f"{self.config.conserver_url}/vcon/ingress",
                    json=[vcon_uuid],
                    params={"ingress_list": "load_test_list"},
                    headers={"x-conserver-api-token": self.config.conserver_token}
                )
                
                end_time = time.time()
                response_time = end_time - start_time
                
                if ingress_response.status_code in [200, 201, 204]:
                    logger.info(f"Successfully added vCon {vcon_uuid} to ingress list")
                    return True, response_time, f"vCon {vcon_uuid} created and added to ingress list"
                else:
                    logger.error(f"Failed to add vCon to ingress list: {ingress_response.status_code} - {ingress_response.text}")
                    return False, response_time, f"Created vCon but failed to add to ingress: {ingress_response.text}"
                    
        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            logger.error(f"Error sending vCon: {e}")
            return False, response_time, str(e)
    
    async def run_load_test(self) -> Dict[str, Any]:
        """Run the load test"""
        logger.info("Starting load test...")
        
        # Setup conserver configuration
        if not await self.setup_conserver_config():
            raise Exception("Failed to setup conserver configuration")
        
        # Load sample vCon
        sample_vcon = self.load_sample_vcon()
        if not sample_vcon:
            raise Exception("Failed to load sample vCon")
        
        # No need to start webhook server - we have a dedicated one running in Docker
        
        # Wait a moment for server to start
        await asyncio.sleep(1)
        
        test_results = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_time": 0,
            "response_times": [],
            "webhook_received": 0,
            "files_saved": 0,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "end_time": None
        }
        
        start_time = time.time()
        test_id = self.generate_test_id()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Running load test...", total=self.config.amount)
            
            for i in range(self.config.amount):
                # Rate limiting
                if i > 0:
                    await asyncio.sleep(1.0 / self.config.rate)
                
                # Send vCon
                success, response_time, response_text = await self.send_vcon(sample_vcon, f"{test_id}_{i}")
                
                test_results["total_requests"] += 1
                test_results["response_times"].append(response_time)
                
                if success:
                    test_results["successful_requests"] += 1
                else:
                    test_results["failed_requests"] += 1
                
                progress.update(task, advance=1)
                
                # Check if we've exceeded duration
                if time.time() - start_time > self.config.duration:
                    logger.info(f"Test duration exceeded, stopping at request {i+1}")
                    break
        
        test_results["end_time"] = datetime.now(timezone.utc).isoformat()
        test_results["total_time"] = time.time() - start_time
        
        # Wait for webhooks to arrive (conserver processes immediately)
        logger.info("Waiting for webhooks to arrive (conserver processes immediately)...")
        for i in range(10):  # Wait up to 10 seconds since processing is immediate
            await asyncio.sleep(1)
            # Check webhook server for received data
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"http://localhost:8080/webhooks")
                    if response.status_code == 200:
                        webhook_response = response.json()
                        webhook_count = webhook_response.get("count", 0)
                        if webhook_count > 0:
                            logger.info(f"Webhooks received after {i+1} seconds!")
                            self.webhook_data = webhook_response.get("webhooks", [])
                            break
            except Exception as e:
                logger.debug(f"Error checking webhooks: {e}")
            if i % 2 == 0:  # Log every 2 seconds
                logger.info(f"Still waiting for webhooks... ({i+1}s elapsed)")
        
        logger.info(f"Webhook server received {len(self.webhook_data)} webhooks total")
        
        # Count webhook data
        test_results["webhook_received"] = len(self.webhook_data)
        
        # Check saved files (conserver saves to /app/test_results which is mounted at /root/vcon-server/test_results)
        conserver_test_dir = Path("/root/vcon-server/test_results")
        if conserver_test_dir.exists():
            # Count .json files (conserver saves with .json extension)
            vcon_files = list(conserver_test_dir.glob("*.json"))
            test_results["files_saved"] = len(vcon_files)
        else:
            test_results["files_saved"] = 0
        
        return test_results
    
    def validate_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Validate test results"""
        validation = {
            "success_rate": 0,
            "avg_response_time": 0,
            "webhook_delivery_rate": 0,
            "file_save_rate": 0,
            "overall_success": False
        }
        
        if results["total_requests"] > 0:
            validation["success_rate"] = results["successful_requests"] / results["total_requests"]
            validation["avg_response_time"] = sum(results["response_times"]) / len(results["response_times"])
        
        if results["successful_requests"] > 0:
            validation["webhook_delivery_rate"] = results["webhook_received"] / results["successful_requests"]
            validation["file_save_rate"] = results["files_saved"] / results["successful_requests"]
        
        # Overall success if >90% success rate and webhooks delivered
        validation["overall_success"] = (
            validation["success_rate"] > 0.9 and
            validation["webhook_delivery_rate"] > 0.8
        )
        
        return validation
    
    def print_results(self, results: Dict[str, Any], validation: Dict[str, Any]):
        """Print test results in a nice format"""
        table = Table(title="Load Test Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Requests", str(results["total_requests"]))
        table.add_row("Successful Requests", str(results["successful_requests"]))
        table.add_row("Failed Requests", str(results["failed_requests"]))
        table.add_row("Success Rate", f"{validation['success_rate']:.2%}")
        table.add_row("Average Response Time", f"{validation['avg_response_time']:.3f}s")
        table.add_row("Webhooks Received", str(results["webhook_received"]))
        table.add_row("Webhook Delivery Rate", f"{validation['webhook_delivery_rate']:.2%}")
        table.add_row("Files Saved", str(results["files_saved"]))
        table.add_row("File Save Rate", f"{validation['file_save_rate']:.2%}")
        table.add_row("Total Test Time", f"{results['total_time']:.2f}s")
        table.add_row("Overall Success", "✅" if validation["overall_success"] else "❌")
        
        console.print(table)


@click.command()
@click.option("--conserver-url", default="http://localhost:8000", help="vCon Server URL")
@click.option("--conserver-token", default="test-token", help="vCon Server API token")
@click.option("--test-directory", default="./test_results", help="Directory to save test results")
@click.option("--webhook-port", default=8080, help="Port for webhook server")
@click.option("--rate", default=10, help="Requests per second")
@click.option("--amount", default=100, help="Total number of requests")
@click.option("--duration", default=60, help="Test duration in seconds")
@click.option("--sample-vcon-path", default="./sample_vcons", help="Path to sample vCon files")
def main(
    conserver_url: str,
    conserver_token: str,
    test_directory: str,
    webhook_port: int,
    rate: int,
    amount: int,
    duration: int,
    sample_vcon_path: str
):
    """vCon Server Load Test Application"""
    
    config = TestConfig(
        conserver_url=conserver_url,
        conserver_token=conserver_token,
        test_directory=test_directory,
        webhook_port=webhook_port,
        rate=rate,
        amount=amount,
        duration=duration,
        sample_vcon_path=sample_vcon_path
    )
    
    console.print(f"[bold blue]vCon Server Load Test[/bold blue]")
    console.print(f"ConServer URL: {config.conserver_url}")
    console.print(f"Rate: {config.rate} req/s")
    console.print(f"Amount: {config.amount} requests")
    console.print(f"Duration: {config.duration}s")
    console.print()
    
    async def run_test():
        try:
            tester = LoadTester(config)
            results = await tester.run_load_test()
            validation = tester.validate_results(results)
            
            console.print()
            tester.print_results(results, validation)
            
            # Save results to file
            results_file = Path(config.test_directory) / f"test_results_{int(time.time())}.json"
            results_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(results_file, 'w') as f:
                json.dump({
                    "config": config.model_dump(),
                    "results": results,
                    "validation": validation
                }, f, indent=2)
            
            console.print(f"\n[green]Results saved to: {results_file}[/green]")
            
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            logger.exception("Load test failed")
    
    asyncio.run(run_test())


if __name__ == "__main__":
    main()
