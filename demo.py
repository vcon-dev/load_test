#!/usr/bin/env python3
"""
Demo script for vCon Load Test Application

This script demonstrates the load testing functionality with a simple example.
"""

import asyncio
import json
import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def show_demo_info():
    """Display demo information"""
    console.print(Panel.fit(
        "[bold blue]vCon Server Load Test Application Demo[/bold blue]\n\n"
        "This application tests the complete vCon processing pipeline:\n"
        "1. 📝 Sets up conserver configuration with tagging and webhooks\n"
        "2. 🚀 Sends vCons at specified rate to test performance\n"
        "3. 📊 Validates processing, file saving, and webhook delivery\n"
        "4. 📈 Provides comprehensive performance metrics",
        title="Demo Overview"
    ))


def show_usage_examples():
    """Show usage examples"""
    table = Table(title="Usage Examples")
    table.add_column("Command", style="cyan")
    table.add_column("Description", style="green")
    
    table.add_row(
        "uv run load_test_app.py",
        "Run with default settings (10 req/s, 100 requests, 60s)"
    )
    table.add_row(
        "uv run load_test_app.py --rate 20 --amount 200",
        "High load test: 20 requests/second, 200 total requests"
    )
    table.add_row(
        "uv run load_test_app.py --rate 5 --amount 10 --duration 30",
        "Quick test: 5 req/s, 10 requests, 30 seconds max"
    )
    table.add_row(
        "uv run load_test_app.py --conserver-url http://localhost:8000",
        "Custom conserver URL"
    )
    
    console.print(table)


def show_configuration_options():
    """Show configuration options"""
    table = Table(title="Configuration Options")
    table.add_column("Option", style="cyan")
    table.add_column("Default", style="yellow")
    table.add_column("Description", style="green")
    
    table.add_row("--conserver-url", "http://localhost:8000", "vCon Server URL")
    table.add_row("--conserver-token", "test-token", "API authentication token")
    table.add_row("--test-directory", "./test_output", "Directory for test results")
    table.add_row("--webhook-port", "8080", "Port for webhook server")
    table.add_row("--rate", "10", "Requests per second")
    table.add_row("--amount", "100", "Total number of requests")
    table.add_row("--duration", "60", "Test duration in seconds")
    table.add_row("--sample-vcon-path", "./sample_data", "Path to sample vCon files")
    
    console.print(table)


def show_test_flow():
    """Show the test flow diagram"""
    flow_text = """
    [bold]Test Flow:[/bold]
    
    1. [cyan]Setup Phase[/cyan]
       ├── Create conserver configuration
       ├── Setup ingress list with tagging
       ├── Configure file storage
       └── Setup webhook endpoint
    
    2. [cyan]Load Testing Phase[/cyan]
       ├── Load random sample vCon
       ├── Send vCons at specified rate
       ├── Measure response times
       └── Track success/failure rates
    
    3. [cyan]Validation Phase[/cyan]
       ├── Verify webhook deliveries
       ├── Check file saves
       ├── Validate processing results
       └── Calculate performance metrics
    
    4. [cyan]Reporting Phase[/cyan]
       ├── Display results table
       ├── Save JSON report
       └── Show success/failure status
    """
    
    console.print(Panel(flow_text, title="Test Flow", border_style="blue"))


def show_sample_results():
    """Show sample test results"""
    sample_results = {
        "total_requests": 100,
        "successful_requests": 98,
        "failed_requests": 2,
        "success_rate": 0.98,
        "avg_response_time": 0.245,
        "webhook_received": 95,
        "webhook_delivery_rate": 0.97,
        "files_saved": 96,
        "file_save_rate": 0.98,
        "total_test_time": 12.5,
        "overall_success": True
    }
    
    table = Table(title="Sample Test Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Total Requests", str(sample_results["total_requests"]))
    table.add_row("Successful Requests", str(sample_results["successful_requests"]))
    table.add_row("Failed Requests", str(sample_results["failed_requests"]))
    table.add_row("Success Rate", f"{sample_results['success_rate']:.2%}")
    table.add_row("Average Response Time", f"{sample_results['avg_response_time']:.3f}s")
    table.add_row("Webhooks Received", str(sample_results["webhook_received"]))
    table.add_row("Webhook Delivery Rate", f"{sample_results['webhook_delivery_rate']:.2%}")
    table.add_row("Files Saved", str(sample_results["files_saved"]))
    table.add_row("File Save Rate", f"{sample_results['file_save_rate']:.2%}")
    table.add_row("Total Test Time", f"{sample_results['total_test_time']:.2f}s")
    table.add_row("Overall Success", "✅" if sample_results["overall_success"] else "❌")
    
    console.print(table)


def main():
    """Main demo function"""
    console.clear()
    
    show_demo_info()
    console.print()
    
    show_usage_examples()
    console.print()
    
    show_configuration_options()
    console.print()
    
    show_test_flow()
    console.print()
    
    show_sample_results()
    console.print()
    
    console.print(Panel.fit(
        "[bold green]Ready to run load tests![/bold green]\n\n"
        "Run: [cyan]uv run load_test_app.py --help[/cyan] for more options\n"
        "Or: [cyan]uv run load_test_app.py[/cyan] to start a test",
        title="Next Steps"
    ))


if __name__ == "__main__":
    main()
