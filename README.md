# Statespace sandbox

A small shop to try [Statespace](https://statespace.com) from start to end.
You run the shop behind `ssp proxy` with Docker. Then you run the experiment
`price`: the live commit and a commit with a lower price, each on 5% of the
visitors.

| File | Purpose |
| --- | --- |
| `app.py`, `Dockerfile` | The shop. `POST /buy` prints a JSON line on stdout |
| `test.py` | The tests. Run them with `python3 test.py` |
| `statespace.toml` | The events, the metrics, the experiment `price`, and the settings of two apps |
| `.github/workflows/build.yml` | Builds each push and records the build |
| `.github/workflows/test.yml` | Runs the tests on each pull request |

Two apps run from this folder:

- `sandbox`: the public copy. The arms of `price` get at most 20% of the
  visitors.
- `sandbox-dev`: a development copy. The arms of `price` can get all
  visitors, and testers can open an arm with `?ssp_arm=price:<commit>`.

## What you need

- The CLI, signed in with GitHub. You need the admin role on
  `statespace-tech/sandbox` to add the app and its token, and the write
  role to start and stop the experiment.

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

6. In a second terminal, open the shop through the proxy. No experiment
   runs, so live answers. The response has `"experiment": null`.

   ```shell
   curl -s localhost:8080/
   ```

7. Show the experiment. It is `stopped` and has no arms. The live
   commit of `main` defines it, in `[experiment.price]`.

   ```shell
   ssp experiment show price --app sandbox
   ```

8. Change the price on a new branch, and push the commit. The workflow
   builds the commit and records the build.

   ```shell
   git switch -c lower-price
   sed -i.bak 's/^PRICE = 12/PRICE = 9/' app.py
   rm app.py.bak
   git commit -am "Lower the price to 9"
   git push -u origin lower-price
   ```

9. When the workflow is done, set the arms. The live commit is the first
   arm, so it is the reference. The new commit is the second arm. Each arm
   gets 5% of the visitors.

   ```shell
   main=$(git rev-parse origin/main)
   new=$(git rev-parse HEAD)
   ssp experiment update price --app sandbox \
     --arm "$main=0.05" --arm "$new=0.05"
   ```

10. Start the experiment. The command waits until both arms are ready. It
    waits at most 5 minutes.

    ```shell
    ssp experiment start price --app sandbox \
      --note "price 9 instead of 12"
    ```

11. Send visitors through the proxy. Each visitor gets its own cookie
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

12. Look at the evidence. The commit status `statespace/sandbox/price`
    on each arm's commit shows the version, the share, the subjects, the
    split check, and `buy rate %` against the other arm.

    ```shell
    ssp experiment show price --app sandbox
    gh api "repos/statespace-tech/sandbox/commits/$new/statuses" \
      --jq '.[0] | .context + ": " + .description'
    ```

13. Stop the experiment. Its visitors go back to live in seconds.
    Statespace keeps the evidence of this version.

    ```shell
    ssp experiment stop price --app sandbox --note "enough data"
    ```

## Change the arms

You cannot change the arms of a running experiment. Stop it, update it,
and start it again. Each start begins a new version.

1. Push a third commit, such as a price of 10.
2. Replace the arm `$new` with the new commit. `=0` removes an arm. The
   arm `$main` does not change.

   ```shell
   ssp experiment update price --app sandbox \
     --arm "$new=0" --arm "$(git rev-parse HEAD)=0.05"
   ```

3. Start the experiment again.

   ```shell
   ssp experiment start price --app sandbox \
     --note "price 10 instead of 12"
   ```

## Open an arm yourself

The app `sandbox-dev` has `overrides = true`. On a proxy for
`sandbox-dev`, add `?ssp_arm=price:<commit>` to the URL to get an arm of
the running experiment.

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

3. Set the arms of `price` on `sandbox-dev`, and start it.

   ```shell
   ssp experiment update price --app sandbox-dev \
     --arm "$main=0.05" --arm "$new=0.05"
   ssp experiment start price --app sandbox-dev
   ```

4. Open the new arm. Use the first 7 characters of the commit or more.

   ```shell
   curl -s -L -c jar -b jar \
     "localhost:8081/?ssp_arm=price:${new:0:7}"
   ```

The response has `"experiment": "price"` and `"price": 9`.

## Clean up

1. Stop the experiment on each app.

   ```shell
   ssp experiment stop price --app sandbox
   ssp experiment stop price --app sandbox-dev
   ```

2. Stop the proxies.
3. Remove the apps. This deletes their data.

   ```shell
   ssp app remove sandbox
   ssp app remove sandbox-dev
   ```
