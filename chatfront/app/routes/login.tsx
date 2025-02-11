import * as React from "react";
import { ActionFunctionArgs, LoaderFunctionArgs, json, redirect } from "@remix-run/node";
import { Form, useActionData, useSearchParams } from "@remix-run/react";
import { authenticator } from "../services/auth.server";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Label } from "../components/ui/label";
import { Input } from "../components/ui/input";
import { Button } from "../components/ui/button";
import { Eye, EyeOff } from "lucide-react";

export async function loader({ request }: LoaderFunctionArgs) {
  // If user is already authenticated, redirect to home
  const user = await authenticator.isAuthenticated(request);
  if (user) {
    return redirect("/");
  }
  return null;
}

export async function action({ request }: ActionFunctionArgs) {
  const clonedRequest = request.clone();
  const formData = await clonedRequest.formData();
  const redirectTo = formData.get("redirectTo")?.toString() || "/";

  try {
    // Attempt authentication with original request
    return await authenticator.authenticate("form", request, {
      successRedirect: redirectTo,
      failureRedirect: undefined,
      throwOnError: true
    });
  } catch (error) {
    // Check if the error is a redirect response (status 302)
    if (error instanceof Response && error.status === 302) {
      return error; // Return the redirect response
    }

    console.error('Login action error:', {
      error,
      message: error instanceof Error ? error.message : 'Unknown error',
      stack: error instanceof Error ? error.stack : undefined
    });

    return json({ 
      error: error instanceof Error ? error.message : 'Authentication failed. Please check your credentials and try again.' 
    }, {
      status: 400
    });
  }
}

export default function Login() {
  const [searchParams] = useSearchParams();
  const redirectTo = searchParams.get("redirectTo") || "/";
  const actionData = useActionData<typeof action>();
  const [showPassword, setShowPassword] = React.useState(false);

  return (
    <main className="flex-1 min-h-[calc(100vh-12rem)] grid place-items-center bg-muted/50 -mt-[1px]">
      <Card className="w-full max-w-md mx-4 shadow-lg">
        <CardHeader className="space-y-4">
          <div className="flex justify-center">
            <img 
              src="/images/logos/logo.svg" 
              alt="AI4MDE Logo" 
              className="h-12 w-12"
            />
          </div>
          <div className="text-center">
            <CardTitle>Welcome to AI4MDE</CardTitle>
            <CardDescription>Sign in to your account</CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          <Form method="post" className="space-y-4">
            <input type="hidden" name="redirectTo" value={redirectTo} />
            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                name="username"
                type="text"
                required
                placeholder="Enter your username"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  required
                  placeholder="Enter your password"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="absolute right-0 top-0 h-full px-2 py-2 hover:bg-transparent"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? (
                    <EyeOff className="h-10 w-10 text-muted-foreground" />
                  ) : (
                    <Eye className="h-10 w-10 text-muted-foreground" />
                  )}
                  <span className="sr-only">
                    {showPassword ? "Hide password" : "Show password"}
                  </span>
                </Button>
              </div>
            </div>
            {actionData?.error && (
              <div className="text-sm text-red-500">{actionData.error}</div>
            )}
            <Button type="submit" className="w-full">
              Sign in
            </Button>
          </Form>
        </CardContent>
      </Card>
    </main>
  );
}
