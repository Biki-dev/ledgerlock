import {
  useMemo,
  useState,
  type ReactNode
} from "react";

import api from "../services/api";

import type {
  User,
  LoginResponse
} from "../types";
import { AuthContext } from "./authContext";

export function AuthProvider({
  children
}: {
  children: ReactNode;
}) {

  const [user, setUser] = useState<User | null>(() => {
    try {
      const token = localStorage.getItem("ledgerlock_token");
      const saved = localStorage.getItem("ledgerlock_user");

      if (!token || !saved) return null;

      return saved ? JSON.parse(saved) : null;
    } catch {
      localStorage.removeItem("ledgerlock_token");
      localStorage.removeItem("ledgerlock_user");
      return null;
    }
  });

  const [loading] = useState(false);

  async function login(
    email: string,
    password: string
  ) {

    const { data } = await api.post<LoginResponse>(
      "/api/auth/login",
      {
        email,
        password
      }
    );

    localStorage.setItem(
      "ledgerlock_token",
      data.access_token
    );

    localStorage.setItem(
      "ledgerlock_user",
      JSON.stringify(data.user)
    );

    setUser(data.user);
  }

  function logout() {
    localStorage.removeItem("ledgerlock_token");
    localStorage.removeItem("ledgerlock_user");

    setUser(null);

    window.location.href = "/login";
  }

  const value = useMemo(
    () => ({
      user,
      loading,
      login,
      logout
    }),
    [user, loading]
  );

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}