# Setting up plotmetwist.in → GitHub Pages

End goal: visiting **https://plotmetwist.in** loads the `plot-twist-nepotism.html` report.

Total cost: **₹600–1,200/year** for the domain. Hosting is free (GitHub Pages).

## Step 1 — Buy the domain

`.in` domains are sold by most major registrars. Pick one:

| Registrar | Typical price (.in/yr) | Notes |
|---|---|---|
| **Cloudflare** (cloudflare.com/products/registrar) | ~₹650 | Cheapest, no markup, but you need a Cloudflare account first |
| **Namecheap** (namecheap.com) | ~₹750 | Clean UI, good for first-timers |
| **BigRock** (bigrock.in) | ~₹800 | India-based, supports UPI |
| **GoDaddy** | ~₹1,000 | Most well-known but pricier |

Search for `plotmetwist.in` on any of them. If it's available, buy it (1-year is enough to start). You'll need:
- An email address
- Payment (UPI / card / netbanking)
- For .in domains: a CR.IN (.IN registry) account is auto-created during checkout

**Skip "Domain Privacy" upsells** for now — `.in` already redacts WHOIS by default.

## Step 2 — Upload the repo to GitHub (if not done yet)

Follow `UPLOAD_INSTRUCTIONS.md`. The new `CNAME` file (containing the line `plotmetwist.in`) goes up with everything else — GitHub Pages needs it to claim the domain.

## Step 3 — Turn on GitHub Pages

1. Open your repo: `https://github.com/pritha-datta/bollywood-nepotism-analysis`
2. Click **Settings** (top-right tabs)
3. Click **Pages** (left sidebar)
4. Under **Build and deployment**:
   - Source: **Deploy from a branch**
   - Branch: **main**, Folder: **/ (root)**
   - Click **Save**
5. Under **Custom domain**, GitHub will detect the `CNAME` file and show `plotmetwist.in` — click **Save**.
6. Tick **Enforce HTTPS** (it'll grey out until the domain is verified — that's fine; tick it once you can).

GitHub will show: *"Your site is ready to be published at https://plotmetwist.in"* but it won't actually work until DNS is set up. That's the next step.

## Step 4 — Point DNS at GitHub

Log into your registrar's dashboard, find the DNS / nameserver management page for `plotmetwist.in`, and add these records:

### Option A — Apex domain only (plotmetwist.in)

| Type | Name | Value | TTL |
|---|---|---|---|
| A | @ | 185.199.108.153 | 3600 |
| A | @ | 185.199.109.153 | 3600 |
| A | @ | 185.199.110.153 | 3600 |
| A | @ | 185.199.111.153 | 3600 |
| CNAME | www | pritha-datta.github.io | 3600 |

The four A records are GitHub Pages' anycast IPs (these are stable and documented at https://docs.github.com/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site).

### Option B — If your registrar is Cloudflare

Use the same records as Option A. Make sure the proxy (orange-cloud icon) is **off** initially — turn it on once HTTPS is working, for free CDN + caching.

## Step 5 — Wait for DNS to propagate (5 min to 24 hr)

Check with:
- Visit https://dnschecker.org/#A/plotmetwist.in — should show GitHub's four IPs globally.
- Then visit https://plotmetwist.in — should load the report.

Once HTTPS is verified by GitHub (auto, takes ~10 min after DNS works):
- Go back to repo **Settings → Pages**
- Tick **Enforce HTTPS** (it should now be available)

## Step 6 — Make the HTML the default landing page

Right now visiting `plotmetwist.in` will go to GitHub's default — which is the README. To make the report itself the landing page:

**Option 1 (easiest)**: rename `plot-twist-nepotism.html` to `index.html` in the repo. GitHub Pages auto-loads `index.html` at the root URL.

**Option 2 (less work but uglier URL)**: keep the filename, and the URL becomes `plotmetwist.in/plot-twist-nepotism.html`. You can put a redirect in a new `index.html`:

```html
<!DOCTYPE html>
<meta http-equiv="refresh" content="0; url=plot-twist-nepotism.html">
```

I recommend **Option 1** — short, clean URL.

## Troubleshooting

- **`plotmetwist.in` shows a 404 / "improperly configured"** → wait longer, check DNS records carefully (no trailing dots, no http://).
- **HTTPS toggle stuck disabled** → GitHub is still issuing the cert. Comes back enabled in 10–60 min after DNS resolves correctly.
- **Site loads but no styling** → the HTML file might still reference old paths. Check by opening `https://plotmetwist.in/plot-twist-nepotism.html` directly.

## What happens if you don't want GitHub Pages

Same DNS approach, different target. Alternatives:
- **Netlify** — free, drag-drop deploy from the dashboard, custom domain in their UI, you set DNS to point at their nameservers.
- **Cloudflare Pages** — free, very fast, also drag-drop, integrated with their DNS.

If you want to switch to one of those, just tell me and I'll write the equivalent setup notes.
