import { UserDashboard } from "@/components/user-dashboard";

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-zinc-50 via-white to-zinc-100 py-16 font-sans text-zinc-900 dark:from-zinc-950 dark:via-zinc-900 dark:to-zinc-900 dark:text-zinc-100">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-12 px-6">
        <header className="space-y-4 text-center lg:text-left">
          <p className="text-xs uppercase tracking-[0.5em] text-indigo-500">User Operations</p>
          <h1 className="text-4xl font-semibold leading-tight text-zinc-900 dark:text-white">
            Manage wallets, execute transfers, and keep balances healthy.
          </h1>
          <p className="text-base text-zinc-600 dark:text-zinc-400 lg:max-w-2xl">
            The user dashboard provides a fast way to spin up new customers, inspect their multi-currency balances, and run secure deposits, transfers, and withdrawals with built-in validation.
          </p>
        </header>

        <UserDashboard />
      </div>
    </div>
  );
}
