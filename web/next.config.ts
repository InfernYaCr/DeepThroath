import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  serverExternalPackages: ["duckdb", "duckdb-async", "@duckdb/node-api"],
  output: 'standalone',
};

export default nextConfig;
