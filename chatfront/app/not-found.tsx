import Link from 'next/link'

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh]">
      <h1 className="text-4xl font-bold text-foreground mb-4">404</h1>
      <h2 className="text-xl text-foreground mb-4">Page Not Found</h2>
      <p className="text-muted-foreground mb-4">The page you're looking for doesn't exist.</p>
      <Link 
        href="/" 
        className="text-primary hover:text-primary/80 underline underline-offset-4"
      >
        Return Home
      </Link>
    </div>
  );
}
