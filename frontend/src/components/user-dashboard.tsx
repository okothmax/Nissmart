"use client";

import clsx from "clsx";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { useSWRConfig } from "swr";

import { Button } from "@/components/ui/button";
import { apiFetch } from "@/lib/api";
import { useApi } from "@/lib/hooks";
import type {
  Transaction,
  TransactionListResponse,
  User,
  UserBalanceResponse,
  UserListResponse,
} from "@/lib/types";
import { useRouter } from "next/navigation";

const CURRENCIES = ["KES", "USD", "EUR"];
const TRANSACTION_PAGE_SIZE = 15;

type OperationMode = "deposit" | "transfer" | "withdraw";

interface OperationState {
  mode: OperationMode;
  amount: string;
  currency: string;
  description: string;
  destinationUserId?: string;
}

interface OperationErrors {
  amount?: string;
  destinationUserId?: string;
  general?: string;
}

const INITIAL_OPERATION: OperationState = {
  mode: "deposit",
  amount: "",
  currency: "KES",
  description: "",
  destinationUserId: undefined,
};

export function UserDashboard() {
  const { mutate } = useSWRConfig();
  const router = useRouter();
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newUserName, setNewUserName] = useState("");
  const [newUserEmail, setNewUserEmail] = useState("");
  const [isCreatingUser, setIsCreatingUser] = useState(false);

  const [operation, setOperation] = useState<OperationState>(INITIAL_OPERATION);
  const [isSubmittingOperation, setIsSubmittingOperation] = useState(false);
  const [transactionsLimit, setTransactionsLimit] = useState(TRANSACTION_PAGE_SIZE);

  const transactionsEndpoint = selectedUserId
    ? `/transactions?user_id=${selectedUserId}&limit=${transactionsLimit}`
    : null;

  const {
    data: usersData,
    isLoading: isLoadingUsers,
    error: usersError,
  } = useApi<UserListResponse>("/users?limit=100");

  const {
    data: balanceData,
  } = useApi<UserBalanceResponse>(selectedUserId ? `/ledger/balance/${selectedUserId}` : null);

  const {
    data: transactionsData,
    isLoading: isLoadingTransactions,
  } = useApi<TransactionListResponse>(transactionsEndpoint);

  useEffect(() => {
    setTransactionsLimit(TRANSACTION_PAGE_SIZE);
  }, [selectedUserId]);

  const selectedUser = useMemo(() => {
    if (!selectedUserId) return null;
    return usersData?.items.find((user) => user.id === selectedUserId) ?? null;
  }, [selectedUserId, usersData?.items]);

  const handleSelectUser = (userId: string) => {
    setSelectedUserId(userId);
    setOperation((prev) => ({ ...prev, destinationUserId: undefined }));
  };

  const handleCreateUser = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!newUserName.trim() || !newUserEmail.trim()) {
      toast.error("Name and email are required");
      return;
    }

    setIsCreatingUser(true);
    try {
      const { data } = await apiFetch<User>(
        "/users",
        {
          method: "POST",
          body: JSON.stringify({
            full_name: newUserName.trim(),
            email: newUserEmail.trim(),
          }),
        },
        { idempotent: true }
      );

      toast.success("User created successfully");
      setNewUserName("");
      setNewUserEmail("");
      setIsCreateOpen(false);
      setSelectedUserId(data.id);
      await mutate("/users?limit=100");
    } catch (error) {
      toast.error((error as Error).message);
    } finally {
      setIsCreatingUser(false);
    }
  };

  const handleOperationSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedUserId) {
      toast.error("Select a user first");
      return;
    }

    if (hasOperationErrors) {
      toast.error(
        operationErrors.general ??
          operationErrors.amount ??
          operationErrors.destinationUserId ??
          "Resolve the highlighted issues before submitting."
      );
      return;
    }

    const amountNumber = Number(operation.amount);

    let endpoint = "";
    const body: Record<string, unknown> = {
      amount: amountNumber,
      currency: operation.currency,
      description: operation.description || undefined,
    };

    if (operation.mode === "deposit") {
      endpoint = "/ledger/deposit";
      body.user_id = selectedUserId;
    } else if (operation.mode === "withdraw") {
      endpoint = "/ledger/withdraw";
      body.user_id = selectedUserId;
    } else {
      endpoint = "/ledger/transfer";
      if (!operation.destinationUserId) {
        toast.error("Choose a destination user");
        return;
      }
      body.source_user_id = selectedUserId;
      body.destination_user_id = operation.destinationUserId;
    }

    setIsSubmittingOperation(true);
    try {
      await apiFetch(
        endpoint,
        {
          method: "POST",
          body: JSON.stringify(body),
        },
        { idempotent: true }
      );

      toast.success(`${operation.mode} processed`);
      setOperation((prev) => ({
        ...INITIAL_OPERATION,
        mode: prev.mode,
        destinationUserId:
          prev.mode === "transfer" ? prev.destinationUserId : undefined,
      }));

      const balanceKey = selectedUserId ? `/ledger/balance/${selectedUserId}` : null;
      const transactionsKey = transactionsEndpoint;

      await Promise.all([
        balanceKey ? mutate(balanceKey) : Promise.resolve(),
        transactionsKey ? mutate(transactionsKey) : Promise.resolve(),
        mutate("/transactions"),
        mutate("/dashboard/admin"),
      ]);
    } catch (error) {
      toast.error((error as Error).message);
    } finally {
      setIsSubmittingOperation(false);
    }
  };

  const availableDestinationUsers = useMemo(() => {
    return (usersData?.items ?? []).filter((user) => user.id !== selectedUserId);
  }, [usersData?.items, selectedUserId]);

  const canLoadMoreTransactions = (transactionsData?.total ?? 0) > (transactionsData?.items.length ?? 0);

  const handleLoadMoreTransactions = () => {
    if (canLoadMoreTransactions && !isLoadingTransactions) {
      setTransactionsLimit((limit) => limit + TRANSACTION_PAGE_SIZE);
    }
  };

  const availableBalancesByCurrency = useMemo(() => {
    const balances = new Map<string, number>();
    (balanceData?.totals ?? []).forEach((total) => {
      balances.set(total.currency, total.available_balance);
    });
    return balances;
  }, [balanceData?.totals]);

  const operationErrors = useMemo<OperationErrors>(() => {
    const errors: OperationErrors = {};

    if (!selectedUserId) {
      errors.general = "Select a user to run an operation.";
      return errors;
    }

    const rawAmount = operation.amount.trim();
    if (!rawAmount) {
      errors.amount = "Amount is required.";
    }

    const amountNumber = Number(rawAmount);
    if (!errors.amount && (Number.isNaN(amountNumber) || amountNumber <= 0)) {
      errors.amount = "Enter an amount greater than zero.";
    }

    if (!errors.amount && operation.mode !== "deposit") {
      if (!balanceData) {
        errors.general = "Balances are still loading. Please wait.";
      } else {
        const available = availableBalancesByCurrency.get(operation.currency) ?? 0;
        if (available < amountNumber) {
          errors.amount = `Insufficient ${operation.currency} balance (${available.toFixed(2)} available).`;
        }
      }
    }

    if (operation.mode === "transfer") {
      if (!operation.destinationUserId) {
        errors.destinationUserId = "Choose a destination user.";
      } else if (operation.destinationUserId === selectedUserId) {
        errors.destinationUserId = "Destination must be different from the source user.";
      }
    }

    return errors;
  }, [balanceData, operation, selectedUserId, availableBalancesByCurrency]);

  const hasOperationErrors = Boolean(
    operationErrors.general || operationErrors.amount || operationErrors.destinationUserId
  );

  const submitDisabled = hasOperationErrors || isSubmittingOperation || !selectedUserId;

  return (
    <section className="space-y-8 rounded-xl border border-zinc-200 bg-white p-8 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
      <header className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-100">User Dashboard</h2>
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            Manage user wallets, run transactions, and inspect balances.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" onClick={() => router.push("/admin/dashboard")}>
            Admin
          </Button>
          <Button variant="primary" onClick={() => setIsCreateOpen((open) => !open)}>
            {isCreateOpen ? "Close" : "New User"}
          </Button>
        </div>
      </header>

      {isCreateOpen && (
        <form
          onSubmit={handleCreateUser}
          className="grid gap-4 rounded-lg border border-dashed border-zinc-200 p-4 dark:border-zinc-700"
        >
          <div className="grid gap-2">
            <label className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
              Full name
            </label>
            <input
              type="text"
              value={newUserName}
              onChange={(event) => setNewUserName(event.target.value)}
              className="rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 dark:border-zinc-700 dark:bg-zinc-800"
              placeholder="Jane Doe"
              required
            />
          </div>
          <div className="grid gap-2">
            <label className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
              Email
            </label>
            <input
              type="email"
              value={newUserEmail}
              onChange={(event) => setNewUserEmail(event.target.value)}
              className="rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 dark:border-zinc-700 dark:bg-zinc-800"
              placeholder="jane@example.com"
              required
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="ghost" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" isLoading={isCreatingUser}>
              Create user
            </Button>
          </div>
        </form>
      )}

      <div className="grid gap-6 lg:grid-cols-[260px_1fr]">
        <aside className="space-y-3">
          <h3 className="text-sm font-semibold text-zinc-500 uppercase tracking-wide dark:text-zinc-400">
            Users
          </h3>
          <div className="space-y-2">
            {isLoadingUsers && <p className="text-sm text-zinc-500">Loading users…</p>}
            {usersError && (
              <p className="text-sm text-red-500">Failed to load users: {usersError.message}</p>
            )}
            {(usersData?.items ?? []).map((user) => (
              <button
                key={user.id}
                onClick={() => handleSelectUser(user.id)}
                className={clsx(
                  "w-full rounded-md border px-3 py-2 text-left text-sm transition-colors",
                  selectedUserId === user.id
                    ? "border-indigo-500 bg-indigo-50 text-indigo-700 dark:border-indigo-400 dark:bg-indigo-950 dark:text-indigo-100"
                    : "border-zinc-200 hover:border-indigo-300 hover:bg-indigo-50/60 dark:border-zinc-800 dark:hover:border-indigo-400"
                )}
              >
                <span className="block font-medium">{user.full_name}</span>
                <span className="block text-xs text-zinc-500 dark:text-zinc-400">
                  {user.email}
                </span>
              </button>
            ))}
            {!isLoadingUsers && (usersData?.items.length ?? 0) === 0 && (
              <p className="text-sm text-zinc-500">No users yet. Create one to get started.</p>
            )}
          </div>
        </aside>

        <div className="space-y-6">
          {selectedUser ? (
            <>
              <section className="grid gap-4 md:grid-cols-3">
                {Array.isArray(balanceData?.totals) && balanceData.totals.map((total) => (
                  <div
                    key={total.currency}
                    className="rounded-lg border border-zinc-200 bg-zinc-50 p-4 dark:border-zinc-700 dark:bg-zinc-800"
                  >
                    <p className="text-sm text-zinc-500 dark:text-zinc-400">{total.currency} Balance</p>
                    <p className="mt-2 text-2xl font-semibold text-zinc-900 dark:text-zinc-100">
                      {Number(total.balance).toFixed(2)}
                    </p>
                    <p className="text-xs text-zinc-500 dark:text-zinc-400">
                      Available: {Number(total.available_balance).toFixed(2)}
                    </p>
                  </div>
                ))}
                {(!balanceData?.totals || balanceData.totals.length === 0) && (
                  <div className="rounded-lg border border-dashed border-zinc-300 p-4 text-sm text-zinc-500 dark:border-zinc-600 dark:text-zinc-400">
                    No balances yet. Run a deposit or transfer to fund this user.
                  </div>
                )}
              </section>

              <form
                onSubmit={handleOperationSubmit}
                className="grid gap-4 rounded-lg border border-zinc-200 p-4 dark:border-zinc-700"
              >
                {operationErrors.general && (
                  <p className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800 dark:border-amber-500/40 dark:bg-amber-500/10 dark:text-amber-200">
                    {operationErrors.general}
                  </p>
                )}
                <div className="flex flex-wrap items-center gap-2">
                  {(["deposit", "transfer", "withdraw"] as OperationMode[]).map((mode) => (
                    <Button
                      key={mode}
                      type="button"
                      variant={operation.mode === mode ? "primary" : "ghost"}
                      onClick={() => setOperation((prev) => ({
                        ...INITIAL_OPERATION,
                        mode,
                        destinationUserId: prev.destinationUserId,
                      }))}
                    >
                      {mode.charAt(0).toUpperCase() + mode.slice(1)}
                    </Button>
                  ))}
                </div>

                <div className="grid gap-2 md:grid-cols-3">
                  <div className="grid gap-2">
                    <label className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
                      Amount
                    </label>
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      value={operation.amount}
                      onChange={(event) => setOperation((prev) => ({ ...prev, amount: event.target.value }))}
                      className={clsx(
                        "rounded-md border px-3 py-2 text-sm outline-none focus:ring-2 dark:bg-zinc-800",
                        operationErrors.amount
                          ? "border-red-500 focus:border-red-500 focus:ring-red-200 dark:border-red-400"
                          : "border-zinc-300 focus:border-indigo-500 focus:ring-indigo-200 dark:border-zinc-700"
                      )}
                      required
                    />
                    {operationErrors.amount && (
                      <p className="text-sm text-red-600 dark:text-red-400">{operationErrors.amount}</p>
                    )}
                  </div>
                  <div className="grid gap-2">
                    <label className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
                      Currency
                    </label>
                    <select
                      value={operation.currency}
                      onChange={(event) => setOperation((prev) => ({ ...prev, currency: event.target.value }))}
                      className="rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 dark:border-zinc-700 dark:bg-zinc-800"
                    >
                      {CURRENCIES.map((currency) => (
                        <option key={currency} value={currency}>
                          {currency}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="grid gap-2">
                    <label className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
                      Description
                    </label>
                    <input
                      type="text"
                      value={operation.description}
                      onChange={(event) => setOperation((prev) => ({
                        ...prev,
                        description: event.target.value,
                      }))}
                      className="rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 dark:border-zinc-700 dark:bg-zinc-800"
                      placeholder="Optional note"
                    />
                  </div>
                </div>

                {operation.mode === "transfer" && (
                  <div className="grid gap-2">
                    <label className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
                      Destination user
                    </label>
                    <select
                      value={operation.destinationUserId ?? ""}
                      onChange={(event) => setOperation((prev) => ({
                        ...prev,
                        destinationUserId: event.target.value || undefined,
                      }))}
                      className={clsx(
                        "rounded-md border px-3 py-2 text-sm outline-none focus:ring-2 dark:bg-zinc-800",
                        operationErrors.destinationUserId
                          ? "border-red-500 focus:border-red-500 focus:ring-red-200 dark:border-red-400"
                          : "border-zinc-300 focus:border-indigo-500 focus:ring-indigo-200 dark:border-zinc-700"
                      )}
                      required
                    >
                      <option value="">Select a user</option>
                      {availableDestinationUsers.map((user) => (
                        <option key={user.id} value={user.id}>
                          {user.full_name} ({user.email})
                        </option>
                      ))}
                    </select>
                    {operationErrors.destinationUserId && (
                      <p className="text-sm text-red-600 dark:text-red-400">
                        {operationErrors.destinationUserId}
                      </p>
                    )}
                  </div>
                )}

                <div className="flex justify-end">
                  <Button type="submit" isLoading={isSubmittingOperation} disabled={submitDisabled}>
                    Submit {operation.mode}
                  </Button>
                </div>
              </form>

              <section className="rounded-lg border border-zinc-200 dark:border-zinc-700">
                <div className="border-b border-zinc-200 bg-zinc-50 px-4 py-3 dark:border-zinc-700 dark:bg-zinc-800">
                  <h3 className="text-sm font-semibold text-zinc-600 dark:text-zinc-300">
                    Recent transactions
                  </h3>
                </div>
                <div className="divide-y divide-zinc-200 dark:divide-zinc-700">
                  {(transactionsData?.items ?? []).map((txn: Transaction) => (
                    <article key={txn.id} className="grid gap-1 px-4 py-3 text-sm md:grid-cols-4 md:items-center">
                      <div>
                        <p className="font-medium text-zinc-900 dark:text-zinc-100">
                          {txn.type.toLowerCase()}
                        </p>
                        {txn.description && (
                          <p className="text-xs text-zinc-500 dark:text-zinc-400">{txn.description}</p>
                        )}
                      </div>
                      <div className="text-zinc-600 dark:text-zinc-300">
                        {Number(txn.amount).toFixed(2)} {txn.currency}
                      </div>
                      <div className="truncate text-xs text-zinc-500 dark:text-zinc-400">
                        Ref: {txn.reference}
                      </div>
                      <div className="text-right text-xs text-zinc-500 dark:text-zinc-400">
                        {new Date(txn.occurred_at).toLocaleString()}
                      </div>
                    </article>
                  ))}
                  {(transactionsData?.items ?? []).length === 0 && (
                    <p className="px-4 py-6 text-sm text-zinc-500">
                      No transactions yet. Execute an operation to populate history.
                    </p>
                  )}
                  {isLoadingTransactions && (transactionsData?.items.length ?? 0) > 0 && (
                    <p className="px-4 py-3 text-center text-xs text-zinc-500 dark:text-zinc-400">
                      Loading more transactions…
                    </p>
                  )}
                </div>
                {canLoadMoreTransactions && (
                  <div className="border-t border-zinc-200 bg-white/70 px-4 py-3 text-center dark:border-zinc-700 dark:bg-zinc-900/40">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={handleLoadMoreTransactions}
                      isLoading={isLoadingTransactions}
                      disabled={isLoadingTransactions}
                    >
                      Load more
                    </Button>
                  </div>
                )}
              </section>
            </>
          ) : (
            <div className="flex items-center justify-center rounded-lg border border-dashed border-zinc-300 p-12 text-sm text-zinc-500 dark:border-zinc-600 dark:text-zinc-400">
              Select a user to view balances and run operations.
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
