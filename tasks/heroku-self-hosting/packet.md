<!-- Create one packet for every non-trivial Consumer Task. `svc task init` creates only this shape. Do not create family children until their topology or information owner is admitted; keep this as a compact Human collaboration surface, not a completed-work log. -->
# heroku-self-hosting

- **Objective**: A fork owner can manually converge the selected commit to two Heroku Eco apps backed by the Neon default branch, with the same observable Core and PostgREST contract as the existing Render self-host profile.
- **Guardrails**: Keep Render unchanged and canonical production defaults unchanged. Never persist the Neon owner URL in Heroku, print JWT/database passwords, rotate role passwords on rerun, adopt an app owned by another self-host profile, or infer cleanup authority.
- **Verification**: Shell syntax, workflow YAML parsing, `git diff --check`, and `pdm run check` pass. Provider mutation remains acceptance-testable only with owner credentials; the workflow itself performs Core and PostgREST black-box probes.
- **Current Truth**: The dedicated Heroku workflow builds the selected commit, reuses the existing Heroku delivery mechanics with production-preserving defaults, binds app ownership to the selected Neon project, and documents five secrets plus two variables. Render remains unchanged.
- **Next Step**: Human review and a credentialed workflow dispatch from a fork.
