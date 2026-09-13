import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";

import { describeError } from "@/lib/api";
import * as endpoints from "@/lib/endpoints";
import { clearTokens, getAccessToken, storeTokens } from "@/lib/tokens";
import type { RegisterPayload, User } from "@/lib/types";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  status: "idle" | "loading" | "succeeded" | "failed";
  error: string | null;
}

const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  status: "idle",
  error: null,
};

export const login = createAsyncThunk<
  User,
  { email: string; password: string },
  { rejectValue: string }
>("auth/login", async (credentials, { rejectWithValue }) => {
  try {
    const tokens = await endpoints.login(credentials.email, credentials.password);
    storeTokens(tokens.access, tokens.refresh);
    return await endpoints.currentUser();
  } catch (error) {
    clearTokens();
    return rejectWithValue(describeError(error, "Unable to sign in"));
  }
});

export const register = createAsyncThunk<void, RegisterPayload, { rejectValue: string }>(
  "auth/register",
  async (payload, { rejectWithValue }) => {
    try {
      await endpoints.register(payload);
    } catch (error) {
      return rejectWithValue(describeError(error, "Unable to create the account"));
    }
  },
);

/** Rehydrates the session from a stored token on first mount. */
export const loadUser = createAsyncThunk<User | null, void, { rejectValue: string }>(
  "auth/loadUser",
  async (_, { rejectWithValue }) => {
    if (!getAccessToken()) return null;
    try {
      return await endpoints.currentUser();
    } catch (error) {
      clearTokens();
      return rejectWithValue(describeError(error, "Session expired"));
    }
  },
);

const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    logout(state) {
      clearTokens();
      state.user = null;
      state.isAuthenticated = false;
      state.status = "idle";
      state.error = null;
    },
    reset(state) {
      state.status = "idle";
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(login.pending, (state) => {
        state.status = "loading";
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action) => {
        state.status = "succeeded";
        state.user = action.payload;
        state.isAuthenticated = true;
      })
      .addCase(login.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.payload ?? "Unable to sign in";
      })
      .addCase(register.pending, (state) => {
        state.status = "loading";
        state.error = null;
      })
      .addCase(register.fulfilled, (state) => {
        state.status = "succeeded";
      })
      .addCase(register.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.payload ?? "Unable to create the account";
      })
      .addCase(loadUser.fulfilled, (state, action) => {
        state.user = action.payload;
        state.isAuthenticated = Boolean(action.payload);
      })
      .addCase(loadUser.rejected, (state) => {
        state.user = null;
        state.isAuthenticated = false;
      });
  },
});

export const { logout, reset } = authSlice.actions;
export default authSlice.reducer;
