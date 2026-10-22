# Statespace sandbox

A small shop that tests [Statespace](https://statespace.com) end to end.

| File | Purpose |
| --- | --- |
| `app.py`, `Dockerfile` | The shop. It prints a JSON line for each visit and purchase |
| `test.py`, `.github/workflows/test.yml` | The test that `main` requires |
| `.github/workflows/production.yml` | Builds the default from `main` and records it |

The Statespace App opens a "Set up Statespace" pull request. It adds:

- `statespace.toml`, with the app and the share of each arm;
- `.github/workflows/statespace.yml`, which records each commit of an `exp/`
  branch.

Branch protection on `main` requires the `test` check. An arm runs while its
pull request can merge, so it runs only while the test passes.

To try it:

1. Merge the setup pull request.
2. Push a branch named `exp/price/lower` that lowers `PRICE`.
3. Open a pull request. The `Statespace` check tells what runs.
