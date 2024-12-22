"use client";
import React from "react";
import Link from "next/link";
import { useNavigation } from './use-navigation'
import Image from "next/image";
import { MobileNav } from "./mobile-nav"
import MenuItem from "./MenuItem";
import { Button } from '@/components/ui/button';
import { LogOut, LogIn } from "lucide-react"
import Logo from '@/app/assets/logo.svg';
import { cn } from "@/lib/utils";
import { ThemeToggle } from "@/components/layout/theme-toggle"

const NavBar = () => {
  const { navigation, handleLogout, handleProtectedLink, isAuthenticated } = useNavigation();

  return (
    <nav className="container flex h-16 items-center justify-between">
      <div className="flex items-center gap-2">
        <Link href="/" className="flex items-center space-x-2">
          <Image 
            src={Logo} 
            alt="Logo" 
            width={128} 
            height={32} 
            className="w-auto h-12" 
            priority 
          />
        </Link>
      </div>

      <div className="hidden md:flex items-center space-x-4">
        {navigation.map((item) => (
          <MenuItem
            key={item.name}
            href={item.href}
            protected={item.protected}
            isAuthenticated={isAuthenticated}
            onProtectedClick={(event) => handleProtectedLink(event, item.href)}
          >
            <div className="flex items-center gap-2">
              {item.icon && <item.icon className="h-4 w-4" />}
              <span>{item.name}</span>
            </div>
          </MenuItem>
        ))}
        
        <ThemeToggle />
        
        <div className="ml-4">
          {isAuthenticated ? (
            <Button 
              onClick={handleLogout}
              variant="ghost"
              className={cn(
                "flex items-center gap-2",
                "text-muted-foreground hover:text-foreground",
                "hover:bg-[hsl(var(--primary))] hover:text-primary-foreground"
              )}
            >
              <LogOut className="h-4 w-4" />
              <span>Logout</span>
            </Button>
          ) : (
            <Link href="/login">
              <Button 
                variant="ghost"
                className={cn(
                  "flex items-center gap-2",
                  "text-muted-foreground hover:text-foreground",
                  "hover:bg-[hsl(var(--primary))] hover:text-primary-foreground"
                )}
              >
                <LogIn className="h-4 w-4" />
                <span>Login</span>
              </Button>
            </Link>
          )}
        </div>
      </div>

      <div className="md:hidden">
        <MobileNav />
      </div>
    </nav>
  );
};

export default NavBar;
