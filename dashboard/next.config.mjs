/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  // Allow CORS for API requests during development
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.NEXT_PUBLIC_API_URL 
          ? `${process.env.NEXT_PUBLIC_API_URL}/api/:path*`
          : 'http://localhost:8000/api/:path*',
      },
    ];
  },
};

export default nextConfig;
