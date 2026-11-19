import { redirect } from "next/navigation";
import { defaultNode } from "@/lib/data";

export const dynamic = "force-dynamic";

export default function Home() {
  redirect(`/node/${defaultNode()}`);
}
