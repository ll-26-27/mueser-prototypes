import Link from "next/link";

export default function NotFound() {
  return <main className="tl-logpage"><h1>No such node</h1><p>Nothing in the set has that id. <Link href="/">Back to the start</Link>.</p></main>;
}
