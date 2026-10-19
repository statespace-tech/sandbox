# Statespace sandbox

A small shop that tests [Statespace](https://statespace.com) end to end. It
shows the setup that a repository needs:

| File | Purpose |
| --- | --- |
| `app.py`, `Dockerfile` | The shop. It prints a JSON line for each visit and purchase |
| `test.py`, `.github/workflows/test.yml` | The test that `main` requires |
| `statespace.toml` | The app, and the share of each arm |
| `.github/workflows/statespace.yml` | Publishes each commit of an `exp/` branch |
| `.github/workflows/production.yml` | Builds and records the default from `main` |

Branch protection on `main` requires the `test` check. An arm runs while its
pull request can merge, so it runs only while the test passes. A team usually
also requires an approval, so that a second person approves each commit of an
arm before users see it.

To try it, push a branch named `exp/price/lower` that lowers `PRICE`, and open
a pull request. The `statespace/arm` check tells what runs.
