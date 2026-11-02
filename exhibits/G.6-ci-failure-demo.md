# G.6 — CI failure on a deliberately broken record

Use this only to produce a screenshot for exhibit G.6. **Do not merge** the broken commit to `main`.

## Steps

1. Create a branch: `git checkout -b exhibit/ci-failure-demo`

2. In `data/territories.json`, set one record to unverified, for example:

   ```json
   "verified": false,
   "verified_by": null
   ```

3. Commit and push. Open the pull request or inspect the **CI** workflow run on the branch.

4. Capture a screenshot of the failed step **Validate data** showing:

   `verified is not true — a human must check this record against the primary source before it can ship`

5. Close the PR without merging; delete the branch.

The enforced rules live in `scripts/validate.py` (citation required; `verified` must be true).
