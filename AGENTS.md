# Watch Drop — project guide

## What this project does

Watch Drop is an email-driven TV episode alert service. Users email `add <TMDB TV URL>`, `remove <TMDB TV URL>`, `help`, or `nuke account` to an SES address. Subscription rows are stored in DynamoDB. A scheduled Lambda checks TMDB for episodes that aired yesterday and asks a separate Lambda to send notifications through SES.

## Repository map

- `lambdas/email_processor/`: handles inbound SES email commands and edits subscription rows.
- `lambdas/tmdb_scanner/`: scheduled scan of subscriptions and TMDB episode checks. Its deployment package includes vendored Python dependencies; preserve these when editing application code.
- `lambdas/ses_sender/`: sends HTML and text emails through SES.
- `iac/`: Terraform configuration for AWS resources, IAM, SES, scheduling, and Lambda packaging.
- `misc/`: architecture diagrams, sample SES events, and example payloads.
- `README.md`: user setup, configuration, and deployment instructions.

## Working rules

- Keep changes focused and consistent with the existing Python and Terraform structure. Avoid broad refactors unless requested.
- Treat AWS infrastructure and email behavior as production-sensitive. Do not run `terraform apply`, destroy resources, change the configured remote state backend, or deploy Lambda code unless explicitly asked.
- Never expose or commit secrets, credentials, real user email data, Terraform state, or local `terraform.tfvars`. The `.gitignore` already excludes Terraform state and variable files.
- Terraform's `archive_file` data sources package each Lambda source directory. Keep each function's imports and runtime dependencies available inside its package; AWS runtime is Python 3.11.
- `tmdb_scanner` uses vendored `requests` dependencies. Do not remove or regenerate vendored files as part of unrelated changes.
- Preserve both HTML and plain-text variants for outbound email content.
- There is no checked-in test suite or Python dependency manifest at present. Inspect the relevant handler and sample events before changing event parsing. Do not invent a test or build workflow without a task that needs one.

## Useful entry points

- Email command flow: `lambdas/email_processor/main.py`; response copy: `lambdas/email_processor/responses.py`.
- Scheduled episode alert flow: `lambdas/tmdb_scanner/main.py`; alert templates: `lambdas/tmdb_scanner/aired_alert.py`.
- Outbound SES delivery: `lambdas/ses_sender/main.py`.
- Lambda packaging and runtime settings: `iac/lambdas.tf`.
- Resource wiring and permissions: the other `.tf` files under `iac/`.

## Verification

For code changes, prefer narrow static checks or targeted local checks when dependencies and fixtures allow. For Terraform changes, inspect the diff and use `terraform fmt -check` or `terraform validate` only when the local Terraform setup is available; validation must not apply changes or contact AWS. Report checks that could not be run.
