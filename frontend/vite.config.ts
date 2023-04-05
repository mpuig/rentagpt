import {defineConfig} from 'vite'
import react from '@vitejs/plugin-react'
import cssInjectedByJsPlugin from "vite-plugin-css-injected-by-js";

export default defineConfig({
    plugins: [
        react(),
        cssInjectedByJsPlugin(),
    ],
    build: {
        cssCodeSplit: false,
        rollupOptions: {
            input: {
                app: './src/main.tsx',
            },
        },
    },
})
