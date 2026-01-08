# GLP-1 Regulatory Intelligence Platform - Frontend

**Modern, Industry-Grade Web Interface for Drug Label Analysis**

## 🎨 Features

- **Dashboard**: Overview of all GLP-1 drug labels with search and filtering
- **Analytics**: Platform-wide statistics and insights
- **Comparison Workspace**: Side-by-side drug label comparison
- **Reports**: Manage and access saved analysis reports
- **Version Checker**: Manual trigger for label version monitoring
- **Chat Interface**: AI-powered Q&A about drug labels

## 🛠️ Tech Stack

- **React 18** - UI Library
- **TypeScript** - Type Safety
- **Vite** - Build Tool
- **Tailwind CSS** - Styling
- **Radix UI** - Accessible Components
- **Zustand** - State Management
- **React Router** - Navigation
- **Axios** - API Client
- **Recharts** - Data Visualization

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Backend API running on http://localhost:8000

### Installation

```bash
# Run the setup script
./setup.sh

# Or manually:
npm install
```

### Development

```bash
# Start development server
npm run dev

# Open http://localhost:3000
```

### Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── layout/          # Layout components (Sidebar, Header)
│   │   ├── ui/              # Base UI components
│   │   └── features/        # Feature-specific components
│   ├── pages/               # Page components
│   │   ├── Dashboard.tsx
│   │   ├── Analytics.tsx
│   │   ├── Comparison.tsx
│   │   ├── Reports.tsx
│   │   └── VersionChecker.tsx
│   ├── hooks/               # Custom React hooks
│   ├── store/               # Zustand stores
│   ├── services/            # API services
│   ├── types/               # TypeScript types
│   └── utils/               # Utility functions
├── public/                  # Static assets
└── index.html              # Entry HTML
```

## 🎯 Key Features

### Dark Mode
- Toggle between light and dark themes
- Persists user preference
- Smooth transitions

### Responsive Design
- Mobile-first approach
- Collapsible sidebar
- Adaptive layouts

### Performance
- Code splitting
- Lazy loading
- Optimized bundles

## 🔌 API Integration

All API calls are proxied through Vite:
- Development: http://localhost:3000/api → http://localhost:8000/api
- Production: Configure in environment variables

## 📝 Environment Variables

Create `.env` file:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## 🎨 Design System

### Colors
- **Primary**: Blue (#3B82F6)
- **Secondary**: Gray
- **Success**: Green
- **Warning**: Yellow
- **Error**: Red

### Typography
- **Font Family**: Inter, system-ui
- **Sizes**: Tailwind default scale

## 🧪 Testing

```bash
# Coming soon
npm run test
```

## 📦 Build Output

```bash
dist/
├── assets/              # Bundled JS/CSS
├── index.html           # Entry point
└── vite.svg            # Favicon
```

## 🚢 Deployment

1. Build the project: `npm run build`
2. Deploy `dist/` folder to your hosting service
3. Configure environment variables for production API

## 🤝 Contributing

1. Follow TypeScript strict mode
2. Use Tailwind CSS for styling
3. Maintain component reusability
4. Write meaningful commit messages

## 📄 License

Proprietary - Company Internal Use Only

## 👥 Team

Built for showcasing to your company leadership

---

**Built with ❤️ using React + TypeScript + Vite**
