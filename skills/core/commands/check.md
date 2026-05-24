---
description: "Check infrastructure health - all systems or specific services"
tools: ["bash"]
---

Check the health and status of infrastructure components with intelligent service detection.

Parse $ARGUMENTS to identify what to check:
- "all" or empty - Check all critical infrastructure
- "<PRODUCT_NAME>" - <PRODUCT_NAME> production systems
- "elastic" or "elasticsearch" - Elasticsearch cluster (elastic1-5)
- "elastic-test" - Test Elasticsearch cluster
- "auth" - Authentication servers
- "database" or "db" - Database servers (mysql, mongodb)
- "scrapers" - Data collection scrapers
- "proxy" or "proxies" - Proxy fleet (proxy0-proxy9)
- "dev" - Development environments
- "core" - Core infrastructure services
- Specific host names (e.g., "elastic1", "mysql", "grafana")

Health checks performed:
1. SSH connectivity test
2. System uptime and load
3. Service-specific checks:
   - Elasticsearch: Cluster health, node status
   - MySQL: Connection test, process list
   - Web services: HTTP response codes
   - Scrapers: Process status, recent activity
4. Disk space and memory usage
5. Network connectivity between services

Infrastructure groups from SSH config:
- <PRODUCT_NAME>: <PRODUCT_NAME>-client, <PRODUCT_NAME>-alerting-docker, <PRODUCT_NAME>-es
- Elasticsearch: elastic1-5, elastic-test1-3  
- Core: auth-server, frontend, mysql, mongodb, kafka, grafana
- Scrapers: telegram-scraper, discord-scraper, scraper-staging
- Proxies: proxy0-proxy9
- Development: <USER_NAME>-dev, <TEAM_MEMBER>-dev (× N — one per teammate)

Example usage:
- `/check` or `/check all` - Check all systems
- `/check elastic` - Check Elasticsearch cluster
- `/check <PRODUCT_NAME>` - Check <PRODUCT_NAME> production
- `/check proxy` - Check proxy fleet
- `/check elastic1` - Check specific server

Arguments: $ARGUMENTS