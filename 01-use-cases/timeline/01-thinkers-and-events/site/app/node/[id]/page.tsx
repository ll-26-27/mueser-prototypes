import { notFound } from "next/navigation";
import { bundle } from "@/lib/data";
import { NodeView } from "@/components/NodeView";

export const dynamic = "force-dynamic";

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const b = bundle(id);
  return { title: b ? `${b.node.label} · Thinkers and events` : "Thinkers and events" };
}

export default async function NodePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const b = bundle(id);
  if (!b) notFound();
  return <NodeView bundle={b} />;
}
