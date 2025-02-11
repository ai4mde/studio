import { useRouteLoaderData } from "@remix-run/react";
import type { CustomUser } from "../types/auth.types";

export function useOptionalUser(): CustomUser | undefined {
  const data = useRouteLoaderData("root") as { user: CustomUser | undefined };
  return data?.user;
}

export function useUser(): CustomUser {
  const user = useOptionalUser();
  if (!user) {
    throw new Error(
      "No user found in root loader, but user is required by useUser. If user is optional, try useOptionalUser instead."
    );
  }
  return user;
} 