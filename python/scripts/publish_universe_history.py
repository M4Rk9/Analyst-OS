"""Controlled preview/apply for reviewed HDFC/L&T/Tata history, using existing atomic publisher."""

from scripts.plan_universe_history import load_catalog
from scripts.publish_ril_tcs import main

if __name__ == "__main__":
    raise SystemExit(main(catalog_loader=load_catalog, description=__doc__))
