"""
Example usage of OpenMesh API
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000/api/v1"


def register_example_nodes():
    """Register example nodes"""
    nodes = [
        {"node_id": "node_1", "host": "localhost", "port": 8080, "gpu_memory": 24, "compute_score": 8.5},
        {"node_id": "node_2", "host": "localhost", "port": 8081, "gpu_memory": 16, "compute_score": 7.0},
        {"node_id": "node_3", "host": "localhost", "port": 8082, "gpu_memory": 32, "compute_score": 9.0},
    ]
    
    print("Registering nodes...")
    for node_data in nodes:
        response = requests.post(f"{BASE_URL}/nodes/register", json=node_data)
        if response.status_code == 200:
            node = response.json()
            print(f"✓ Registered {node['node_id']} (Reputation: {node['reputation']:.2f})")
        else:
            print(f"✗ Failed to register {node_data['node_id']}: {response.text}")


def list_nodes():
    """List all active nodes"""
    print("\nActive nodes:")
    response = requests.get(f"{BASE_URL}/nodes")
    if response.status_code == 200:
        nodes = response.json()
        for node in nodes:
            print(f"  - {node['node_id']}: {node['gpu_memory']}GB, Score: {node['compute_score']:.1f}, Rep: {node['reputation']:.2f}")
    else:
        print(f"Error: {response.text}")


def create_finetune_job():
    """Create a finetuning job"""
    print("\nCreating finetuning job...")
    job_data = {
        "model": "llama-3-8b",
        "dataset": "custom_data.json",
        "max_budget": 40.0,
        "speed": "balanced",
        "user_id": "example_user"
    }
    
    response = requests.post(f"{BASE_URL}/finetune", json=job_data)
    if response.status_code == 200:
        job = response.json()
        print(f"✓ Job created: {job['job_id']}")
        print(f"  Model: {job['model']}")
        print(f"  Status: {job['status']}")
        return job['job_id']
    else:
        print(f"✗ Failed to create job: {response.text}")
        return None


def monitor_job(job_id):
    """Monitor job progress"""
    print(f"\nMonitoring job {job_id}...")
    max_wait = 60  # Maximum wait time in seconds
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        response = requests.get(f"{BASE_URL}/jobs/{job_id}")
        if response.status_code == 200:
            job = response.json()
            status = job['status']
            print(f"  Status: {status}", end="\r")
            
            if status == "completed":
                print(f"\n✓ Job completed! Cost: ${job.get('cost', 0):.2f}")
                if job.get('assigned_node'):
                    print(f"  Assigned to: {job['assigned_node']}")
                return True
            elif status == "failed":
                print(f"\n✗ Job failed: {job.get('error_message', 'Unknown error')}")
                return False
        
        time.sleep(2)
    
    print(f"\n⏱ Job still running after {max_wait} seconds")
    return False


def get_system_stats():
    """Get system statistics"""
    print("\nSystem Statistics:")
    response = requests.get(f"{BASE_URL}/stats")
    if response.status_code == 200:
        stats = response.json()
        print(f"  Nodes: {stats['nodes']['total']}")
        print(f"  Jobs: {stats['jobs']['total']} (Running: {stats['jobs']['running']}, Completed: {stats['jobs']['completed']})")
        print(f"  Revenue: ${stats['revenue']['total']:.2f}")
    else:
        print(f"Error: {response.text}")


def health_check():
    """Check system health"""
    print("\nHealth Check:")
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        health = response.json()
        status_icon = "✓" if health['status'] == "healthy" else "⚠"
        print(f"  {status_icon} Status: {health['status']}")
        print(f"  Active Nodes: {health['active_nodes']}")
        if health['issues']:
            print(f"  Issues: {', '.join(health['issues'])}")
    else:
        print(f"Error: {response.text}")


if __name__ == "__main__":
    print("=" * 50)
    print("OpenMesh Example Usage")
    print("=" * 50)
    
    # Health check
    health_check()
    
    # Register nodes
    register_example_nodes()
    
    # List nodes
    list_nodes()
    
    # Create a job
    job_id = create_finetune_job()
    
    if job_id:
        # Monitor job
        monitor_job(job_id)
    
    # Get stats
    get_system_stats()
    
    print("\n" + "=" * 50)
    print("Example completed!")
    print("=" * 50)

