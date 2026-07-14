import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const base = env.VITE_BASE_PATH || '/ui/';
  const apiProxy = env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:8090';

  return {
    plugins: [react(), tailwindcss()],
    base,
    build: {
      outDir: 'dist',
      emptyOutDir: true,
    },
    server: {
      port: Number(env.VITE_DEV_PORT || 5173),
      proxy: {
        '/v1': {
          target: apiProxy,
          changeOrigin: true,
        },
      },
    },
  };
});
