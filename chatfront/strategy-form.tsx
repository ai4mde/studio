import * as React from "react";
import { Form } from "@remix-run/react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Label } from "./ui/label";
import { Input } from "./ui/input";
import { Button } from "./ui/button";

interface StrategyFormProps {
  error?: string;
  defaultValues?: {
    name?: string;
    description?: string;
    prompt?: string;
  };
}

export function StrategyForm({ error, defaultValues = {} }: StrategyFormProps) {
  return (
    <Card className="w-full max-w-2xl">
      <CardHeader>
        <CardTitle>Create Strategy</CardTitle>
        <CardDescription>Create a new chat strategy for your bot</CardDescription>
      </CardHeader>
      <CardContent>
        <Form method="post" className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Strategy Name</Label>
            <Input
              id="name"
              name="name"
              defaultValue={defaultValues.name}
              required
              placeholder="Enter strategy name"
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Input
              id="description"
              name="description"
              defaultValue={defaultValues.description}
              placeholder="Enter strategy description"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="prompt">Prompt</Label>
            <textarea
              id="prompt"
              name="prompt"
              defaultValue={defaultValues.prompt}
              required
              className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 min-h-[200px]"
              placeholder="Enter the strategy prompt"
            />
          </div>

          {error && (
            <div className="text-sm text-red-500">{error}</div>
          )}

          <Button type="submit" className="w-full">
            Create Strategy
          </Button>
        </Form>
      </CardContent>
    </Card>
  );
} 