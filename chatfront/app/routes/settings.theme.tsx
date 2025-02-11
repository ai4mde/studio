import * as React from "react"
import { ThemeColors } from "../components/layout/theme-colors"
import { ThemeToggle } from "../components/layout/theme-toggle"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
import { Separator } from "../components/ui/separator"

export default function ThemeSettings() {
  return (
    <div className="container py-10">
      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-medium">Theme Settings</h3>
          <p className="text-sm text-muted-foreground">
            Customize how the application looks and feels.
          </p>
        </div>
        <Separator />
        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Theme</CardTitle>
              <CardDescription>
                Select your preferred theme mode.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ThemeToggle />
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Theme Colors</CardTitle>
              <CardDescription>
                Preview of the current theme colors.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ThemeColors />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
} 