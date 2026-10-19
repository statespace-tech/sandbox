# Statespace sandbox

A small shop that tests [Statespace](https://statespace.com) end to end. It
shows the setup that a repository needs:

| File | Purpose |
| --- | --- |
| `app.py`, `Dockerfile` | The shop. It prints a JSON line for each visit and purchase |
| `statespace.toml` | The app, and the share of each arm |
| `.github/workflows/statespace.yml` | Publishes each commit of an `exp/` branch |
| `.github/workflows/production.yml` | Builds and records the default from `main` |

Branch protection on `main` requires one approval, so each commit of an arm
needs a second person before users see it.

To try it, push a branch named `exp/price/lower` that lowers `PRICE`, and open
a pull request. The `statespace/arm` check tells what runs.
