export type TransactionType = 'income' | 'expense' | 'investment' | 'donation'

export interface User {
  id: string
  cognito_sub: string
  email: string | null
  created_at: string
}

export interface Wallet {
  id: string
  user_id: string
  name: string
  created_at: string
}

export interface WalletCreate {
  name: string
}

export interface WalletUpdate {
  name: string
}

export interface Subcategory {
  id: string
  transaction_type: TransactionType
  name: string
  is_system: boolean
  user_id: string | null
}

export interface Transaction {
  id: string
  wallet_id: string
  type: TransactionType
  subcategory_id: string
  amount_cents: number
  description: string | null
  tags: string[]
  transaction_date: string
  created_at: string
}

export interface TransactionCreate {
  wallet_id: string
  type: TransactionType
  subcategory_id: string
  amount_cents: number
  description?: string | null
  tags?: string[]
  transaction_date: string
}

export interface TransactionUpdate {
  type?: TransactionType
  subcategory_id?: string
  amount_cents?: number
  description?: string | null
  tags?: string[]
  transaction_date?: string
}

export interface Budget {
  id: string
  user_id: string
  subcategory_id: string
  limit_cents: number
  period_start: string
  period_end: string
  created_at: string
}

export interface BudgetCreate {
  subcategory_id: string
  limit_cents: number
  period_start: string
  period_end: string
}

export interface BudgetUpdate {
  subcategory_id?: string
  limit_cents?: number
  period_start?: string
  period_end?: string
}

export interface Goal {
  id: string
  user_id: string
  title: string
  target_cents: number
  goal_type: TransactionType
  period_start: string
  period_end: string
  created_at: string
}

export interface GoalCreate {
  title: string
  target_cents: number
  goal_type: TransactionType
  period_start: string
  period_end: string
}

export interface GoalUpdate {
  title?: string
  target_cents?: number
  goal_type?: TransactionType
  period_start?: string
  period_end?: string
}

export interface ChatResponse {
  reply: string
}
