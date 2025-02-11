import * as React from "react";
import { Link } from "@remix-run/react";
import { Button } from "../components/ui/button";
import { Home } from "lucide-react";
import MaxWidthWrapper from "../components/layout/max-width-wrapper";

export default function NotFound() {
  return (
    <MaxWidthWrapper>
      <div className="min-h-[80vh] flex flex-col items-center justify-center text-center gap-8">
        <div className="space-y-6">
          <img 
            src="/images/logos/logo.svg" 
            alt="AI4MDE Logo" 
            className="w-24 h-24 mx-auto opacity-50 dark:invert"
          />
          <h1 className="text-4xl font-bold tracking-tight">Page not found</h1>
          <p className="text-xl text-muted-foreground">
            Sorry, we couldn't find the page you're looking for.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-4">
          <Button asChild>
            <Link to="/" className="flex items-center gap-2">
              <Home className="w-4 h-4" />
              Back to Home
            </Link>
          </Button>
          <Button variant="outline" asChild>
            <Link to="/srsdocs">
              View Documents
            </Link>
          </Button>
        </div>

        <p className="text-sm text-muted-foreground">
          Error Code: 404
        </p>
      </div>
    </MaxWidthWrapper>
  );
} 