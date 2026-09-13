import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  images: {
    remotePatterns: [
      // Django serves uploaded photos from /mediafiles/ behind nginx.
      { protocol: "http", hostname: "localhost", port: "8080", pathname: "/mediafiles/**" },
      { protocol: "http", hostname: "api", port: "8000", pathname: "/mediafiles/**" },
    ],
  },
};

export default nextConfig;
