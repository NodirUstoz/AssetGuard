/**
 * API service for authentication endpoints.
 */
import apiClient, { clearTokens, setTokens } from "./client";

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface UserProfile {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: "admin" | "manager" | "technician" | "viewer";
  phone: string;
  avatar: string | null;
  department: string | null;
  department_name: string | null;
  receive_notifications: boolean;
  is_active: boolean;
  last_login: string | null;
}

export const authApi = {
  async login(credentials: LoginCredentials): Promise<UserProfile> {
    const tokenResponse = await apiClient.post<AuthTokens>(
      "/auth/login/",
      credentials,
    );
    setTokens(tokenResponse.data.access, tokenResponse.data.refresh);

    const profileResponse = await apiClient.get<UserProfile>("/accounts/users/me/");
    return profileResponse.data;
  },

  async logout(): Promise<void> {
    try {
      const refresh = localStorage.getItem("assetguard_refresh_token");
      if (refresh) {
        await apiClient.post("/auth/logout/", { refresh });
      }
    } finally {
      clearTokens();
    }
  },

  async getProfile(): Promise<UserProfile> {
    const response = await apiClient.get<UserProfile>("/accounts/users/me/");
    return response.data;
  },

  async updateProfile(
    data: Partial<Pick<UserProfile, "first_name" | "last_name" | "phone" | "receive_notifications">>,
  ): Promise<UserProfile> {
    const response = await apiClient.patch<UserProfile>(
      "/accounts/users/me/",
      data,
    );
    return response.data;
  },

  async changePassword(data: {
    old_password: string;
    new_password: string;
    new_password_confirm: string;
  }): Promise<void> {
    await apiClient.post("/accounts/users/change_password/", data);
  },
};
