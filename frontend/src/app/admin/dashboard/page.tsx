import { AdminDashboard } from "@/components/admin-dashboard";

export default function AdminDashboardPage() {
  return (
    <div className="min-h-screen bg-slate-50 py-12 font-sans text-slate-900 dark:bg-zinc-950 dark:text-zinc-50">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-6">
        <header className="space-y-2">
          <p className="text-xs uppercase tracking-[0.4em] text-indigo-500">Admin Control</p>
          <h1 className="text-4xl font-semibold text-slate-900 dark:text-white">Platform dashboard</h1>
          <p className="text-base text-slate-600 dark:text-zinc-400">
            Monitor aggregate wallet value, user growth, and operation mix in real time.
          </p>
        </header>
        <AdminDashboard />
      </div>
    </div>
  );
}
