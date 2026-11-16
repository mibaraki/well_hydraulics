#!/usr/bin/env python3
"""
make_key.py — create and check license keys. RUN THIS ON YOUR OWN COMPUTER ONLY.

  python make_key.py --init                         # once: make your key pair
  python make_key.py --customer "Acme Water" --days 365
  python make_key.py --customer "Acme Water" --until 2027-12-31
  python make_key.py --check THEIS.xxxx.yyyy        # check a key you were sent
  python make_key.py --list                         # keys you have issued

Keep license_private.pem secret and backed up. Never commit it to GitHub
(.gitignore already excludes it). Anyone with it can create valid keys.
"""

import argparse
import base64
import csv
import json
import os
import secrets
import sys
from datetime import date, datetime, timedelta

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

HERE = os.path.dirname(os.path.abspath(__file__))
PRIVATE_PEM = os.environ.get("LICENSE_PRIVATE_PEM", os.path.join(HERE, "license_private.pem"))
LOG_CSV = os.path.join(HERE, "keys_issued.csv")
PREFIX = "THEIS"


def b64e(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def public_b64(priv):
    raw = priv.public_key().public_bytes(serialization.Encoding.Raw,
                                         serialization.PublicFormat.Raw)
    return b64e(raw)


def load_private():
    if not os.path.exists(PRIVATE_PEM):
        sys.exit(f"No private key at {PRIVATE_PEM}. Run:  python make_key.py --init")
    with open(PRIVATE_PEM, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)


def cmd_init(args):
    if os.path.exists(PRIVATE_PEM):
        sys.exit(f"{PRIVATE_PEM} already exists. Refusing to overwrite it: keys you "
                 "issued earlier would stop working. Delete it yourself if you are sure.")
    priv = Ed25519PrivateKey.generate()
    pem = priv.private_bytes(serialization.Encoding.PEM,
                             serialization.PrivateFormat.PKCS8,
                             serialization.NoEncryption())
    with open(PRIVATE_PEM, "wb") as f:
        f.write(pem)
    os.chmod(PRIVATE_PEM, 0o600)
    print(f"Private key saved to {PRIVATE_PEM}  (KEEP SECRET, BACK IT UP)\n")
    print("Public key — set this as LICENSE_PUBLIC_KEY on the pro server:\n")
    print(public_b64(priv))


def cmd_make(args):
    if not args.customer:
        sys.exit("--customer is required")
    if args.until:
        expiry = datetime.strptime(args.until, "%Y-%m-%d").date()
    else:
        expiry = date.today() + timedelta(days=args.days)
    priv = load_private()
    payload = {"v": 1, "id": secrets.token_hex(4), "c": args.customer,
               "e": expiry.isoformat()}
    payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    key = f"{PREFIX}.{b64e(payload_bytes)}.{b64e(priv.sign(payload_bytes))}"

    new = not os.path.exists(LOG_CSV)
    with open(LOG_CSV, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["issued", "id", "customer", "expires", "note"])
        w.writerow([date.today().isoformat(), payload["id"], args.customer,
                    expiry.isoformat(), args.note or ""])

    print(f"Customer : {args.customer}")
    print(f"Key id   : {payload['id']}   (use this id to revoke)")
    print(f"Expires  : {expiry}  (last valid day)\n")
    print("Send the customer this key:\n")
    print(key)


def cmd_check(args):
    priv = load_private()
    sys.path.insert(0, HERE)
    # reuse the app's own checker, without needing Streamlit running
    from utils.license import verify_key
    ok, info, msg = verify_key(args.check, public_key_b64=public_b64(priv), revoked=set())
    print(("VALID: " if ok else "NOT VALID: ") + msg)
    if info:
        print(json.dumps(info))


def cmd_list(args):
    if not os.path.exists(LOG_CSV):
        sys.exit("No keys issued yet.")
    with open(LOG_CSV, newline="") as f:
        for row in csv.reader(f):
            print("  ".join(row))


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--init", action="store_true", help="create your private/public key pair")
    p.add_argument("--customer", help="customer or organisation name")
    p.add_argument("--days", type=int, default=365, help="validity in days (default 365)")
    p.add_argument("--until", help="last valid day, YYYY-MM-DD (overrides --days)")
    p.add_argument("--note", help="free text kept in keys_issued.csv")
    p.add_argument("--check", metavar="KEY", help="verify a key")
    p.add_argument("--list", action="store_true", help="show keys you have issued")
    args = p.parse_args()

    if args.init:
        cmd_init(args)
    elif args.check:
        cmd_check(args)
    elif args.list:
        cmd_list(args)
    else:
        cmd_make(args)


if __name__ == "__main__":
    main()
