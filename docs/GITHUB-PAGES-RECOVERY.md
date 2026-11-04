# GitHub Pages recovery (stuck deployment)

If Actions show **in progress deployment** or Pages status is **errored**:

1. **Settings → Pages → Source:** **Deploy from a branch** → `main` → **`/docs`** (not GitHub Actions).

2. As repo **admin** (Divine16), run:
   ```sh
   ./scripts/unblock_pages_deploy.sh
   ```

3. **Settings → Pages:** turn Pages **off**, save, turn **on** again with `main` / `/docs`.

4. Wait **10–15 minutes**.

5. Push a new commit to `main` (do not only re-run old failed workflows).

6. If still broken after 30 minutes, contact **GitHub Support** with deployment ID
   `1d3428500cf37e1736a1b2d8281cdc81ebf0cbfe`.
