# Pipeline Doctor Skill

This skill allows Antigravity to interact with the **Pipeline Doctor Agent** to monitor, diagnose, and improve the project's automated pipelines.

## Capabilities

1. **Diagnose Pipeline**: Analyzes the latest GitHub Actions runs to identify failure causes.
   - Command: `python3 tools/pipeline_doctor.py --diagnose`
2. **Improve Pipeline**: Analyzes pipeline code and logs to suggest optimizations.
   - Command: `python3 tools/pipeline_doctor.py --improve`
3. **Check Health**: Views the history of pipeline performance.
   - File: `data/pipeline_health.json`

## When to use

- When the project's GitHub Actions are failing.
- When you want to optimize the scraping or video generation logic.
- When performing maintenance on the CI/CD flow.

## Instructions for Antigravity

Whenever the user asks to "check the pipeline", "see why it failed", or "improve the automation", use the commands listed above.
Always review the output of the doctor before suggesting fixed to the user.
