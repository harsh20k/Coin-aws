## Deploy Backend Failure — Database Password Auth (Feb 25)

**Problem:** Backend deploy pipeline failing at `create_tables` step with:
```
asyncpg.exceptions.InvalidPasswordError: password authentication failed for user "dalla"
```

**Root Cause:**
- Commit `bfcf0e9` ("CI/CD implementation initial run", Feb 22) added `override_special = "!#$%&*()-_=+[]{}<>:?"` to the `random_password` resource in `rds.tf`
- This changed the resource config, so the next `terraform apply` regenerated the password
- The password wasn't regenerated immediately — it happened later when `terraform apply` was run for other changes (monitoring deletion in `7bd3dd3`, Lambda auto-confirm addition, etc.)
- The newly generated password contained URL-special characters (`#`, `%`, `?`, `:`) from `override_special`
- These characters were interpolated **raw** into the `DATABASE_URL` connection string stored in the SSM parameter
- When asyncpg parsed the URL, characters like `#` (fragment), `%` (encoding prefix), `?` (query delimiter) truncated or corrupted the password
- The password sent to PostgreSQL didn't match the actual RDS password → `InvalidPasswordError`

**Fix (`infra/terraform/rds.tf` line 41):**
```hcl
# Before
database_url = "postgresql+asyncpg://dalla:${random_password.db_password.result}@...host...:...port.../dalla"

# After
database_url = "postgresql+asyncpg://dalla:${urlencode(random_password.db_password.result)}@...host...:...port.../dalla"
```
- Wrapped password with `urlencode()` so special characters are percent-encoded (`#` → `%23`, `?` → `%3F`, etc.)
- asyncpg now receives the full correct password after URL-decoding

**Steps to apply:**
1. `terraform apply` in `infra/terraform/` — updates the SSM parameter with the URL-encoded password
2. Re-run the deploy backend pipeline

**Key Learning:**
- Never embed passwords raw into connection URLs — always URL-encode them
- `random_password` with `special = true` can generate characters that break URL parsing
- Adding/changing `override_special` causes password regeneration on the next `terraform apply`, not at commit time

**Files Changed:**
- `infra/terraform/rds.tf` — added `urlencode()` around password in `database_url` local
