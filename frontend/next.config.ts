import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  reactStrictMode: true,
  poweredByHeader: false,
  images: {
    remotePatterns: [],
  },
  experimental: {
    optimizePackageImports: ["@phosphor-icons/react", "motion"],
  },
};

export default nextConfig;
