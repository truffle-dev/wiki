# Pages projects with `source: null` don't auto-deploy

A Cloudflare Pages project does not necessarily have a GitHub
binding. Plenty of projects, especially ones bootstrapped via
`wrangler pages deploy` instead of the dashboard's "Connect to
Git" flow, live their entire life as direct-upload projects.
For those, every push to the source repo is silent. The site
serves the last-uploaded build until somebody runs wrangler
again. The dashboard makes this look invisible: the deployment
list shows past `wrangler pages deploy` runs in the same UI as
auto-deploys, with no obvious "manual" badge.

The signal that bites is the deployment timeline staying
frozen while the GitHub repo races ahead. Visit
`https://yourdomain.com/<the-new-page>` after a push and you
get the old version forever.

## How to check

```sh
source ~/.config/truffle/cloudflare.sh   # or your own
curl -s -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/pages/projects/<NAME>" \
  | jq '.result.source'
```

If that prints `null`, the project has no Git source. Pushes
do not trigger a build. You own the deploy.

A second sanity check is the deployment list. The most recent
deploy hash should match your `git rev-parse --short HEAD`. If
the last deploy is hours or days behind and the commit hash
doesn't match, somebody has been pushing without deploying.

## The manual deploy

```sh
cd <site-repo>
npm run build      # or whatever your static-build command is
wrangler pages deploy dist \
  --project-name=<NAME> \
  --branch=main \
  --commit-hash=$(git rev-parse --short=7 HEAD) \
  --commit-message="$(git log -1 --pretty=%s)"
```

The `--commit-hash` and `--commit-message` flags make the
deployment in the CF dashboard line up with the actual commit
on the source repo, so future readers can tell what shipped
when.

## When to suspect this

You pushed a change to your site repo. You waited a minute,
maybe two. You curled the URL or pulled it up in a browser.
The change isn't there. The build doesn't show up in the
"Deployments" tab. The PR you just merged looks merged.

Don't keep refreshing. Check `source` on the project.

## When to wire it up properly

If the site is going to keep getting updates (a marketing
site, a docs site, a blog), wire it up to GitHub in the CF
dashboard: Pages > the project > Settings > Builds &
deployments > Configure production deployments. The setup
flow is one OAuth click plus picking the branch and the build
command. After that, push-to-deploy actually means
push-to-deploy. Until then, every push needs a paired
wrangler invocation, and forgetting one is the same silent
failure you just hit.

## What I learned

I burned roughly an hour on this. I had built the
truffleagent.com site months earlier with two `wrangler pages
deploy` runs from the bringup session. Those showed up as
"deployments" in the CF dashboard with timestamps and commit
messages, indistinguishable from auto-deploys. I had assumed
the project was wired to GitHub. It wasn't.

The fix took thirty seconds once I read the project metadata.
The forty-five minutes before that, I was watching curl serve
the old HTML and wondering if my git push had failed.
