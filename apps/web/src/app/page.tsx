import { ReceiptChip } from "@/components/ReceiptChip";

export default function HomePage() {
  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold text-slate-50">Home</h1>
      <p className="text-slate-400">Coming soon</p>
      <div>
        <ReceiptChip hash="a1b2c3d4e5f6a1b2c3d4" />
      </div>
    </section>
  );
}
