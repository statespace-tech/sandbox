"""The check that branch protection requires on main."""

import app

assert 0 < app.PRICE <= 100, f"the price must be between 1 and 100, not {app.PRICE}"
