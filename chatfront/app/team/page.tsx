'use client'

import Image from 'next/image'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { matrixStyles } from "@/components/ui/matrix-styles"
import JohnDoeAvatar from '@/app/assets/john_doe.jpg'
import JaneSmithAvatar from '@/app/assets/jane_smith.jpg'
import AlexJohnsonAvatar from '@/app/assets/alex_johnson.jpg'
import { cn } from "@/lib/utils"

interface TeamMember {
  name: string
  role: string
  image: string
  bio: string
  links?: {
    github?: string
    linkedin?: string
    twitter?: string
  }
}
// Photos by https://www.uifaces.co/
const teamMembers: TeamMember[] = [
  {
    name: "John Doe",
    role: "Project Lead",
    image: JohnDoeAvatar.src,
    bio: "Leading the development of AI4MDE tools and methodologies.",
    links: {
      github: "https://github.com/johndoe",
      linkedin: "https://linkedin.com/in/johndoe"
    }
  },
  {
    name: "Jane Smith",
    role: "AI Research Engineer",
    image: JaneSmithAvatar.src,
    bio: "Specializing in machine learning applications for model transformation and validation.",
    links: {
      github: "https://github.com/janesmith",
      linkedin: "https://linkedin.com/in/janesmith",
      twitter: "https://twitter.com/janesmith"
    }
  },
  {
    name: "Alex Johnson",
    role: "MDE Specialist",
    image: AlexJohnsonAvatar.src,
    bio: "Expert in model-driven engineering practices and metamodeling frameworks.",
    links: {
      github: "https://github.com/alexj",
      linkedin: "https://linkedin.com/in/alexjohnson"
    }
  }
]

export default function TeamPage() {
  return (
    <div className={matrixStyles.layout.base}>
      <div className={matrixStyles.layout.gradient} />
      <div className="container py-10">
        <div className="space-y-4 text-center mb-10">
          <h1 className="text-3xl font-bold">Our Team</h1>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Meet the dedicated individuals working to advance Model-Driven Engineering through AI innovation.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {teamMembers.map((member) => (
            <Card 
              key={member.name} 
              className={cn(
                "overflow-hidden flex flex-col",
                matrixStyles.card.base,
                matrixStyles.card.shadow,
                matrixStyles.card.border
              )}
            >
              <CardHeader className="text-center space-y-4">
                <div className="flex justify-center">
                  <Image
                    src={member.image}
                    alt={member.name}
                    width={120}
                    height={120}
                    className="rounded-full ring-2 ring-primary/20"
                  />
                </div>
                <div className="space-y-1">
                  <CardTitle className="text-xl break-words">
                    {member.name}
                  </CardTitle>
                  <p className="text-sm text-muted-foreground">
                    {member.role}
                  </p>
                </div>
              </CardHeader>
              <CardContent className="flex-1 flex flex-col">
                <p className="text-sm text-muted-foreground mb-4 flex-1">{member.bio}</p>
                {member.links && (
                  <div className="flex justify-center gap-4 pt-2">
                    {member.links.github && (
                      <a
                        href={member.links.github}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-muted-foreground hover:text-primary transition-colors"
                      >
                        GitHub
                      </a>
                    )}
                    {member.links.linkedin && (
                      <a
                        href={member.links.linkedin}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-muted-foreground hover:text-primary"
                      >
                        LinkedIn
                      </a>
                    )}
                    {member.links.twitter && (
                      <a
                        href={member.links.twitter}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-muted-foreground hover:text-primary"
                      >
                        Twitter
                      </a>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  )
} 