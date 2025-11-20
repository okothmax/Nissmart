export interface User {
  id: string;
  created_at: string;
  updated_at: string;
  email: string;
  full_name: string;
  is_active: boolean;
}

export interface Account {
  id: string;
  user_id?: string | null;
  name: string;
  currency: string;
  type: string;
  status: string;
  balance: number;
  available_balance: number;
  created_at: string;
  updated_at: string;
}

export interface Transaction {
  id: string;
  reference: string;
  user_id?: string | null;
  account_id: string;
  type: string;
  status: string;
  amount: number;
  currency: string;
  description?: string | null;
  occurred_at: string;
  context_data?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface UserListResponse {
  items: User[];
  total: number;
}

export interface UserBalanceResponse {
  user_id: string;
  accounts: Account[];
  totals: Array<{
    currency: string;
    balance: number;
    available_balance: number;
  }>;
}

export interface TransactionListResponse {
  items: Transaction[];
  total: number;
}

export interface AdminSummaryResponse {
  total_users: number;
  total_wallet_value: number;
  total_deposits: number;
  total_transfers: number;
  total_withdrawals: number;
  total_deposits_amount: number;
  total_transfers_amount: number;
  total_withdrawals_amount: number;
}
