# StatEdge MCP Server Documentation

## Overview

StatEdge is equipped with **7 powerful Model Context Protocol (MCP) servers** that provide AI-enhanced development capabilities. These servers enable intelligent assistance across all aspects of the baseball analytics platform development lifecycle.

## 🎯 Quick Reference

| MCP Server | Type | Purpose | Status |
|------------|------|---------|---------|
| [Docker Hub](#docker-hub-mcp) | Container | Docker image management | ✅ Connected |
| [PyBaseball Docs](#pybaseball-docs-mcp) | HTTP | MLB data expertise | ✅ Connected |
| [Fetch](#fetch-mcp) | Container | Web content retrieval | ✅ Connected |
| [GitHub](#github-mcp) | Container | Repository management | ✅ Connected |
| [PostgreSQL](#postgresql-mcp) | Container | Database operations | ✅ Connected |
| [Playwright](#playwright-mcp) | Container | Web automation & testing | ✅ Connected |
| [Context7](#context7-mcp) | Node.js | Live documentation | ✅ Connected |

---

## 🐳 Docker Hub MCP

### Purpose
Intelligent Docker image discovery, repository management, and container optimization for StatEdge infrastructure.

### Key Capabilities
- **Image Search**: Find optimal base images for services
- **Repository Management**: Create, update, and manage Docker repositories
- **Security Analysis**: Discover hardened and verified images
- **Tag Management**: List and analyze image versions

### Example Usage
```
"Find official PostgreSQL 16 Alpine images for production"
"Search for lightweight Python 3.11 containers optimized for FastAPI"
"Show me Docker Hardened Images for database containers"
"List all tags for the redis repository"
```

### Configuration
- **Container**: `mcp/dockerhub`
- **Authentication**: Docker Hub Personal Access Token
- **Transport**: STDIO via wrapper script
- **Location**: `/home/jeffreyconboy/dockerhub-mcp-wrapper.sh`

---

## 📚 PyBaseball Docs MCP

### Purpose
Expert guidance on MLB data collection, PyBaseball library usage, and baseball analytics best practices.

### Key Capabilities
- **Data Collection**: Statcast and FanGraphs integration patterns
- **API Usage**: PyBaseball function documentation and examples
- **Performance**: Rate limiting and optimization strategies
- **Analytics**: Advanced baseball metrics explanations

### Example Usage
```
"How do I collect Statcast data for specific date ranges?"
"Show me FanGraphs batting stats collection methods"
"What are the best practices for PyBaseball rate limiting?"
"Help me optimize Statcast data queries for performance"
```

### Configuration
- **URL**: `https://gitmcp.io/jldbc/pybaseball`
- **Transport**: HTTP
- **Type**: Documentation server

---

## 🌐 Fetch MCP

### Purpose
Web content retrieval and HTML-to-markdown conversion for research and data collection.

### Key Capabilities
- **Content Extraction**: Convert web pages to structured markdown
- **Research**: Gather information from baseball and betting websites
- **Documentation**: Fetch external documentation and guides
- **Data Sources**: Access content that requires web scraping

### Example Usage
```
"Fetch the latest MLB standings from ESPN"
"Get content from FanGraphs player analysis pages"
"Retrieve documentation from the MLB Stats API website"
"Fetch betting odds comparison from sports websites"
```

### Configuration
- **Container**: `mcp/fetch`
- **Transport**: STDIO via wrapper script
- **User Agent**: "StatEdge-Analytics/1.0 (Baseball Analytics Platform)"
- **Location**: `/home/jeffreyconboy/fetch-mcp-wrapper.sh`

---

## 🔧 GitHub MCP

### Purpose
Comprehensive GitHub repository management, issue tracking, and development workflow automation.

### Key Capabilities
- **Repository Management**: Create, update, and manage repositories
- **Issue Tracking**: Create and manage development tasks
- **Pull Requests**: Code review and collaboration workflows
- **Actions**: CI/CD pipeline management
- **Security**: Vulnerability scanning and dependency management

### Example Usage
```
"Create a GitHub issue for optimizing the trending players API"
"Review pull requests in the StatEdge repository"
"Set up GitHub Actions for automated testing"
"Check repository security vulnerabilities"
```

### Configuration
- **Container**: `ghcr.io/github/github-mcp-server`
- **Authentication**: GitHub Personal Access Token
- **Transport**: STDIO via wrapper script
- **Toolsets**: All (repositories, issues, pull requests, actions, security, etc.)
- **Location**: `/home/jeffreyconboy/github-mcp-wrapper.sh`

---

## 🗄️ PostgreSQL MCP

### Purpose
Read-only database inspection, schema analysis, and query execution for the StatEdge database.

### Key Capabilities
- **Schema Inspection**: Analyze table structures and relationships
- **Data Exploration**: Execute read-only queries for insights
- **Performance Analysis**: Identify optimization opportunities
- **Data Validation**: Verify data integrity and consistency

### Example Usage
```
"Show me the schema of the statcast table"
"Query players with the highest batting averages in the last 30 days"
"How many Statcast records do we have by month?"
"Analyze the structure of all tables in the database"
```

### Configuration
- **Container**: `mcp/postgres`
- **Database**: `postgresql://statedge_user:statedge_pass@localhost:15432/statedge`
- **Transport**: STDIO via wrapper script
- **Access**: Read-only queries only
- **Location**: `/home/jeffreyconboy/postgres-mcp-wrapper.sh`

---

## 🎭 Playwright MCP

### Purpose
Web automation, end-to-end testing, and interactive data collection for StatEdge applications.

### Key Capabilities
- **Web Automation**: Navigate and interact with web applications
- **Testing**: End-to-end testing of StatEdge components
- **Screenshots**: Visual documentation and regression testing
- **Data Collection**: Automated scraping of dynamic content

### Example Usage
```
"Test the StatEdge dashboard functionality end-to-end"
"Navigate to FanGraphs and screenshot the player leaderboards"
"Automate testing of our live scores ticker component"
"Scrape betting odds from interactive sports websites"
```

### Configuration
- **Container**: `mcr.microsoft.com/playwright/mcp`
- **Browser**: Headless Chrome with vision capabilities
- **Transport**: STDIO via wrapper script
- **Viewport**: 1920x1080
- **Features**: Vision enabled, isolated sessions
- **Location**: `/home/jeffreyconboy/playwright-mcp-wrapper.sh`

---

## 📖 Context7 MCP

### Purpose
Access to up-to-date documentation for any library, framework, or technology used in StatEdge development.

### Key Capabilities
- **Live Documentation**: Current, version-specific library docs
- **Library Resolution**: Automatic library ID resolution
- **Topic Filtering**: Focused documentation by topic
- **Implementation Examples**: Real-world usage patterns

### Example Usage
```
"Get the latest FastAPI documentation for background tasks"
"Show me current Vue.js 3 Composition API documentation"
"Find PostgreSQL documentation for query optimization"
"Get pandas documentation for performance optimization"
```

### Configuration
- **Package**: `@upstash/context7-mcp`
- **Transport**: STDIO via npx wrapper
- **Location**: `/home/jeffreyconboy/context7-mcp-wrapper.sh`

---

## 🎪 Powerful Combinations

### Complete Development Workflow
```
Context7 + GitHub + PostgreSQL
"Research latest SQLAlchemy async patterns, implement in our database layer, and create a pull request"
```

### Data Pipeline Development
```
PyBaseball + Fetch + PostgreSQL
"Get PyBaseball documentation, fetch MLB API specs, and design optimal database schema"
```

### Testing & Quality Assurance
```
Playwright + GitHub + Docker Hub
"Test our application, find issues, create GitHub tickets, and research better container images"
```

### Full-Stack Research
```
All 7 MCPs
"Research modern baseball analytics architectures, find optimal technologies, implement features, test everything, and document the process"
```

---

## 🚀 Getting Started

### Check MCP Status
```bash
claude mcp list
```

### Example Workflow
1. **Research**: Use Context7 and PyBaseball Docs for technical guidance
2. **Plan**: Create GitHub issues for development tasks
3. **Develop**: Query PostgreSQL for data insights while coding
4. **Test**: Use Playwright for automated testing
5. **Deploy**: Find optimal containers with Docker Hub
6. **Monitor**: Fetch external monitoring and analytics data

---

## 🔧 Troubleshooting

### Connection Issues
All MCP servers should show `✓ Connected` status. If any show `✗ Failed to connect`:

1. **Check wrapper scripts**: Ensure all scripts in `/home/jeffreyconboy/` are executable
2. **Verify Docker containers**: Run `docker images` to confirm all MCP images are pulled
3. **Test individual MCPs**: Run wrapper scripts directly to diagnose issues
4. **Restart if needed**: Use `claude mcp remove <name>` and `claude mcp add` to reconfigure

### Configuration Files
- **Main config**: `/home/jeffreyconboy/.claude.json`
- **Wrapper scripts**: `/home/jeffreyconboy/*-mcp-wrapper.sh`

---

## 🔒 Security Features

### Container Isolation
- All containerized MCPs run in ephemeral, isolated environments
- No persistent data storage outside of designated volumes
- Proper security contexts and restricted permissions

### Authentication
- Docker Hub: Personal Access Token with read-only permissions
- GitHub: Personal Access Token with repository access
- PostgreSQL: Read-only database access
- Other MCPs: No authentication required (public APIs)

### Network Security
- Containers use host networking only when required
- External API calls are limited to documented endpoints
- No unauthorized network access or data exfiltration

---

## 📊 Performance Notes

### Resource Usage
- **Lightweight**: MCPs only consume resources during active use
- **Ephemeral**: Most containers are removed after each operation
- **Efficient**: Minimal overhead when not in use

### Best Practices
- Use specific, focused queries for better performance
- Combine MCP capabilities in single requests when possible
- Cache results locally when appropriate

---

*This documentation covers the complete MCP ecosystem configured for the StatEdge baseball analytics platform. All servers are production-ready and optimized for development workflows.*