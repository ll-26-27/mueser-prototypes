import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // The data file and the log live in the case folder beside this site; nothing is fetched at build time.
  reactStrictMode: true,
  images: { unoptimized: true },
  agentRules: false,
  allowedDevOrigins: ["127.0.0.1"],
};

export default nextConfig;
