#!/bin/bash

# StatEdge Postman MCP Server Setup Script
# This script sets up the mcp-postman server for API testing

echo "🚀 Setting up Postman MCP Server for StatEdge..."

# Create directory for MCP servers if it doesn't exist
mkdir -p /home/jeffreyconboy/mcp-servers

# Clone the mcp-postman repository
cd /home/jeffreyconboy/mcp-servers
if [ ! -d "mcp-postman" ]; then
    echo "📥 Cloning mcp-postman repository..."
    git clone https://github.com/shannonlal/mcp-postman.git
fi

# Install dependencies and build
cd mcp-postman
echo "📦 Installing dependencies..."
pnpm install
echo "🔨 Building the project..."
pnpm build

# Create wrapper script
echo "📝 Creating wrapper script..."
cat > /home/jeffreyconboy/postman-mcp-wrapper.sh << 'EOF'
#!/bin/bash
exec node /home/jeffreyconboy/mcp-servers/mcp-postman/build/index.js
EOF

# Make wrapper script executable
chmod +x /home/jeffreyconboy/postman-mcp-wrapper.sh

echo "✅ Setup complete!"
echo ""
echo "🔧 Next steps:"
echo "1. Add the MCP server to Claude configuration:"
echo "   claude mcp add --transport stdio \"postman-runner\" \"/home/jeffreyconboy/postman-mcp-wrapper.sh\""
echo ""
echo "2. Verify the connection:"
echo "   claude mcp list"
echo ""
echo "3. Test with a Postman collection:"
echo "   Ask Claude: 'Run the Postman collection at /path/to/your/collection.json'"
echo ""
echo "📚 StatEdge API Testing Use Cases:"
echo "- Test MLB Stats API endpoints"
echo "- Validate FanGraphs data integration"
echo "- Verify Statcast data pipeline APIs"
echo "- Test sports betting API connections"
echo "- Performance and load testing"