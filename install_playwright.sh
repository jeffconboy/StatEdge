#!/bin/bash
# Install Playwright browsers for E2E testing

echo "🎭 Installing Playwright browsers..."
npx playwright install chrome
npx playwright install chromium
npx playwright install firefox

echo "✅ Playwright browsers installed!"
echo "Now you can run E2E tests with the Playwright MCP"