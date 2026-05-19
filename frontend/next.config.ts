import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  reactStrictMode: true,
  // Static export uses unoptimized images
  images: { unoptimized: true },
  // We serve from FastAPI at the same origin; no trailing slash quirks
  trailingSlash: false,
};

export default nextConfig;
