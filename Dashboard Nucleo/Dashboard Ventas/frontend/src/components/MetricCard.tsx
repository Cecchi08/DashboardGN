type MetricCardProps = { label: string; value: string; detail: string };

export default function MetricCard({ label, value, detail }: MetricCardProps) {
  return <article className="kpi"><span>{label}</span><strong>{value}</strong><small>{detail}</small></article>;
}
