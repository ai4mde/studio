'use client';

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { useToast } from "@/hooks/use-toast"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"

const formSchema = z.object({
  firstName: z.string().min(2).max(50),
  lastName: z.string().min(2).max(50),
  email: z.string().email(),
  message: z.string().min(10).max(1000)
})

type FormData = z.infer<typeof formSchema>

export default function ContactPage() {
  const { toast } = useToast()
  const [isSending, setIsSending] = useState(false)
  const [showThankYou, setShowThankYou] = useState(false)
  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(formSchema)
  })

  const onSubmit = async (data: FormData) => {
    setIsSending(true)
    try {
      const response = await fetch('/api/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })

      if (!response.ok) throw new Error('Failed to send message')

      reset()
      setShowThankYou(true)
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to submit form",
        variant: "destructive"
      })
    } finally {
      setIsSending(false)
    }
  }

  return (
    <>
      <div className="container flex flex-col items-center py-10 space-y-8 max-w-7xl">
        <div className="space-y-2 text-center">
          <h1 className="text-3xl font-bold">Get In Touch</h1>
          <p className="text-muted-foreground">
            Have questions, feedback, or want to collaborate? Drop us a message!
          </p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="w-full space-y-6">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label htmlFor="firstName" className="text-sm font-medium">
                First Name
              </label>
              <Input
                id="firstName"
                {...register('firstName')}
                placeholder="John"
                error={errors.firstName?.message}
              />
            </div>
            <div className="space-y-2">
              <label htmlFor="lastName" className="text-sm font-medium">
                Last Name
              </label>
              <Input
                id="lastName"
                {...register('lastName')}
                placeholder="Doe"
                error={errors.lastName?.message}
              />
            </div>
          </div>

          <div className="space-y-2">
            <label htmlFor="email" className="text-sm font-medium">
              Email
            </label>
            <Input
              type="email"
              id="email"
              {...register('email')}
              placeholder="john.doe@example.com"
              error={errors.email?.message}
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="message" className="text-sm font-medium">
              Message
            </label>
            <Textarea
              id="message"
              {...register('message')}
              className="min-h-[250px]"
              error={errors.message?.message}
            />
          </div>

          <Button
            type="submit"
            className="w-full"
            disabled={isSending}
          >
            {isSending ? 'Sending...' : 'Send Message'}
          </Button>
        </form>
      </div>

      <Dialog open={showThankYou} onOpenChange={setShowThankYou}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Thank You!</DialogTitle>
            <DialogDescription>
              We have received your message and will get back to you within 2 working days.
            </DialogDescription>
          </DialogHeader>
        </DialogContent>
      </Dialog>
    </>
  )
}
