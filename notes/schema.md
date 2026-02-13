-- Dalla – minimal SQL schema
-- Assumes auth is in Cognito; users table links app data to Cognito sub.

-- User (Cognito identity link)
CREATE TABLE users (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cognito_sub VARCHAR(255) NOT NULL UNIQUE,
  email      VARCHAR(255),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Wallets (multiple per user)
CREATE TABLE wallets (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name       VARCHAR(255) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Transaction type enum
CREATE TYPE transaction_type AS ENUM ('income', 'expense', 'investment', 'donation');

-- Subcategories: per type; is_system = default, user_id NULL = system
CREATE TABLE subcategories (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  transaction_type transaction_type NOT NULL,
  name             VARCHAR(255) NOT NULL,
  is_system        BOOLEAN NOT NULL DEFAULT false,
  user_id          UUID REFERENCES users(id) ON DELETE CASCADE,
  UNIQUE (transaction_type, name, user_id)
);

-- Transactions
CREATE TABLE transactions (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  wallet_id        UUID NOT NULL REFERENCES wallets(id) ON DELETE CASCADE,
  type             transaction_type NOT NULL,
  subcategory_id   UUID NOT NULL REFERENCES subcategories(id),
  amount_cents     BIGINT NOT NULL,
  description      TEXT,
  tags             JSONB DEFAULT '[]',
  transaction_date DATE NOT NULL,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Budgets: expense limit per subcategory per period (e.g. month)
CREATE TABLE budgets (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id        UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  subcategory_id UUID NOT NULL REFERENCES subcategories(id),
  limit_cents    BIGINT NOT NULL,
  period_start   DATE NOT NULL,
  period_end     DATE NOT NULL,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Goals: target amount for a type over a period
CREATE TABLE goals (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id        UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title          VARCHAR(500) NOT NULL,
  target_cents   BIGINT NOT NULL,
  goal_type      transaction_type NOT NULL,
  period_start   DATE NOT NULL,
  period_end     DATE NOT NULL,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes for common queries
CREATE INDEX idx_wallets_user ON wallets(user_id);
CREATE INDEX idx_transactions_wallet_date ON transactions(wallet_id, transaction_date);
CREATE INDEX idx_transactions_type ON transactions(type);
CREATE INDEX idx_budgets_user_period ON budgets(user_id, period_start, period_end);
CREATE INDEX idx_goals_user_period ON goals(user_id, period_start, period_end);
CREATE INDEX idx_subcategories_type_user ON subcategories(transaction_type, user_id);
