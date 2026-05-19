/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",
  reactStrictMode: true,
  // Static export uses unoptimized images
  images: { unoptimized: true },
  trailingSlash: false,
};

export default nextConfig;
