"""
CLI interface for testing OpenMesh
"""
import click
import requests
import json
import time
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


BASE_URL = "http://localhost:8000/api/v1"


@click.group()
def cli():
    """OpenMesh CLI - Decentralized GPU Mesh"""
    pass


@cli.command()
@click.option("--node-id", required=True, help="Node ID")
@click.option("--host", default="localhost", help="Node host")
@click.option("--port", default=8080, type=int, help="Node port")
@click.option("--gpu-memory", default=24, type=int, help="GPU memory in GB")
@click.option("--compute-score", default=8.5, type=float, help="Compute score")
def register_node(node_id: str, host: str, port: int, gpu_memory: int, compute_score: float):
    """Register a node"""
    try:
        response = requests.post(
            f"{BASE_URL}/nodes/register",
            json={
                "node_id": node_id,
                "host": host,
                "port": port,
                "gpu_memory": gpu_memory,
                "compute_score": compute_score
            }
        )
        response.raise_for_status()
        node = response.json()
        console.print(Panel(f"[green]Node registered successfully![/green]\n"
                          f"Node ID: {node['node_id']}\n"
                          f"Status: {node['status']}\n"
                          f"Reputation: {node['reputation']}"))
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
def list_nodes():
    """List all active nodes"""
    try:
        response = requests.get(f"{BASE_URL}/nodes")
        response.raise_for_status()
        nodes = response.json()
        
        if not nodes:
            console.print("[yellow]No active nodes found[/yellow]")
            return
        
        table = Table(title="Active Nodes")
        table.add_column("Node ID")
        table.add_column("Host:Port")
        table.add_column("GPU Memory")
        table.add_column("Compute Score")
        table.add_column("Reputation")
        table.add_column("Status")
        
        for node in nodes:
            table.add_row(
                node["node_id"],
                f"{node['host']}:{node['port']}",
                f"{node['gpu_memory']} GB",
                f"{node['compute_score']:.2f}",
                f"{node['reputation']:.2f}",
                node["status"]
            )
        
        console.print(table)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.option("--model", required=True, help="Model name (e.g., llama-3-8b)")
@click.option("--dataset", help="Dataset path or name")
@click.option("--max-budget", type=float, help="Maximum budget in USD")
@click.option("--speed", type=click.Choice(["fast", "balanced", "cheap"]), default="balanced", help="Speed preference")
@click.option("--user-id", default="cli_user", help="User ID")
def finetune(model: str, dataset: Optional[str], max_budget: Optional[float], speed: str, user_id: str):
    """Create a finetuning job"""
    try:
        payload = {
            "model": model,
            "speed": speed,
            "user_id": user_id
        }
        
        if dataset:
            payload["dataset"] = dataset
        if max_budget:
            payload["max_budget"] = max_budget
        
        console.print(f"[cyan]Creating finetuning job...[/cyan]")
        response = requests.post(f"{BASE_URL}/finetune", json=payload)
        response.raise_for_status()
        job = response.json()
        
        console.print(Panel(
            f"[green]Job created successfully![/green]\n\n"
            f"Job ID: {job['job_id']}\n"
            f"Model: {job['model']}\n"
            f"Status: {job['status']}\n"
            f"Speed: {job['speed']}\n"
            f"Budget: ${job.get('budget', 'N/A')}",
            title="Finetuning Job"
        ))
        
        # Monitor job
        console.print("\n[cyan]Monitoring job progress...[/cyan]")
        monitor_job(job["job_id"])
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def monitor_job(job_id: str):
    """Monitor job progress"""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task(f"Job {job_id}...", total=None)
        
        while True:
            try:
                response = requests.get(f"{BASE_URL}/jobs/{job_id}")
                response.raise_for_status()
                job = response.json()
                
                status = job["status"]
                
                if status == "completed":
                    progress.update(task, description=f"[green]Job completed! Cost: ${job.get('cost', 0):.2f}[/green]")
                    console.print(Panel(
                        f"[green]Job completed successfully![/green]\n\n"
                        f"Job ID: {job['job_id']}\n"
                        f"Status: {job['status']}\n"
                        f"Cost: ${job.get('cost', 0):.2f}\n"
                        f"Assigned Node: {job.get('assigned_node', 'N/A')}",
                        title="Job Complete"
                    ))
                    break
                elif status == "failed":
                    progress.update(task, description="[red]Job failed![/red]")
                    console.print(Panel(
                        f"[red]Job failed![/red]\n\n"
                        f"Error: {job.get('error_message', 'Unknown error')}",
                        title="Job Failed"
                    ))
                    break
                elif status == "running":
                    progress.update(task, description=f"[yellow]Job running... (Status: {status})[/yellow]")
                else:
                    progress.update(task, description=f"Job {status}...")
                
                time.sleep(2)
            except KeyboardInterrupt:
                console.print("\n[yellow]Monitoring stopped[/yellow]")
                break
            except Exception as e:
                console.print(f"[red]Error monitoring job: {e}[/red]")
                break


@cli.command()
@click.argument("job_id")
def job_status(job_id: str):
    """Get job status"""
    try:
        response = requests.get(f"{BASE_URL}/jobs/{job_id}")
        response.raise_for_status()
        job = response.json()
        
        console.print(Panel(
            f"Job ID: {job['job_id']}\n"
            f"Status: {job['status']}\n"
            f"Model: {job['model']}\n"
            f"Cost: ${job.get('cost', 0):.2f}\n"
            f"Assigned Node: {job.get('assigned_node', 'N/A')}\n"
            f"Created: {job['created_at']}",
            title="Job Status"
        ))
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
def stats():
    """Get system statistics"""
    try:
        response = requests.get(f"{BASE_URL}/stats")
        response.raise_for_status()
        stats = response.json()
        
        table = Table(title="System Statistics")
        table.add_column("Metric")
        table.add_column("Value")
        
        table.add_row("Total Nodes", str(stats["nodes"]["total"]))
        table.add_row("Avg Reputation", f"{stats['nodes']['average_reputation']:.2f}")
        table.add_row("Avg Compute Score", f"{stats['nodes']['average_compute_score']:.2f}")
        table.add_row("Total Jobs", str(stats["jobs"]["total"]))
        table.add_row("Running Jobs", str(stats["jobs"]["running"]))
        table.add_row("Completed Jobs", str(stats["jobs"]["completed"]))
        table.add_row("Failed Jobs", str(stats["jobs"]["failed"]))
        table.add_row("Total Revenue", f"${stats['revenue']['total']:.2f}")
        
        console.print(table)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
def health():
    """Check system health"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        response.raise_for_status()
        health = response.json()
        
        status_color = {
            "healthy": "green",
            "degraded": "yellow",
            "unhealthy": "red"
        }.get(health["status"], "white")
        
        console.print(Panel(
            f"Status: [{status_color}]{health['status']}[/{status_color}]\n"
            f"Active Nodes: {health['active_nodes']}\n"
            f"Issues: {', '.join(health['issues']) if health['issues'] else 'None'}",
            title="System Health"
        ))
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


if __name__ == "__main__":
    cli()

