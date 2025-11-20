"use client";

import { useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { useApi } from "@/lib/hooks";
import type { AdminSummaryResponse, TransactionListResponse } from "@/lib/types";
import { useRouter } from "next/navigation";

const currencyFormatter = new Intl.NumberFormat("en-KE", {
  style: "currency",
  currency: "KES",
  maximumFractionDigits: 0,
});

const numberFormatter = new Intl.NumberFormat("en-US");

export function AdminDashboard() {
  const {
    data: summary,
    isLoading,
    error,
    mutate,
  } = useApi<AdminSummaryResponse>("/dashboard/admin", { revalidateOnFocus: true });

  const router = useRouter();
  const [filterType, setFilterType] = useState<"all" | "deposit" | "transfer" | "withdrawal">("all");
  const [filterStartDate, setFilterStartDate] = useState("");
  const [filterEndDate, setFilterEndDate] = useState("");

  const transactionFilterEndpoint = useMemo(() => {
    const params = new URLSearchParams();
    params.set("limit", "100");
    params.set("offset", "0");
    if (filterType !== "all") {
      params.set("type", filterType);
    }
    if (filterStartDate) {
      params.set("start_date", filterStartDate);
    }
    if (filterEndDate) {
      params.set("end_date", filterEndDate);
    }
    const query = params.toString();
    return `/transactions?${query}`;
  }, [filterType, filterStartDate, filterEndDate]);

  const { data: filteredTransactions, isLoading: isLoadingFilteredTransactions } = useApi<TransactionListResponse>(
    transactionFilterEndpoint
  );

  const breakdown = useMemo(() => {
    if (!summary) return [];
    return [
      { label: "Deposits", value: summary.total_deposits, barClass: "bg-emerald-500" },
      { label: "Transfers", value: summary.total_transfers, barClass: "bg-indigo-500" },
      { label: "Withdrawals", value: summary.total_withdrawals, barClass: "bg-amber-500" },
    ];
  }, [summary]);

  const totalOperations = useMemo(() => {
    if (!summary) return 0;
    return summary.total_deposits + summary.total_transfers + summary.total_withdrawals;
  }, [summary]);

  const dailyVolumeSeries = useMemo(() => {
    const items = filteredTransactions?.items ?? [];
    if (!items.length) return [];

    const buckets = new Map<string, number>();
    items.forEach((txn) => {
      const dayKey = txn.occurred_at.slice(0, 10);
      buckets.set(dayKey, (buckets.get(dayKey) ?? 0) + Math.abs(Number(txn.amount)));
    });

    const ordered = Array.from(buckets.entries()).sort(([a], [b]) => a.localeCompare(b));
    const lastSeven = ordered.slice(-7);
    return lastSeven.map(([day, total]) => ({
      label: new Date(day).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
      value: total,
    }));
  }, [filteredTransactions?.items]);

  return (
    <section className="space-y-6 rounded-xl border border-zinc-200 bg-white p-8 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
      <header className="flex items-center justify-between">
        <div>
          <p className="text-sm uppercase tracking-wide text-zinc-500 dark:text-zinc-400">Admin Overview</p>
          <h2 className="text-2xl font-semibold text-zinc-900 dark:text-white">Platform performance</h2>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" onClick={() => router.push("/")}>Users</Button>
          <Button variant="outline" onClick={() => mutate()} isLoading={isLoading}>
            Refresh
          </Button>
        </div>
      </header>

      <div className="grid gap-3 rounded-lg border border-zinc-200 bg-zinc-50 p-4 text-sm dark:border-zinc-800 dark:bg-zinc-900/40">
        <div className="flex flex-wrap items-center gap-3 text-zinc-600 dark:text-zinc-300">
          <label className="text-xs font-semibold uppercase tracking-wide text-zinc-500">Filters</label>
          <select
            value={filterType}
            onChange={(event) => setFilterType(event.target.value as "all" | "deposit" | "transfer" | "withdrawal")}
            className="rounded border border-zinc-300 bg-white px-2 py-1 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-200 dark:border-zinc-700 dark:bg-zinc-900"
          >
            <option value="all">All types</option>
            <option value="deposit">Deposits</option>
            <option value="transfer">Transfers</option>
            <option value="withdrawal">Withdrawals</option>
          </select>
          <input
            type="date"
            value={filterStartDate}
            onChange={(event) => setFilterStartDate(event.target.value)}
            className="rounded border border-zinc-300 bg-white px-2 py-1 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-200 dark:border-zinc-700 dark:bg-zinc-900"
            placeholder="Start"
          />
          <span className="text-xs text-zinc-400">→</span>
          <input
            type="date"
            value={filterEndDate}
            onChange={(event) => setFilterEndDate(event.target.value)}
            className="rounded border border-zinc-300 bg-white px-2 py-1 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-200 dark:border-zinc-700 dark:bg-zinc-900"
            placeholder="End"
          />
          <Button variant="ghost" onClick={() => { setFilterType("all"); setFilterStartDate(""); setFilterEndDate(""); }}>
            Clear
          </Button>
        </div>
      </div>

      {error && (
        <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-500/40 dark:bg-red-500/10 dark:text-red-200">
          Failed to load summary: {error.message}
        </p>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-6">
        <KpiCard
          label="Total users"
          value={summary ? numberFormatter.format(summary.total_users) : "—"}
          helper="Active wallet holders"
          isLoading={isLoading}
        />
        <KpiCard
          label="Wallet value"
          value={summary ? currencyFormatter.format(Number(summary.total_wallet_value)) : "—"}
          helper="All accounts combined"
          isLoading={isLoading}
        />
        <KpiCard
          label="Transfers processed"
          value={summary ? numberFormatter.format(summary.total_transfers) : "—"}
          helper="Inter-user movements"
          isLoading={isLoading}
        />
        <KpiCard
          label="Deposits processed"
          value={summary ? numberFormatter.format(summary.total_deposits) : "—"}
          helper="Incoming funds"
          isLoading={isLoading}
        />
        <KpiCard
          label="Deposit volume"
          value={summary ? currencyFormatter.format(Number(summary.total_deposits_amount)) : "—"}
          helper="Total deposited"
          isLoading={isLoading}
        />
        <KpiCard
          label="Transfer volume"
          value={summary ? currencyFormatter.format(Number(summary.total_transfers_amount)) : "—"}
          helper="Total moved"
          isLoading={isLoading}
        />
        <KpiCard
          label="Withdrawal volume"
          value={summary ? currencyFormatter.format(Number(summary.total_withdrawals_amount)) : "—"}
          helper="Cash out"
          isLoading={isLoading}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <TransactionMixCard
          breakdown={breakdown}
          totalOperations={totalOperations}
          isLoading={isLoading}
        />
        <VolumeChartCard
          points={dailyVolumeSeries}
          isLoading={isLoadingFilteredTransactions}
          currencyFormatter={currencyFormatter}
        />
      </div>
    </section>
  );
}

interface KpiCardProps {
  label: string;
  value: string;
  helper?: string;
  isLoading?: boolean;
}

function KpiCard({ label, value, helper, isLoading }: KpiCardProps) {
  return (
    <article className="rounded-lg border border-zinc-200 p-4 dark:border-zinc-800">
      <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">{label}</p>
      <p className="mt-3 text-2xl font-bold text-zinc-900 dark:text-white">
        {isLoading ? <span className="text-sm text-zinc-500">Loading…</span> : value}
      </p>
      {helper && <p className="text-xs text-zinc-500 dark:text-zinc-400">{helper}</p>}
    </article>
  );
}

interface TransactionMixCardProps {
  breakdown: Array<{ label: string; value: number; barClass: string }>;
  totalOperations: number;
  isLoading?: boolean;
}

function TransactionMixCard({ breakdown, totalOperations, isLoading }: TransactionMixCardProps) {
  return (
    <div className="rounded-lg border border-zinc-200 dark:border-zinc-800">
      <div className="border-b border-zinc-200 bg-zinc-50 px-4 py-3 dark:border-zinc-800 dark:bg-zinc-800/40">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-zinc-600 dark:text-zinc-300">
          Transaction mix
        </h3>
        <p className="text-xs text-zinc-500 dark:text-zinc-400">Breakdown of processed operations</p>
      </div>
      <div className="space-y-2 px-4 py-5">
        {breakdown.length === 0 && !isLoading && (
          <p className="text-sm text-zinc-500">No data yet. Execute transactions to populate stats.</p>
        )}
        {breakdown.map((item) => (
          <div key={item.label} className="space-y-1">
            <div className="flex items-center justify-between text-sm">
              <span className="text-zinc-600 dark:text-zinc-300">{item.label}</span>
              <span className="font-semibold text-zinc-900 dark:text-white">
                {numberFormatter.format(item.value)}
              </span>
            </div>
            <div className="h-2 rounded-full bg-zinc-100 dark:bg-zinc-800">
              <div
                className={`h-full rounded-full transition-all ${item.barClass}`}
                style={{ width: totalOperations ? `${(item.value / totalOperations) * 100}%` : "0%" }}
              />
            </div>
          </div>
        ))}
        {isLoading && <p className="text-sm text-zinc-500">Loading breakdown…</p>}
        <TransactionBarChart breakdown={breakdown} totalOperations={totalOperations} />
      </div>
    </div>
  );
}

interface TransactionBarChartProps {
  breakdown: Array<{ label: string; value: number; barClass: string }>;
  totalOperations: number;
}

function TransactionBarChart({ breakdown, totalOperations }: TransactionBarChartProps) {
  if (!breakdown.length) {
    return null;
  }

  return (
    <div className="mt-4 flex min-h-[140px] items-end gap-3">
      {breakdown.map((item) => {
        const relativeHeight = totalOperations ? (item.value / totalOperations) * 100 : 0;
        const height = Math.max(relativeHeight, 10);
        return (
          <div key={item.label} className="flex-1 text-center">
            <div
              className={`${item.barClass} rounded-t-md`}
              style={{ height: `${height}%`, minHeight: "24px" }}
            />
            <p className="mt-2 text-xs font-medium text-zinc-600 dark:text-zinc-300">{item.label}</p>
          </div>
        );
      })}
    </div>
  );
}

interface VolumeChartCardProps {
  points: Array<{ label: string; value: number }>;
  isLoading?: boolean;
  currencyFormatter: Intl.NumberFormat;
}

function VolumeChartCard({ points, isLoading, currencyFormatter }: VolumeChartCardProps) {
  const values = points.map((point) => point.value);
  const max = Math.max(...values, 1);
  const normalizedPoints = points.map((point, index) => {
    const x = points.length > 1 ? (index / (points.length - 1)) * 100 : 50;
    const y = 100 - (point.value / max) * 80 - 10;
    return `${x},${Math.max(Math.min(y, 100), 0)}`;
  });

  const latest = points.at(-1)?.value ?? 0;
  const first = points[0]?.value ?? latest;
  const delta = latest - first;
  const deltaPct = first ? (delta / first) * 100 : 0;

  return (
    <div className="rounded-lg border border-zinc-200 dark:border-zinc-800">
      <div className="border-b border-zinc-200 bg-zinc-50 px-4 py-3 dark:border-zinc-800 dark:bg-zinc-800/40">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-zinc-600 dark:text-zinc-300">
          Daily volume
        </h3>
        <p className="text-xs text-zinc-500 dark:text-zinc-400">Sum of processed amounts (last 7 days)</p>
      </div>
      <div className="space-y-4 px-4 py-5">
        {(!points.length || isLoading) && (
          <p className="text-sm text-zinc-500">{isLoading ? "Loading chart…" : "Not enough data yet."}</p>
        )}
        {points.length > 0 && !isLoading && (
          <div className="space-y-3">
            <div className="flex items-baseline gap-3">
              <p className="text-3xl font-semibold text-zinc-900 dark:text-white">
                {currencyFormatter.format(latest)}
              </p>
              <span
                className={delta >= 0 ? "text-sm font-medium text-emerald-600" : "text-sm font-medium text-red-500"}
              >
                {delta >= 0 ? "▲" : "▼"} {deltaPct.toFixed(1)}%
              </span>
            </div>
            <svg viewBox="0 0 100 100" className="h-40 w-full text-indigo-500">
              <polyline
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                points={normalizedPoints.join(" ")}
              />
              {points.map((point, index) => {
                const x = points.length > 1 ? (index / (points.length - 1)) * 100 : 50;
                const y = 100 - (point.value / max) * 80 - 10;
                return <circle key={point.label} cx={x} cy={Math.max(Math.min(y, 100), 0)} r={1.5} fill="currentColor" />;
              })}
            </svg>
            <div className="flex justify-between text-xs text-zinc-500 dark:text-zinc-400">
              {points.map((point) => (
                <span key={point.label}>{point.label}</span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
