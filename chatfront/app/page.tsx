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
      <section className="text-gray-600 dark:text-gray-50 body-font">
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
                className="text-5xl font-bold text-sky-700 dark:text-sky-500"
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
                Model-Driven Engineering (MDE) represents a software development methodology that emphasizes the use of domain-specific models as primary artifacts throughout the development lifecycle. AI4MDE, a pioneering initiative from Leiden University, revolutionizes this paradigm by integrating Large Language Models (LLMs) with traditional MDE approaches. Through sophisticated natural language processing and interactive dialogue systems, AI4MDE facilitates automated transformation from initial requirements specification to preliminary software architectures, effectively bridging the gap between human-centric documentation and formal model specifications. This innovative approach streamlines the software development process while maintaining rigorous engineering principles.
              </p>
            </div>

            {/* Centered Buttons */}
            <div className="text-center space-x-4">
              <Button 
                asChild 
                className="bg-sky-700 hover:bg-sky-600 text-white py-3 px-6 rounded-lg shadow-md"
              >
                <Link href="/guide">Get Started</Link>
              </Button>
              <Button 
                asChild 
                variant="outline"
                className="bg-background hover:bg-sky-600 hover:text-white py-3 px-6 rounded-lg shadow-md"
              >
                <Link href="/contact">Contact Us</Link>
              </Button>
            </div>
          </div>
        </div>
      </section>
      <section className="text-gray-600 dark:text-gray-50 body-font">
        <div className="container px-5 py-24 mx-auto">
          <h2 className="text-4xl pb-8 mb-4 font-bold  text-center">
            Features
          </h2>
          <div className="flex flex-wrap -m-4">
            <div className="p-4 lg:w-1/3">
              <Card className="h-full bg-gray-200 dark:bg-gray-900 bg-opacity-75 rounded-lg overflow-hidden text-center relative shadow-lg">
                <CardHeader>
                  <CardTitle className="tracking-widest text-xs title-font font-medium mb-1">
                    CHATBOT DRIVEN BY LLM
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <h1 className="title-font sm:text-2xl text-xl font-medium text-gray-900 dark:text-white mb-3">
                    Intelligent Interaction
                  </h1>
                  <p className="leading-relaxed mb-3 text-gray-700 dark:text-gray-50">
                    Experience our advanced chatbot powered by Large Language Models, designed specifically for Model-Driven Engineering. Through natural language dialogue, it guides users from initial requirements gathering to generating UML diagrams and preliminary software architectures, making the software development process more intuitive and efficient.
                  </p>
                </CardContent>
                <CardFooter className="flex justify-center">
                  <Link 
                    href="/guide" 
                    className="inline-flex items-center hover:text-sky-600 dark:hover:text-sky-400"
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
              <Card className="h-full bg-gray-200 dark:bg-gray-900 bg-opacity-75 rounded-lg overflow-hidden text-center relative shadow-lg">
                <CardHeader>
                  <CardTitle className="tracking-widest text-xs title-font font-medium mb-1">
                    SOFTWARE REQUIREMENTS SPECIFICATION
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <h1 className="title-font sm:text-2xl text-xl font-medium text-gray-900 dark:text-white mb-3">
                    Automated SRS Generation
                  </h1>
                  <p className="leading-relaxed mb-3 text-gray-700 dark:text-gray-50">
                    Transform natural language conversations into comprehensive Software Requirements Specification documents. Our AI-powered system analyzes user requirements, automatically structures them into formal SRS sections, and generates detailed documentation following IEEE standards, complete with functional and non-functional requirements.
                  </p>
                </CardContent>
                <CardFooter className="flex justify-center">
                  <Link 
                    href="/guide" 
                    className="inline-flex items-center hover:text-sky-600 dark:hover:text-sky-400"
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
              <Card className="h-full bg-gray-200 dark:bg-gray-900 bg-opacity-75 rounded-lg overflow-hidden text-center relative shadow-lg">
                <CardHeader>
                  <CardTitle className="tracking-widest text-xs title-font font-medium mb-1">
                    UML DIAGRAMS GENERATION
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <h1 className="title-font sm:text-2xl text-xl font-medium text-gray-900 dark:text-white mb-3">
                    Automated Design Visualization
                  </h1>
                  <p className="leading-relaxed mb-3 text-gray-700 dark:text-gray-50">
                    Convert natural language descriptions into precise UML diagrams automatically. Our AI system generates various diagram types including Class, Sequence, and Use Case diagrams, providing clear visual representations of your software architecture and system behavior while maintaining UML standards and best practices.
                  </p>
                </CardContent>
                <CardFooter className="flex justify-center">
                  <Link 
                    href="/guide" 
                    className="inline-flex items-center hover:text-sky-600 dark:hover:text-sky-400"
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
