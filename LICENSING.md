# Licensing guide (for the seller)

One repository, two deployments. `EDITION` decides which pages exist.

| Edition | Pages | License key |
|---|---|---|
| `free` (default) | Home, Theory, Single Well, Parameter Estimation | not needed |
| `pro` | all pages | required for pages marked pro |

Which pages are pro is set in `utils/license.py` (`PRO_PAGES`).
In the free edition the pro pages are not registered in `Home.py`, so they cannot be opened even by typing the URL.

## One-time setup (on your own computer)
    pip install cryptography
    python make_key.py --init
This writes `license_private.pem` (SECRET, back it up, never commit it; `.gitignore` excludes it) and prints the **public key**.
If you lose the private key you cannot issue keys that the deployed app accepts. If you replace it, every old key stops working.

## Deploy the two editions from the same private repo
**Free (Community Cloud):** no settings needed. EDITION defaults to `free`.

**Pro (Render / Railway):** set environment variables
- `EDITION` = `pro`
- `LICENSE_PUBLIC_KEY` = the public key printed by `--init`
- `REVOKED_IDS` = (optional) comma-separated key ids to cancel early
Start command: `streamlit run Home.py --server.port $PORT --server.address 0.0.0.0`

(On Community Cloud the same names can be put in the app's Secrets box.)

## Issue a key
    python make_key.py --customer "Acme Water" --days 365
    python make_key.py --customer "Acme Water" --until 2027-12-31 --note "invoice 1042"
Email the printed `THEIS.…` key. It is also logged in `keys_issued.csv` (local, git-ignored).
`--days` counts from today; the last valid day is the printed expiry date.

## Renew
Issue a new key with a new expiry date and send it. The old key simply expires.

## Revoke early (refund, leaked key)
Add the key id (shown when issued, also in `keys_issued.csv`) to `REVOKED_IDS` on the pro server and restart/redeploy.

## Other commands
    python make_key.py --check THEIS.…     # verify a key
    python make_key.py --list              # keys issued so far

## Limits to be aware of
- A customer can share a key with colleagues until it expires or you revoke it.
- Expiry uses the server's clock, so customers cannot extend a key.
- The key is entered per browser session; customers paste it again on a new visit.
