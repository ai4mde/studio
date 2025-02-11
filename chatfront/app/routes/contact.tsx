import * as React from "react";
import { json, redirect } from "@remix-run/node";
import type { ActionFunction, MetaFunction } from "@remix-run/node";
import { Form, useActionData, useNavigation } from "@remix-run/react";
import { z } from "zod";
import MaxWidthWrapper from "../components/layout/max-width-wrapper";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { Label } from "../components/ui/label";
import { promises as fs } from 'fs';
import path from 'path';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "../components/ui/dialog";

export const meta: MetaFunction = () => {
  return [
    { title: "Contact - AI4MDE" },
    { name: "description", content: "Get in touch with the AI4MDE team" },
  ];
};

const formSchema = z.object({
  firstName: z.string().min(2, "First name must be at least 2 characters").max(50),
  lastName: z.string().min(2, "Last name must be at least 2 characters").max(50),
  email: z.string().email("Invalid email address"),
  message: z.string().min(10, "Message must be at least 10 characters").max(1000),
});

export const action: ActionFunction = async ({ request }) => {
  const formData = Object.fromEntries(await request.formData());
  
  try {
    const validatedData = formSchema.parse(formData);
    
    // Create timestamp in ISO format
    const now = new Date();
    const timestamp = now.toISOString();
    
    // Create filename with timestamp
    const filename = `${validatedData.firstName}_${validatedData.lastName}_${timestamp.replace(/[:.]/g, '-')}.md`;
    
    // Ensure the contact directory exists
    const contactDir = path.join(process.cwd(), 'data', 'contact');
    await fs.mkdir(contactDir, { recursive: true });
    
    // Create markdown content
    const markdown = `---
first_name: ${validatedData.firstName}
last_name: ${validatedData.lastName}
email: ${validatedData.email}
date: ${timestamp}
---

${validatedData.message}
`;

    // Save the file
    const filePath = path.join(contactDir, filename);
    await fs.writeFile(filePath, markdown, 'utf-8');
    
    return json({ success: true });
    
  } catch (error) {
    if (error instanceof z.ZodError) {
      return json({ errors: error.errors }, { status: 400 });
    }
    console.error('Failed to save contact form:', error);
    return json({ error: "Failed to send message. Please try again later." }, { status: 500 });
  }
};

export default function Contact() {
  const actionData = useActionData<typeof action>();
  const [showThankYou, setShowThankYou] = React.useState(false);
  const formRef = React.useRef<HTMLFormElement>(null);
  const navigation = useNavigation();
  const isSubmitting = navigation.state === "submitting";
  
  React.useEffect(() => {
    if (actionData?.success) {
      setShowThankYou(true);
      if (formRef.current) {
        formRef.current.reset();
      }
    }
  }, [actionData]);

  const handleDialogClose = () => {
    setShowThankYou(false);
  };

  return (
    <>
      <MaxWidthWrapper className="py-8">
        <div className="flex flex-col items-center space-y-8">
          <div className="space-y-2 text-center">
            <h1 className="text-3xl font-bold">Get In Touch</h1>
            <p className="text-muted-foreground">
              Have questions, feedback, or want to collaborate? Drop us a message!
            </p>
          </div>

          <Card className="w-full max-w-md md:max-w-2xl lg:max-w-4xl">
            <CardContent className="pt-6">
              <Form ref={formRef} method="post" className="space-y-6">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="firstName">First Name</Label>
                    <Input
                      id="firstName"
                      name="firstName"
                      placeholder="John"
                      aria-describedby={
                        actionData?.errors?.find((e) => e.path[0] === "firstName")
                          ? "firstName-error"
                          : undefined
                      }
                    />
                    {actionData?.errors?.find((e) => e.path[0] === "firstName") && (
                      <p className="text-sm text-red-500" id="firstName-error">
                        {actionData.errors.find((e) => e.path[0] === "firstName")?.message}
                      </p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="lastName">Last Name</Label>
                    <Input
                      id="lastName"
                      name="lastName"
                      placeholder="Doe"
                      aria-describedby={
                        actionData?.errors?.find((e) => e.path[0] === "lastName")
                          ? "lastName-error"
                          : undefined
                      }
                    />
                    {actionData?.errors?.find((e) => e.path[0] === "lastName") && (
                      <p className="text-sm text-red-500" id="lastName-error">
                        {actionData.errors.find((e) => e.path[0] === "lastName")?.message}
                      </p>
                    )}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    type="email"
                    id="email"
                    name="email"
                    placeholder="john.doe@example.com"
                    aria-describedby={
                      actionData?.errors?.find((e) => e.path[0] === "email")
                        ? "email-error"
                        : undefined
                    }
                  />
                  {actionData?.errors?.find((e) => e.path[0] === "email") && (
                    <p className="text-sm text-red-500" id="email-error">
                      {actionData.errors.find((e) => e.path[0] === "email")?.message}
                    </p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="message">Message</Label>
                  <Textarea
                    id="message"
                    name="message"
                    className="min-h-[250px]"
                    aria-describedby={
                      actionData?.errors?.find((e) => e.path[0] === "message")
                        ? "message-error"
                        : undefined
                    }
                  />
                  {actionData?.errors?.find((e) => e.path[0] === "message") && (
                    <p className="text-sm text-red-500" id="message-error">
                      {actionData.errors.find((e) => e.path[0] === "message")?.message}
                    </p>
                  )}
                </div>

                <Button type="submit" className="w-full" disabled={isSubmitting}>
                  {isSubmitting ? "Sending..." : "Send Message"}
                </Button>
              </Form>
            </CardContent>
          </Card>
        </div>
      </MaxWidthWrapper>

      <Dialog open={showThankYou} onOpenChange={handleDialogClose}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Thank You!</DialogTitle>
            <DialogDescription>
              We have received your message and will get back to you within 2 working days.
            </DialogDescription>
          </DialogHeader>
          <div className="flex justify-end">
            <Button onClick={handleDialogClose}>
              Close
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
} 