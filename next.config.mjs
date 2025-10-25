import withBundleAnalyzer from '@next/bundle-analyzer'

const bundleAnalyzerConfig = withBundleAnalyzer({
  enabled: process.env.ANALYZE === 'true',
})

const nextConfig = {
  reactStrictMode: true,

  // Performance optimizations
  compress: true,
  poweredByHeader: false,

  // Standlone output for production deployment
  output: 'standalone',

  // Disable static optimization for all pages to avoid vendor compatibility issues
  generateBuildId: async () => {
    return 'build-' + Date.now()
  },

  // Image optimization
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**',
      },
      {
        protocol: 'http',
        hostname: 'localhost',
      },
    ],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },

  // Security headers
  async headers() {
    return [
      {
        // Apply to all routes
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=()',
          },
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on',
          },
          // Cache control for better performance
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
      {
        // Additional security for API routes
        source: '/api/(.*)',
        headers: [
          {
            key: 'X-RateLimit-Limit',
            value: '100', // Requests per minute
          },
          {
            key: 'X-RateLimit-Reset',
            value: (Date.now() + 60000).toString(),
          },
        ],
      },
    ]
  },

  // Turbopack configuration
  turbopack: {
    // Basic Turbopack config - can be expanded as needed
  },
};

export default bundleAnalyzerConfig(nextConfig);
