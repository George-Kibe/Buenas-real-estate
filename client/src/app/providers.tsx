"use client";

import { useEffect, useState } from "react";
import { Provider } from "react-redux";
import { ToastContainer } from "react-toastify";

import { makeStore, type AppStore } from "@/store";
import { loadUser } from "@/store/authSlice";

function SessionLoader({ store }: { store: AppStore }) {
  useEffect(() => {
    // Restore the session from the stored JWT once the client has mounted.
    void store.dispatch(loadUser());
  }, [store]);
  return null;
}

export default function Providers({ children }: { children: React.ReactNode }) {
  // A lazy initialiser builds the store once per browser session, and keeps
  // StrictMode's double render from creating a second one.
  const [store] = useState<AppStore>(makeStore);

  return (
    <Provider store={store}>
      <SessionLoader store={store} />
      {children}
      <ToastContainer position="top-right" autoClose={4000} newestOnTop theme="colored" />
    </Provider>
  );
}
