# Barn Management - Mobile App

React-based mobile-first progressive web application for barn management.

## Quick Start

1. Copy environment variables:
   ```bash
   cp .env.example .env
   ```

2. Update `.env` with your configuration:
   - `VITE_AUTH_URL`: Your PropelAuth domain
   - `VITE_API_URL`: Backend API URL (default: http://localhost:8002)

3. Install dependencies:
   ```bash
   npm install
   ```

4. Start development server:
   ```bash
   npm run dev
   ```

5. Open http://localhost:3000 in your browser

## Features

- Mobile-first responsive design
- Progressive Web App (PWA) ready
- PropelAuth authentication
- React Router for navigation
- Tailwind CSS for styling
- TypeScript for type safety

## Development

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Deployment

This app is designed to be deployed alongside the existing Streamlit frontend as part of a hybrid architecture.