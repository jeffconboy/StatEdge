# Parallel Debug Analysis

Debug issue: $ARGUMENTS

Launch 5 specialized debugging agents to analyze this issue from different angles:

**Task 1 - Code Structure Analyst**: 
Examine the overall code structure, imports, dependencies, and file organization. Look for:
- Missing imports or circular dependencies  
- File path issues
- Configuration problems
- Version conflicts

**Task 2 - Runtime Error Detective**: 
Focus on runtime execution and error tracking. Analyze:
- Error logs and stack traces
- Database connection issues
- API authentication problems
- File system permissions

**Task 3 - Data Flow Investigator**: 
Trace data flow through the entire pipeline. Check:
- Data format consistency
- API response validation
- Database schema mismatches
- Data transformation errors

**Task 4 - Integration Specialist**: 
Examine external service integrations. Verify:
- Twitter API authentication and limits
- Claude Code integration issues
- MLB API data availability
- Weather service connectivity

**Task 5 - Environment Auditor**: 
Review environment setup and configuration. Validate:
- Environment variables and secrets
- File system structure
- Required dependencies installation
- Windows Task Scheduler configuration

Each agent should:
1. Read relevant files and logs
2. Test specific components in isolation
3. Provide specific actionable fixes
4. Rate confidence level (1-10) in their findings

After all agents complete, synthesize findings into a prioritized action plan.

