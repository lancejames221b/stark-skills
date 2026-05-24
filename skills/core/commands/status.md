---
description: "Get real-time status of critical infrastructure services"
tools: ["bash"]
---

Display real-time status dashboard of critical infrastructure services.

Parse $ARGUMENTS for optional filters:
- "prod" or "production" - Production services only
- "staging" - Staging environments
- "quick" - Fast overview (no deep checks)
- "detailed" - Comprehensive status report

Status checks include:

**<PRODUCT_NAME> Production:**
- <PRODUCT_NAME>-client (GCP): SSH, HTTP response, disk space
- <PRODUCT_NAME>-alerting-docker: Container status, alerts queue
- <PRODUCT_NAME>-es: Elasticsearch health, indices status

**Elasticsearch Cluster:**
- elastic1-5: Cluster health, node roles, shard distribution
- elastic-test1-3: Test cluster status

**Core Services:**
- auth-server: Authentication service, user sessions
- frontend: Web frontend, response time
- mysql: Database connections, slow queries
- mongodb: Replica set status, connections
- kafka: Topic status, consumer lag
- grafana: Dashboard availability, datasources

**Data Collection:**
- telegram-scraper: Process status, recent collections
- discord-scraper: Bot status, API rate limits
- scraper-staging: Staging environment status

**Proxy Fleet:**
- proxy0-proxy9: Connectivity, IP rotation status

**Development:**
- <USER_NAME>-dev: Vault server, development services
- Other dev boxes: Resource usage, active sessions

Output format:
✅ Service OK | ⚠️ Warning | ❌ Critical | 🔄 Checking...

Arguments: $ARGUMENTS