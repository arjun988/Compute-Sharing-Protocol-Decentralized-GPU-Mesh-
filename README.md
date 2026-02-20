# OpenMesh v0.1 - Decentralized GPU Mesh Compute Sharing Protocol

A production-ready decentralized compute sharing protocol that enables GPU resource sharing across a mesh network. Built with FastAPI, Redis, Celery, and Docker.

## Architecture

The system consists of 5 core layers:

1. **Node Registration** - Manages node registration, heartbeat, and status
2. **Job Scheduling** - Handles job allocation, load balancing, and fault tolerance
3. **Task Containerization** - Docker-based task execution and sandboxing
4. **Payment/Reputation** - Payment processing and reputation management
5. **Monitoring** - System monitoring, metrics, and health checks

## Tech Stack

- **FastAPI** - Control plane API
- **Redis** - Task queue and caching
- **Celery** - Distributed task execution
- **Docker** - Task containerization and sandboxing
- **SQLAlchemy** - Database ORM
- **SQLite** - Database (can be upgraded to PostgreSQL)

## Features

- ✅ Node registration and management
- ✅ Intelligent job scheduling with load balancing
- ✅ Docker-based task containerization
- ✅ Payment and reputation system
- ✅ System monitoring and metrics
- ✅ Budget guardrails for jobs
- ✅ Fault tolerance and retry logic
- ✅ Vast.ai integration (Phase 2)
- ✅ CLI interface for testing

## Installation

### Prerequisites

- Python 3.10+
- Redis server
- Docker (optional, for containerization)

### Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd Compute-Sharing-Protocol-Decentralized-GPU-Mesh-
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Initialize database**
```bash
python init_db.py
```

6. **Start Redis** (if not running)
```bash
# On Linux/Mac
redis-server

# On Windows (using WSL or Docker)
docker run -d -p 6379:6379 redis:alpine
```

## Running the System

### 1. Start the API Server

```bash
python main.py
```

The API will be available at `http://localhost:8000`

### 2. Start Celery Worker (in a separate terminal)

```bash
python run_celery.py
```

Or using celery directly:
```bash
celery -A app.tasks.celery_app worker --loglevel=info
```

### 3. Use the CLI

```bash
# Register a node
python -m app.cli register-node --node-id node_1 --host localhost --port 8080 --gpu-memory 24 --compute-score 8.5

# List nodes
python -m app.cli list-nodes

# Create a finetuning job
python -m app.cli finetune --model llama-3-8b --dataset my_data.json --max-budget 40 --speed balanced

# Check job status
python -m app.cli job-status <job_id>

# View system stats
python -m app.cli stats

# Check system health
python -m app.cli health
```

## API Endpoints

### Nodes
- `POST /api/v1/nodes/register` - Register a new node
- `GET /api/v1/nodes` - List all active nodes
- `GET /api/v1/nodes/{node_id}` - Get node details
- `POST /api/v1/nodes/{node_id}/heartbeat` - Update node heartbeat
- `GET /api/v1/nodes/{node_id}/metrics` - Get node metrics

### Jobs
- `POST /api/v1/finetune` - Create a finetuning job
- `GET /api/v1/jobs/{job_id}` - Get job details
- `POST /api/v1/jobs/{job_id}/retry` - Retry a failed job
- `GET /api/v1/jobs/{job_id}/metrics` - Get job metrics

### System
- `GET /api/v1/stats` - Get system statistics
- `GET /api/v1/health` - System health check

## Usage Examples

### Example 1: Register a Node

```bash
python -m app.cli register-node \
  --node-id node_1 \
  --host localhost \
  --port 8080 \
  --gpu-memory 24 \
  --compute-score 8.5
```

### Example 2: Create a Finetuning Job

```bash
python -m app.cli finetune \
  --model llama-3-8b \
  --dataset custom_data.json \
  --max-budget 40 \
  --speed balanced
```

### Example 3: Using the API Directly

```python
import requests

# Register a node
response = requests.post("http://localhost:8000/api/v1/nodes/register", json={
    "node_id": "node_1",
    "host": "localhost",
    "port": 8080,
    "gpu_memory": 24,
    "compute_score": 8.5
})

# Create a finetuning job
response = requests.post("http://localhost:8000/api/v1/finetune", json={
    "model": "llama-3-8b",
    "dataset": "my_data.json",
    "max_budget": 40,
    "speed": "balanced"
})
job = response.json()
print(f"Job ID: {job['job_id']}")
```

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── config.py              # Configuration
│   ├── database.py            # Database setup
│   ├── models.py              # Database models
│   ├── tasks.py               # Celery tasks
│   ├── vast_ai.py             # Vast.ai integration
│   ├── cli.py                 # CLI interface
│   ├── api/
│   │   ├── main.py            # FastAPI app
│   │   ├── routes.py          # API routes
│   │   └── schemas.py         # Pydantic schemas
│   └── layers/
│       ├── node_registration.py
│       ├── job_scheduling.py
│       ├── task_containerization.py
│       ├── payment_reputation.py
│       └── monitoring.py
├── main.py                    # API server entry point
├── run_celery.py              # Celery worker entry point
├── init_db.py                 # Database initialization
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Configuration

Edit `.env` file to configure:

- Redis connection
- Celery broker/backend
- Docker settings
- Vast.ai API key (for Phase 2)
- API host/port

## Phase 1: CPU-Only Prototype

The current implementation simulates GPU nodes and workloads:

- Nodes are registered with simulated GPU capacity
- Jobs are allocated to nodes based on compute score and reputation
- Tasks are executed using CPU-intensive simulations
- Budget guardrails prevent cost overruns

## Phase 2: Vast.ai Integration

Vast.ai integration is included for GPU rental:

- Automatic GPU selection based on price and specs
- Budget-aware instance creation
- Instance lifecycle management

To use Vast.ai, set `VAST_API_KEY` in your `.env` file.

## Development

### Running in Development Mode

```bash
# Terminal 1: API Server
python main.py

# Terminal 2: Celery Worker
python run_celery.py

# Terminal 3: CLI Commands
python -m app.cli <command>
```

### Database Migrations

The database is automatically created on first run. To reset:

```bash
rm openmesh.db
python init_db.py
```

## License

See LICENSE file for details.

## Contributing

This is a production-level implementation focused on backend functionality. The system is designed to be testable via command-line interface only.
