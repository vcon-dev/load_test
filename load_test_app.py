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
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
from vcon import Vcon

# Load environment variables from .env file
load_dotenv()

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
    
    # JLINC Tracer Configuration
    jlinc_enabled: bool = False
    jlinc_data_store_api_url: str = "http://jlinc-server:9090"
    jlinc_data_store_api_key: str = ""
    jlinc_archive_api_url: str = "http://jlinc-server:9090"
    jlinc_archive_api_key: str = ""
    jlinc_system_prefix: str = "VCONTest"
    jlinc_agreement_id: str = "00000000-0000-0000-0000-000000000000"
    jlinc_hash_event_data: bool = True
    jlinc_dlq_vcon_on_error: bool = True


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
        self.config_backup_path: Optional[str] = None
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
    
    async def backup_existing_config(self) -> Optional[str]:
        """Backup existing conserver configuration to a temporary file"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.config.conserver_url}/config",
                    headers={"x-conserver-api-token": self.config.conserver_token}
                )
                
                if response.status_code == 200:
                    existing_config = response.json()
                    
                    # Save to temporary file
                    backup_path = Path(self.config.test_directory) / f"conserver_config_backup_{int(time.time())}.yml"
                    backup_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    with open(backup_path, 'w') as f:
                        yaml.dump(existing_config, f, default_flow_style=False)
                    
                    logger.info(f"Backed up existing configuration to: {backup_path}")
                    return str(backup_path)
                else:
                    logger.warning(f"Could not retrieve existing configuration: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.warning(f"Error backing up existing configuration: {e}")
            return None
    
    async def restore_config(self, backup_path: str) -> bool:
        """Restore conserver configuration from backup file"""
        try:
            if not Path(backup_path).exists():
                logger.error(f"Backup file not found: {backup_path}")
                return False
            
            # Load backup configuration
            with open(backup_path, 'r') as f:
                backup_config = yaml.safe_load(f)
            
            # Restore configuration
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.config.conserver_url}/config",
                    json=backup_config,
                    headers={"x-conserver-api-token": self.config.conserver_token}
                )
                
                if response.status_code in [200, 204]:
                    logger.info("Successfully restored original configuration")
                    return True
                else:
                    logger.error(f"Failed to restore configuration: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error restoring configuration: {e}")
            return False

    async def setup_conserver_config(self) -> bool:
        """Setup conserver configuration with ingress list and webhook"""
        try:
            # Ensure test directory exists
            test_dir = Path(self.config.test_directory)
            test_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Test directory: {test_dir.resolve()}")
            
            # Backup existing configuration
            backup_path = await self.backup_existing_config()
            if backup_path:
                # Store backup path for later restoration
                self.config_backup_path = backup_path
            
            # Clear existing vCon files from conserver storage
            conserver_test_dir = Path("/root/vcon-server/test_results")
            if conserver_test_dir.exists():
                vcon_files = list(conserver_test_dir.glob("*.json"))
                for file in vcon_files:
                    file.unlink()
                logger.info(f"Cleared {len(vcon_files)} existing vCon files")
            
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
            
            # Add JLINC tracer if enabled
            if self.config.jlinc_enabled:
                config["tracers"] = {
                    "jlinc": {
                        "module": "tracers.jlinc",
                        "options": {
                            "data_store_api_url": self.config.jlinc_data_store_api_url,
                            "data_store_api_key": self.config.jlinc_data_store_api_key,
                            "archive_api_url": self.config.jlinc_archive_api_url,
                            "archive_api_key": self.config.jlinc_archive_api_key,
                            "system_prefix": self.config.jlinc_system_prefix,
                            "agreement_id": self.config.jlinc_agreement_id,
                            "hash_event_data": self.config.jlinc_hash_event_data,
                            "dlq_vcon_on_error": self.config.jlinc_dlq_vcon_on_error
                        }
                    }
                }
                # Add JLINC tracer to the chain
                config["chains"]["load_test_chain"]["tracers"] = ["jlinc"]
            
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
    
    async def send_vcon(self, test_id: str) -> Tuple[bool, float, str]:
        """Send a random vCon to conserver and add to ingress list for processing"""
        start_time = time.time()
        
        try:
            # Load a random sample vCon for this request
            vcon = self.load_sample_vcon()
            if not vcon:
                end_time = time.time()
                response_time = end_time - start_time
                logger.error("Failed to load sample vCon")
                return False, response_time, "Failed to load sample vCon"
            
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
        
        # No need to load sample vCon here - we'll load a random one for each request
        
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
                success, response_time, response_text = await self.send_vcon(f"{test_id}_{i}")
                
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
    
    async def cleanup(self, restore_original_config: bool = True) -> bool:
        """Clean up after test completion"""
        try:
            if restore_original_config and self.config_backup_path:
                logger.info("Restoring original conserver configuration...")
                success = await self.restore_config(self.config_backup_path)
                if success:
                    logger.info("Original configuration restored successfully")
                else:
                    logger.error("Failed to restore original configuration")
                return success
            else:
                logger.info("Skipping configuration restoration")
                return True
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return False
    
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
@click.option("--conserver-url", default=lambda: os.getenv("CONSERVER_URL", "http://localhost:8000"), help="vCon Server URL")
@click.option("--conserver-token", default=lambda: os.getenv("CONSERVER_TOKEN", "test-token"), help="vCon Server API token")
@click.option("--test-directory", default="./test_results", help="Directory to save test results")
@click.option("--webhook-port", default=8080, help="Port for webhook server")
@click.option("--rate", default=10, help="Requests per second")
@click.option("--amount", default=100, help="Total number of requests")
@click.option("--duration", default=60, help="Test duration in seconds")
@click.option("--sample-vcon-path", default="./sample_vcons", help="Path to sample vCon files")
@click.option("--jlinc-enabled", is_flag=True, default=lambda: os.getenv("JLINC_ENABLED", "false").lower() == "true", help="Enable JLINC tracer")
@click.option("--jlinc-data-store-api-url", default=lambda: os.getenv("JLINC_DATA_STORE_API_URL", "http://jlinc-server:9090"), help="JLINC data store API URL")
@click.option("--jlinc-data-store-api-key", default=lambda: os.getenv("JLINC_DATA_STORE_API_KEY", ""), help="JLINC data store API key")
@click.option("--jlinc-archive-api-url", default=lambda: os.getenv("JLINC_ARCHIVE_API_URL", "http://jlinc-server:9090"), help="JLINC archive API URL")
@click.option("--jlinc-archive-api-key", default=lambda: os.getenv("JLINC_ARCHIVE_API_KEY", ""), help="JLINC archive API key")
@click.option("--jlinc-system-prefix", default=lambda: os.getenv("JLINC_SYSTEM_PREFIX", "VCONTest"), help="JLINC system prefix")
@click.option("--jlinc-agreement-id", default=lambda: os.getenv("JLINC_AGREEMENT_ID", "00000000-0000-0000-0000-000000000000"), help="JLINC agreement ID")
@click.option("--jlinc-hash-event-data/--no-jlinc-hash-event-data", default=lambda: os.getenv("JLINC_HASH_EVENT_DATA", "true").lower() == "true", help="Hash event data in JLINC")
@click.option("--jlinc-dlq-vcon-on-error/--no-jlinc-dlq-vcon-on-error", default=lambda: os.getenv("JLINC_DLQ_VCON_ON_ERROR", "true").lower() == "true", help="Send vCon to DLQ on error in JLINC")
@click.option("--restore-config/--no-restore-config", default=True, help="Restore original conserver configuration after test")
def main(
    conserver_url: str,
    conserver_token: str,
    test_directory: str,
    webhook_port: int,
    rate: int,
    amount: int,
    duration: int,
    sample_vcon_path: str,
    jlinc_enabled: bool,
    jlinc_data_store_api_url: str,
    jlinc_data_store_api_key: str,
    jlinc_archive_api_url: str,
    jlinc_archive_api_key: str,
    jlinc_system_prefix: str,
    jlinc_agreement_id: str,
    jlinc_hash_event_data: bool,
    jlinc_dlq_vcon_on_error: bool,
    restore_config: bool
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
        sample_vcon_path=sample_vcon_path,
        jlinc_enabled=jlinc_enabled,
        jlinc_data_store_api_url=jlinc_data_store_api_url,
        jlinc_data_store_api_key=jlinc_data_store_api_key,
        jlinc_archive_api_url=jlinc_archive_api_url,
        jlinc_archive_api_key=jlinc_archive_api_key,
        jlinc_system_prefix=jlinc_system_prefix,
        jlinc_agreement_id=jlinc_agreement_id,
        jlinc_hash_event_data=jlinc_hash_event_data,
        jlinc_dlq_vcon_on_error=jlinc_dlq_vcon_on_error
    )
    
    console.print(f"[bold blue]vCon Server Load Test[/bold blue]")
    console.print(f"ConServer URL: {config.conserver_url}")
    console.print(f"Rate: {config.rate} req/s")
    console.print(f"Amount: {config.amount} requests")
    console.print(f"Duration: {config.duration}s")
    console.print(f"JLINC Tracer: {'Enabled' if config.jlinc_enabled else 'Disabled'}")
    if config.jlinc_enabled:
        console.print(f"  - Data Store API: {config.jlinc_data_store_api_url}")
        console.print(f"  - Archive API: {config.jlinc_archive_api_url}")
        console.print(f"  - System Prefix: {config.jlinc_system_prefix}")
    console.print()
    
    async def run_test():
        tester = None
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
        finally:
            # Always attempt cleanup
            if tester:
                console.print("\n[blue]Cleaning up...[/blue]")
                cleanup_success = await tester.cleanup(restore_config)
                if cleanup_success:
                    console.print("[green]Cleanup completed successfully[/green]")
                else:
                    console.print("[yellow]Cleanup completed with warnings[/yellow]")
    
    asyncio.run(run_test())


if __name__ == "__main__":
    main()
