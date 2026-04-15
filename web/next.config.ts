import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  serverExternalPackages: ["duckdb", "duckdb-async", "@duckdb/node-api"],
};

export default nextConfig;
