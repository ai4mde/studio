import * as React from "react";
import { ActionFunctionArgs, json, redirect } from "@remix-run/node";
import { useActionData } from "@remix-run/react";
import { StrategyForm } from "../components/strategy-form";

interface ActionData {
  error?: string;
  fields?: {
    name: string;
    description: string;
    prompt: string;
  };
}

export async function action({ request }: ActionFunctionArgs) {
  const formData = await request.formData();
  const name = formData.get("name") as string;
  const description = formData.get("description") as string;
  const prompt = formData.get("prompt") as string;

  if (!name || !prompt) {
    return json<ActionData>({
      error: "Name and prompt are required",
      fields: { name, description, prompt },
    });
  }

  try {
    // TODO: Add API call to create strategy
    // const response = await createStrategy({ name, description, prompt });
    return redirect("/strategies");
  } catch (error) {
    console.error("Failed to create strategy:", error);
    return json<ActionData>({
      error: "Failed to create strategy. Please try again.",
      fields: { name, description, prompt },
    });
  }
}

export default function NewStrategy() {
  const actionData = useActionData<typeof action>();

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 p-4">
      <StrategyForm
        error={actionData?.error}
        defaultValues={actionData?.fields}
      />
    </div>
  );
} 