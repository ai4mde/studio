import type { ActionFunctionArgs } from "@remix-run/node";
import { destroySession } from "../services/session.server";

export async function action({ request }: ActionFunctionArgs) {
  return await destroySession(request);
}

export default function Logout() {
  return null;
}
