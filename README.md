# Bazar.com Distributed Bookstore

Bazar.com is a small distributed online bookstore built to demonstrate RESTful microservices, persistent storage, caching, replication, load distribution, and partial failover. The repository contains the original three-service implementation and an extended Lab 2 version that adds replicated Catalog and Order services plus a frontend LRU cache.

The Lab 2 implementation in [`part_two/`](part_two/) is the recommended version to run.

## Features

- Separate Frontend, Catalog, and Order Flask services
- REST/JSON communication between services
- SQLite-backed catalog and order data
- Two Catalog replicas and two Order replicas in Lab 2
- In-memory least-recently-used (LRU) cache for book details, limited to five entries
- Round-robin selection for uncached catalog reads
- Cache invalidation before purchases and stock changes
- Order-service retry when a replica is unavailable
- Docker images and Docker Compose orchestration

## Architecture

```text
                         GET /info/<id>
Client ---> Frontend ---> LRU cache -- miss --> Catalog replica 1
   |           |                              `-> Catalog replica 2
   |           |
   |           `-- POST /purchase/<id> ------> Order replica 1
   |                                          `-> Order replica 2
   |                                                 |
   `-------------------------------------------------+--> catalog update
                                                             |
                                                   replicated stock update
```

All client traffic enters through the Frontend service on port `5000`. Each replica owns a local SQLite database. In the normal path, a purchase is recorded by Order replica 1, copied to Order replica 2 through `/sync/<book_id>`, and sent to Catalog replica 1; that Catalog service decrements its stock and synchronizes Catalog replica 2.

### Services

| Service | Responsibility |
| --- | --- |
| Frontend | Public API, five-entry LRU cache, catalog read distribution, order failover, and cache invalidation |
| Catalog | Stores book metadata and stock; serves book details and applies/replicates stock updates |
| Order | Records purchases, requests catalog stock updates, and replicates order records |

### Caching, replication, and failover

- `GET /info/<book_id>` is served from the frontend cache when possible. On a miss, the frontend alternates between Catalog replicas and caches the response.
- Purchase requests bypass the cache. The relevant entry is invalidated before the Catalog database is changed.
- In the normal path, Catalog and Order writes are copied from replica 1 to replica 2 through internal `/sync/<book_id>` endpoints.
- The frontend tries each Order replica until one accepts a purchase, allowing purchases to continue if an Order replica is unavailable.
- Catalog reads are distributed round-robin, but the current code does **not** retry the other Catalog replica when the selected replica is down. A previously cached book remains available while Catalog replicas are unavailable.
- Replication targets are statically configured as replica 2. If replica 1 is unavailable and replica 2 handles a purchase, the current implementation does not redirect synchronization back to replica 1.
- Replication is synchronous HTTP at the application level; the implementation does not use a message broker or database-level replication.

## API

The Lab 2 public API is exposed by the Frontend service:

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/info/<book_id>` | Return a book's ID, title, topic, quantity, and price |
| `POST` | `/purchase/<book_id>` | Record a purchase and decrement replicated catalog stock |

The Catalog and Order services also expose internal `update` and `sync` routes used for replication. The original Lab 1 implementation at the repository root additionally provides topic search and order-list endpoints; these routes were not carried into the Lab 2 frontend.

Examples:

```bash
curl http://localhost:5000/info/1
curl -X POST http://localhost:5000/purchase/1
curl http://localhost:5000/info/1
```

## Technologies

- Python 3.10
- Flask 3
- Requests
- SQLite
- Docker and Docker Compose

## Project structure

```text
.
|-- Documentation/
|   `-- Dos.pdf                  # Lab 1 report
|-- catalog_service/             # Original Catalog service
|-- frontend_service/            # Original Frontend service
|-- order_service/               # Original Order service
|-- docker-compose.yml           # Original three-container deployment
`-- part_two/
    |-- Dos-Lab2_Report.pdf      # Lab 2 report
    |-- catalog_service/         # Replicated Catalog implementation
    |-- frontend_service/        # Cache and replica routing
    |-- order_service/           # Replicated Order implementation
    `-- docker-compose.yml       # Five-container Lab 2 deployment
```

## Installation and running with Docker

### Prerequisites

- Docker Engine or Docker Desktop
- Docker Compose v2 (`docker compose`)

Clone the repository, enter it, and start the Lab 2 system:

```bash
git clone <repository-url>
cd <repository-directory>/part_two
docker compose up --build
```

The frontend is then available at `http://localhost:5000`. The replica ports are only needed for container-to-container communication and are assigned dynamically on the host.

To run in the background or stop the system:

```bash
docker compose up --build -d
docker compose down
```

SQLite files are created inside the service containers. Because the Lab 2 Compose file does not mount database volumes, `docker compose down` followed by container recreation resets that data.

To run the original Lab 1 implementation instead:

```bash
docker compose up --build
```

Run that command from the repository root. It exposes the Frontend on port `5000`, Catalog on `5001`, and Order on `5002`, with host-mounted SQLite files for persistence.

## Team

- Ayham Thiab - 12218365
- Ayham Baarah - 12218367

Developed for the Distributed Operating Systems project at An-Najah National University, supervised by Dr. Samer Al-Arandi.
