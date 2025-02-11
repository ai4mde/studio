import {
  useRouteLoaderData
} from "/build/_shared/chunk-5SMQHKI5.js";
import {
  createHotContext
} from "/build/_shared/chunk-YJEMTN56.js";

// app/hooks/use-user.ts
if (import.meta) {
  import.meta.hot = createHotContext(
    //@ts-expect-error
    "app/hooks/use-user.ts"
  );
  import.meta.hot.lastModified = "1738662837903.6753";
}
function useOptionalUser() {
  const data = useRouteLoaderData("root");
  return data?.user;
}
function useUser() {
  const user = useOptionalUser();
  if (!user) {
    throw new Error(
      "No user found in root loader, but user is required by useUser. If user is optional, try useOptionalUser instead."
    );
  }
  return user;
}

export {
  useOptionalUser,
  useUser
};
//# sourceMappingURL=/build/_shared/chunk-IVLWEOHB.js.map
