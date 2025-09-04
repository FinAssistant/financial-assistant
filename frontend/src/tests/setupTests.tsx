import "@testing-library/jest-dom";
import React from "react";
import { render } from "@testing-library/react";
import { Provider } from "react-redux";
import { MemoryRouter } from "react-router-dom";
import { ThemeProvider } from "styled-components";
import { configureStore } from "@reduxjs/toolkit";
import { persistStore } from "redux-persist";
import { PersistGate } from "redux-persist/integration/react";
import { baseApi } from "../store/api/baseApi";
import authReducer from "../store/slices/authSlice";
import conversationReducer from "../store/slices/conversationSlice";
import { theme } from "../styles/theme";
import { RootState } from "../store";

// Mock redux-persist
jest.mock("redux-persist", () => ({
  persistStore: jest.fn(() => ({})),
  persistReducer: jest.fn((_, reducer) => reducer),
}));

// Mock redux-persist/integration/react
jest.mock("redux-persist/integration/react", () => ({
  PersistGate: ({ children }: { children: React.ReactNode }) => children,
}));

// Mock redux-persist/lib/storage
jest.mock("redux-persist/lib/storage", () => ({
  default: {
    getItem: jest.fn(() => Promise.resolve(null)),
    setItem: jest.fn(() => Promise.resolve()),
    removeItem: jest.fn(() => Promise.resolve()),
  },
}));

// Mock fetch for RTK Query
global.fetch = jest.fn(() =>
  Promise.resolve({
    json: () => Promise.resolve({}),
    ok: true,
    status: 200,
  })
) as jest.Mock;

// Common test store creation
export const createTestStore = (initialState: Partial<RootState> = {}) => {
  return configureStore({
    reducer: {
      auth: authReducer,
      conversation: conversationReducer,
      [baseApi.reducerPath]: baseApi.reducer,
    },
    preloadedState: {
      auth: {
        user: null,
        token: null,
        isAuthenticated: false,
        loading: false,
        ...initialState.auth,
      },
      conversation: initialState.conversation,
    },
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware({
        serializableCheck: false,
      }).concat(baseApi.middleware),
  });
};

// Common render function with all providers using MemoryRouter
export const renderWithProviders = (
  component: React.ReactElement,
  initialState = {},
  initialRoute: string | { pathname: string; state?: unknown } = "/"
) => {
  const store = createTestStore(initialState);
  const persistor = persistStore(store);

  return render(
    <Provider store={store}>
      <PersistGate loading={<div>Loading...</div>} persistor={persistor}>
        <MemoryRouter
          future={{
            v7_startTransition: true,
            v7_relativeSplatPath: true,
          }}
          initialEntries={[initialRoute]}
        >
          <ThemeProvider theme={theme}>{component}</ThemeProvider>
        </MemoryRouter>
      </PersistGate>
    </Provider>
  );
};
