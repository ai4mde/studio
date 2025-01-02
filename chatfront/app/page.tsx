"use client";

import {
  Carousel,
  CarouselContent,
  CarouselItem,
} from "@/components/ui/carousel";
import Autoplay from "embla-carousel-autoplay";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card";
import { TypeAnimation } from 'react-type-animation';

export default function Home() {
  const images = [
    "/images/home/hero-01.jpg",
    "/images/home/hero-02.jpg",
    "/images/home/hero-03.jpg",
  ];

  return (
    <main>
      <section className="text-foreground body-font">
        <div className="min-h-screen bg-background flex flex-col items-center justify-center">
          <div className="container mx-auto px-4 py-16">
            {/* Title Section */}
            <div className="w-full text-center mb-8">
              <h1 className="text-5xl font-bold mb-4 text-foreground">Welcome to</h1>
              <TypeAnimation
                sequence={[
                  'AI for Model-Driven Engineering!',
                  5000, // Wait 3s
                  '', // Clear the text
                  500,  // Wait 0.5s before restarting
                  'AI4MDE!',
                  5000, // Wait 3s
                  '', // Clear the text
                  500,  // Wait 0.5s before restarting
                ]}
                wrapper="h1"
                speed={50}
                className="text-5xl font-bold text-primary"
                repeat={Infinity}
              />
            </div>

            {/* Carousel Section */}
            <Carousel
              opts={{
                align: "start",
                loop: true,
              }}
              plugins={[
                Autoplay({
                  delay: 5000,
                }),
              ]}
              className="w-full max-w-5xl mx-auto mb-8"
            >
              <CarouselContent>
                {images.map((image, index) => (
                  <CarouselItem key={index}>
                    <div className="relative aspect-[16/9] w-full">
                      <Image
                        src={image}
                        alt={`Hero image ${index + 1}`}
                        fill
                        className="rounded-lg shadow-md object-cover"
                        priority={index === 0}
                      />
                    </div>
                  </CarouselItem>
                ))}
              </CarouselContent>
            </Carousel>

            {/* Description Section */}
            <div className="w-full md:w-2/3 text-center mx-auto mb-12">
              <p className="text-xl leading-relaxed text-muted-foreground">
                Artifacial Intelligence for Model-Driven Engineering in short AI4MDE is an initiative from Leiden University. Model-Driven Engineering (MDE) is a software development methodology that emphasizes the use of domain-specific models as primary artifacts throughout the development lifecycle. This project uses AI, more specific Large Language Models (LLMs) to conduct interviews with stakeholders and transforms these to requirements, models and documents required in the software development lifecycle. The aim of this project is to support Business Analysts and Architects speed up the software requirements engineering process.
              </p>
            </div>

            {/* Centered Buttons */}
            <div className="text-center space-x-4">
              <Button 
                asChild 
                className="bg-primary hover:bg-primary/90 text-primary-foreground py-3 px-6 rounded-lg shadow-md"
              >
                <Link href="/guide">Get Started</Link>
              </Button>
              <Button 
                asChild 
                variant="outline"
                className="bg-background hover:bg-primary hover:text-primary-foreground py-3 px-6 rounded-lg shadow-md"
              >
                <Link href="/contact">Contact Us</Link>
              </Button>
            </div>
          </div>
        </div>
      </section>

      <section className="text-foreground body-font">
        <div className="container px-5 py-24 mx-auto">
          <h2 className="text-4xl pb-8 mb-4 font-bold text-foreground text-center">
            Features
          </h2>
          <div className="flex flex-wrap -m-4">
            <div className="p-4 lg:w-1/3">
              <Card className="h-full bg-card text-card-foreground rounded-lg overflow-hidden text-center relative shadow-lg">
                <CardHeader>
                  <CardTitle className="tracking-widest text-xs title-font font-medium text-muted-foreground">
                    CHATBOT DRIVEN BY LLM
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <h1 className="title-font sm:text-2xl text-xl font-medium mb-3">
                    Intelligent Interaction
                  </h1>
                  <p className="leading-relaxed mb-3">
                    Discover our modularly designed AI-driven chatbot for engaging with end users. The chatbot makes use of AI agents, each of which is responsible for a specific task or function. This makes it relatively simple to adjust existing functionalities or add new ones. functions relatively simple. Natural language conversations guide the user through a predetermined procedure. Using natural language dialogue, it guides users through a predetermined procedure.
                  </p>
                </CardContent>
                <CardFooter className="flex justify-center">
                  <Link 
                    href="/guide" 
                    className="inline-flex items-center text-primary hover:text-primary/80"
                  >
                    Learn More
                    <svg
                      className="w-4 h-4 ml-2"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth="2"
                      fill="none"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <path d="M5 12h14"></path>
                      <path d="M12 5l7 7-7 7"></path>
                    </svg>
                  </Link>
                </CardFooter>
              </Card>
            </div>

            <div className="p-4 lg:w-1/3">
              <Card className="h-full bg-card text-card-foreground rounded-lg overflow-hidden text-center relative shadow-lg">
                <CardHeader>
                  <CardTitle className="tracking-widest text-xs title-font font-medium text-muted-foreground">
                    SOFTWARE REQUIREMENTS SPECIFICATION
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <h1 className="title-font sm:text-2xl text-xl font-medium mb-3">
                    Automated SRS Generation
                  </h1>
                  <p className="leading-relaxed mb-3">
                    Transform natural language conversations into comprehensive Software Requirements Specification documents. Our AI-powered system gathers and analyses user requirements through an interview and then automatically generates UML models. In conclusion, the system generates a software requirements specification (SRS) document that is compliant with the standards established by the IEEE.
                  </p>
                </CardContent>
                <CardFooter className="flex justify-center">
                  <Link 
                    href="/guide" 
                    className="inline-flex items-center text-primary hover:text-primary/80"
                  >
                    Learn More
                    <svg
                      className="w-4 h-4 ml-2"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth="2"
                      fill="none"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <path d="M5 12h14"></path>
                      <path d="M12 5l7 7-7 7"></path>
                    </svg>
                  </Link>
                </CardFooter>
              </Card>
            </div>
            
            <div className="p-4 lg:w-1/3">
              <Card className="h-full bg-card text-card-foreground rounded-lg overflow-hidden text-center relative shadow-lg">
                <CardHeader>
                  <CardTitle className="tracking-widest text-xs title-font font-medium text-muted-foreground">
                    UML DIAGRAMS GENERATION
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <h1 className="title-font sm:text-2xl text-xl font-medium mb-3">
                    Automated Design Visualization
                  </h1>
                  <p className="leading-relaxed mb-3">
                    Convert natural language descriptions into precise UML diagrams automatically. Our AI system generates various diagram types, including class, sequence, and use case diagrams, providing clear visual representations of your software architecture and system behaviour while maintaining UML standards and best practices. Finaly the UML diagrams can be modified in the Studio app.
                  </p>
                </CardContent>
                <CardFooter className="flex justify-center">
                  <Link 
                    href="/guide" 
                    className="inline-flex items-center text-primary hover:text-primary/80"
                  >
                    Learn More
                    <svg
                      className="w-4 h-4 ml-2"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth="2"
                      fill="none"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <path d="M5 12h14"></path>
                      <path d="M12 5l7 7-7 7"></path>
                    </svg>
                  </Link>
                </CardFooter>
              </Card>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
