---
description: "Manage and check SSH tunnels for infrastructure access"
tools: ["bash"]
---

Manage SSH tunnels for infrastructure services with intelligent port management.

Parse $ARGUMENTS for tunnel operations:
- "list" or empty - Show active tunnels
- "elastic" - Create Elasticsearch tunnel (19200)
- "mysql" - Create MySQL tunnel (13306)
- "grafana" - Create Grafana tunnel (13000)
- "kafka" - Create Kafka tunnel (19092)
- "auth" - Create auth server tunnel (18000)
- "kill [service]" - Kill specific tunnel
- "kill all" - Kill all tunnels
- "start [service]" - Start specific tunnel

Default tunnel mappings from SSH config:
- elastic1: localhost:19200 → elastic1:9200 (Elasticsearch)
- mysql: localhost:13306 → mysql:3306 (MySQL)
- grafana: localhost:13000 → grafana:3000 (Grafana)
- kafka: localhost:19092 → kafka:9092 (Kafka)
- auth-server: localhost:18000 → auth-server:8000 (Auth API)
- frontend: localhost:13000 → frontend:3000 (Frontend)

Known hosts:
- mac (<USER_NAME>@<PRIVATE_IP>) - MacBook Pro, primary dev machine
- <INFERENCE_HOST> (<USER_NAME>@<PRIVATE_IP>) - Linux desktop
- <WORKSTATION_HOST> (<USER_NAME>@<PRIVATE_IP>) - Gaming/utility box
- kali (localhost / 127.0.0.1) - This machine (Kali Linux)
- <INFERENCE_HOST>-ts (<USER_NAME>@<TAILSCALE_IP>) - Tailscale

Operations:
1. Check existing tunnels: `ps aux | grep ssh.*-L`
2. Create new tunnels with background process
3. Verify tunnel connectivity
4. Clean up stale tunnel processes
5. Display tunnel status and local ports

Smart features:
- Auto-detect port conflicts
- Background tunnel creation
- Health check after tunnel creation
- Persistent tunnel management

Example usage:
- `/tunnels` - List active tunnels
- `/tunnels elastic` - Create Elasticsearch tunnel
- `/tunnels kill mysql` - Kill MySQL tunnel
- `/tunnels start auth` - Start auth server tunnel

Arguments: $ARGUMENTS
