import '@testing-library/jest-dom'

// Mock redux-persist
jest.mock('redux-persist', () => ({
  persistStore: jest.fn(() => ({})),
  persistReducer: jest.fn((_, reducer) => reducer),
}))

// Mock redux-persist/integration/react
jest.mock('redux-persist/integration/react', () => ({
  PersistGate: ({ children }: { children: React.ReactNode }) => children,
}))

// Mock redux-persist/lib/storage
jest.mock('redux-persist/lib/storage', () => ({
  default: {
    getItem: jest.fn(() => Promise.resolve(null)),
    setItem: jest.fn(() => Promise.resolve()),
    removeItem: jest.fn(() => Promise.resolve()),
  },
}))

// Mock fetch for RTK Query
global.fetch = jest.fn(() =>
  Promise.resolve({
    json: () => Promise.resolve({}),
    ok: true,
    status: 200,
  })
) as jest.Mock