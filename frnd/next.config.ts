import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'https://akim.larek.tech/api/:path*', // Unified Akim Backend
      },
    ];
  },
};

export default nextConfig;
