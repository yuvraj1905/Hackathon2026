/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    const apiBase = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
    return [
      {
        source: "/proposal/:path*",
        destination: `${apiBase}/proposal/:path*`,
      },
    ];
  },
};

export default nextConfig;
