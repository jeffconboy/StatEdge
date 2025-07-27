#!/bin/bash

# Claude MCP Commands for StatEdge Postman Integration
# Copy and paste these commands to add the Postman MCP server

echo "🔧 Claude MCP Configuration Commands for StatEdge"
echo "=============================================="
echo ""

echo "1. Add Postman MCP Server:"
echo "claude mcp add --transport stdio \"postman-runner\" \"/home/jeffreyconboy/postman-mcp-wrapper.sh\""
echo ""

echo "2. Verify all MCP connections:"
echo "claude mcp list"
echo ""

echo "3. Check MCP server status:"
echo "claude mcp status"
echo ""

echo "4. Remove MCP server (if needed):"
echo "claude mcp remove \"postman-runner\""
echo ""

echo "📊 Current StatEdge MCP Servers (7 total):"
echo "✅ Docker Hub MCP - Container management"
echo "✅ PyBaseball Docs MCP - MLB data expertise" 
echo "✅ Fetch MCP - Web content retrieval"
echo "✅ GitHub MCP - Repository management"
echo "✅ PostgreSQL MCP - Database operations"
echo "✅ Playwright MCP - Web automation & testing"
echo "✅ Context7 MCP - Live documentation"
echo "🆕 Postman MCP - API testing with Newman"
echo ""

echo "🎯 Example Postman MCP Usage:"
echo "Ask Claude: 'Run the Postman collection for MLB Stats API testing'"
echo "Ask Claude: 'Execute API tests for our FanGraphs integration'"
echo "Ask Claude: 'Test the sports betting odds endpoint collection'"