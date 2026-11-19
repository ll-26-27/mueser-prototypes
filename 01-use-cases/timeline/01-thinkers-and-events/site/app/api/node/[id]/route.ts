import { NextResponse } from "next/server";
import { bundle } from "@/lib/data";

export const dynamic = "force-dynamic";

export async function GET(_req: Request, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  const b = bundle(id);
  if (!b) return NextResponse.json({ error: "no such node" }, { status: 404 });
  return NextResponse.json(b);
}
