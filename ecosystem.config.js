module.exports = {
  apps: [
    {
      name: 'tiktok-uploader',
      script: 'dist/server.js',
      cwd: __dirname,
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production',
        PORT: 3000,
      },
    },
    {
      name: 'tiktok-worker',
      script: 'dist/worker.js',
      cwd: __dirname,
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '2G',
      env: {
        NODE_ENV: 'production',
      },
    },
    {
      name: 'tiktok-stats-worker',
      script: 'dist/workers/stats.worker.js',
      cwd: __dirname,
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production',
      },
    },
    {
      name: 'tiktok-uploader-dev',
      script: './node_modules/ts-node/dist/bin.js',
      args: 'src/server.ts',
      cwd: __dirname,
      instances: 1,
      autorestart: true,
      watch: false,
      env: {
        NODE_ENV: 'development',
        PORT: 3000,
      },
    },
    {
      name: 'tiktok-worker-dev',
      script: './node_modules/ts-node/dist/bin.js',
      args: 'src/worker.ts',
      cwd: __dirname,
      instances: 1,
      autorestart: true,
      watch: false,
      env: {
        NODE_ENV: 'development',
      },
    },
    {
      name: 'tiktok-stats-worker-dev',
      script: './node_modules/ts-node/dist/bin.js',
      args: 'src/workers/stats.worker.ts',
      cwd: __dirname,
      instances: 1,
      autorestart: true,
      watch: false,
      env: {
        NODE_ENV: 'development',
      },
    },
  ],
};

