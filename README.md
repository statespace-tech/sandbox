# Statespace sandbox

A small shop to try [Statespace](https://statespace.com) from start to end.
You run the shop behind `ssp proxy` with Docker. Then you test a lower price
as an arm on a share of the visitors.

| File | Purpose |
| --- | --- |
| `app.py`, `Dockerfile` | The shop. `POST /buy` prints a JSON line on stdout |
| `test.py` | The tests. Run them with `python3 test.py` |
| `statespace.toml` | The events, the metrics, and the settings of two apps |
| `.github/workflows/build.yml` | Builds each push and records the build |
| `.github/workflows/test.yml` | Runs the tests on each pull request |

Two apps run from this folder:

- `sandbox`: the public copy. It uses the shared settings.
- `sandbox-dev`: a development copy. It can put all visitors in arms, and
  testers can open an arm with `?ssp_arm=<commit>`.

## What you need

- The CLI, signed in with GitHub. You need the admin role on
  `statespace-tech/sandbox` to add the app and its token.

  ```shell
  curl -fsSL https://statespace.com/install.sh | bash
  ssp login
  ```

- A machine with Docker for the proxy.
- A build of `main`. The workflow `build.yml` makes one on each push.

## Run the demo

1. Clone the repo, and go to its folder.

   ```shell
   git clone https://github.com/statespace-tech/sandbox
   cd sandbox
   ```

2. Add the app. The CLI reads the repo and the folder from the current
   folder.

   ```shell
   ssp app add sandbox --note "public demo"
   ```

3. Add a runtime token for the app. Keep the secret in the output. The CLI
   shows it only one time.

   ```shell
   ssp token add --app sandbox --note "Docker proxy"
   export STATESPACE_TOKEN=<secret from the output>
   ```

4. Write the image of `main` to a file. The proxy runs this image as live.

   ```shell
   main=$(git rev-parse origin/main)
   docker buildx imagetools inspect \
     "ghcr.io/statespace-tech/sandbox:$main" \
     --format '{{.Manifest.Digest}}' > digest
   echo "ghcr.io/statespace-tech/sandbox@$(cat digest)" \
     > image
   ```

5. Start the proxy. Keep it running in this terminal.

   ```shell
   ssp proxy docker --app sandbox --image-file "$PWD/image"
   ```

6. In a second terminal, open the shop through the proxy. The response
   says `"side": "live"`.

   ```shell
   curl -s localhost:8080/
   ```

7. Change the price on a new branch, and push the commit. The workflow
   builds the commit and records the build.

   ```shell
   git switch -c lower-price
   sed -i.bak 's/^PRICE = 12/PRICE = 9/' app.py
   rm app.py.bak
   git commit -am "Lower the price to 9"
   git push -u origin lower-price
   ```

8. When the workflow is done, add the commit as an arm. 5% of the visitors
   get the arm, and 5% get the control.

   ```shell
   ssp arm add "$(git rev-parse HEAD)" --app sandbox \
     --share 0.05 --note "price 9 instead of 12"
   ```

9. Send visitors through the proxy. Each visitor gets its own cookie
   file. One visitor in three buys an item.

   ```shell
   for i in $(seq 1 600); do
     curl -s -c "jar$i" -b "jar$i" localhost:8080/ > /dev/null
     if [ $((i % 3)) -eq 0 ]; then
       curl -s -c "jar$i" -b "jar$i" -X POST \
         localhost:8080/buy > /dev/null
     fi
     rm "jar$i"
   done
   ```

10. Look at the evidence. The commit status `statespace/sandbox` on the
    commit shows the share, the subjects, the split check, and
    `buy rate %` for the arm and the control.

    ```shell
    ssp arm show "$(git rev-parse HEAD)" --app sandbox
    commit=$(git rev-parse HEAD)
    gh api "repos/statespace-tech/sandbox/commits/$commit/statuses" \
      --jq '.[0] | .context + ": " + .description'
    ```

11. Stop the arm. Its visitors go back to live in seconds. The commit
    status becomes red.

    ```shell
    ssp arm stop "$(git rev-parse HEAD)" --app sandbox \
      --note "check the stop"
    ```

12. Resume the arm.

    ```shell
    ssp arm resume "$(git rev-parse HEAD)" --app sandbox
    ```

13. Remove the arm. Statespace keeps its evidence. The commit status says
    "Ended".

    ```shell
    ssp arm remove "$(git rev-parse HEAD)" --app sandbox
    ```

## Open an arm yourself

The app `sandbox-dev` has `overrides = true`. On a proxy for
`sandbox-dev`, add `?ssp_arm=<commit>` to the URL to get a running arm.

1. Add the app and a token for it, as in steps 2 and 3.

   ```shell
   ssp app add sandbox-dev --note "demo, development copy"
   ssp token add --app sandbox-dev --note "Docker proxy"
   ```

2. Start a proxy for it, with the token of `sandbox-dev`.

   ```shell
   ssp proxy docker --app sandbox-dev \
     --image-file "$PWD/image" --listen 0.0.0.0:8081
   ```

3. Add the commit as an arm of `sandbox-dev`.

   ```shell
   ssp arm add "$(git rev-parse HEAD)" --app sandbox-dev
   ```

4. Open the arm. Use the first 7 characters of the commit or more.

   ```shell
   curl -s -L -c jar -b jar \
     "localhost:8081/?ssp_arm=$(git rev-parse --short=7 HEAD)"
   ```

The response says `"side": "arm"` and `"price": 9`.

## Clean up

1. Remove every arm of each app.
2. Stop the proxies.
3. Remove the apps. This deletes their data.

   ```shell
   ssp app remove sandbox
   ssp app remove sandbox-dev
   ```
