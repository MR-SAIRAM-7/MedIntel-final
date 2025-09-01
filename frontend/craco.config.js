// Load configuration from environment or config file
const path = require('path');

// Environment variable overrides
const config = {
  disableHotReload: process.env.DISABLE_HOT_RELOAD === 'true',
};

module.exports = {
  webpack: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
    configure: (webpackConfig) => {
      // Disable hot reload completely if environment variable is set
      if (config.disableHotReload) {
        // Remove hot reload related plugins
        webpackConfig.plugins = webpackConfig.plugins.filter(plugin => {
          return !(plugin.constructor.name === 'HotModuleReplacementPlugin');
        });

        // Disable watch mode
        webpackConfig.watch = false;
        webpackConfig.watchOptions = {
          ignored: /.*/, // Ignore all files
        };
      } else {
        // Add ignored patterns to reduce watched directories
        webpackConfig.watchOptions = {
          ...webpackConfig.watchOptions,
          ignored: [
            '**/node_modules/**',
            '**/.git/**',
            '**/build/**',
            '**/dist/**',
            '**/coverage/**',
            '**/public/**',
          ],
        };
      }

      return webpackConfig;
    },
  },

  // 👇 Add this for proxying API calls in dev
  devServer: {
    proxy: {
      '/api': {
        target: process.env.REACT_APP_BACKEND_URL,
        changeOrigin: true,
        secure: false,
      },
    },
    client: {
      webSocketURL: {
        protocol: "ws",          // change from wss → ws for local dev
        hostname: "localhost",   // keep localhost
        port: 8001,              // match your backend port
        pathname: "/ws",         // keep /ws if your backend handles that
      },
    },
  },

};
