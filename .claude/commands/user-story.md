# User Story Creation

Create well-formed user stories for our Agile development sprints.

## User Story Template
As a [type of user]
I want [some goal/functionality]
So that [some reason/value]

## Story Creation Process

1. **Identify the User**
   - Who is the primary user for this feature?
   - What's their role or context?
   - What are their key characteristics

2. **Define the Want/Need**
   - What specific functionality do they need?
   - What action do they want to perform?
   - What problem are they trying to solve?

3. **Clarify the Value**
   - Why is this important to them?
   - What benefit will they gain?
   - How does this help achieve their goals?

4 Identify the vertical slice components needed
    (UI, API, database, etc.)

## Acceptance Criteria

For each user story, define 3-5 acceptance criteria:
Acceptance Criteria:

 Given [initial context], when [action], then [expected result]
 Given [different context], when [action], then [different result]
 [Additional specific conditions that must be met]


## Story Refinement

Ensure stories are:
- **Independent**: Can be developed separately
- **Negotiable**: Details can be discussed and refined
- **Valuable**: Delivers clear user value
- **Estimable**: Can estimate effort required
- **Small**: Fits within a 1-hour sprint
- **Testable**: Can verify completion

## Example User Stories

### Good Examples:
As a developer
I want automated tests to run on code changes
So that I can catch bugs early and maintain code quality
Acceptance Criteria:

 Tests run automatically when files are saved
 Test results are displayed clearly
 Failed tests prevent deployment


As a website visitor
I want to see loading indicators on slow operations
So that I know the system is working and don't get frustrated
Acceptance Criteria:

 Spinner appears for operations taking >2 seconds
 Loading message explains what's happening
 User can cancel long-running operations


### Avoid These Patterns:
- "As a user I want a better system" (too vague)
- "As a developer I want to refactor everything" (too big)
- "As a user I want the login page" (no clear value)

## Sprint-Sized Stories

For 1-hour sprints, ensure stories are small enough:
- Can be completed in 45-50 minutes
- Have clear demo-able outcome
- Don't require extensive research
- Build on existing code when possible

Use story splitting techniques:
- **Workflow Steps**: Break complex workflows into individual steps
- **Business Rules**: Separate different business logic rules
- **Data Variations**: Handle different data types separately
- **Interface Options**: Create basic version first, enhance later

Remember: Great user stories facilitate conversation and shared understanding, not comprehensive documentation.