'use client'

import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet"
import { Menu, LogIn, LogOut } from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { useState, useEffect } from "react"
import { useNavigation } from './use-navigation'
import MenuItem from "./MenuItem"
import LogoutButton from './logout-button'

export function MobileNav() {
  const { navigation, handleLogout, handleProtectedLink, isAuthenticated, user } = useNavigation()
  const [open, setOpen] = useState(false)

  // Close mobile menu when screen size changes to desktop
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 768) { // md breakpoint
        setOpen(false)
      }
    }

    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  const handleLogoutClick = async () => {
    await handleLogout()
    setOpen(false)
  }

  const handleClose = () => {
    setOpen(false)
  }

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="icon" className="md:hidden">
          <Menu className="h-6 w-6" />
          <span className="sr-only">Toggle menu</span>
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-[80vw] sm:w-[350px] p-0">
        <SheetHeader className="p-6 border-b">
          <SheetTitle>Menu</SheetTitle>
        </SheetHeader>
        <div className="flex-1 overflow-y-auto">
          <nav className="flex flex-col px-6 py-4">
            {navigation.map((item) => (
              <MenuItem
                key={item.name}
                href={item.href}
                protected={item.protected}
                isAuthenticated={isAuthenticated}
                onProtectedClick={handleProtectedLink}
                onClick={handleClose}
              >
                <div className="flex items-center gap-2 py-2">
                  {item.icon && <item.icon className="h-5 w-5" />}
                  <span>{item.name}</span>
                </div>
              </MenuItem>
            ))}
            
            <div className="pt-4 mt-4 border-t">
              {isAuthenticated ? (
                <>
                  <div className="text-sm text-muted-foreground mb-2">
                    {user?.name || user?.username || 'User'}
                  </div>
                  <LogoutButton
                    onLogout={handleLogoutClick}
                    className="flex items-center gap-2 py-2 text-lg text-muted-foreground hover:text-primary"
                  >
                    <LogOut className="h-5 w-5" />
                    <span>Logout</span>
                  </LogoutButton>
                </>
              ) : (
                <Link
                  href="/login"
                  onClick={handleClose}
                  className="flex items-center gap-2 py-2 text-lg text-muted-foreground hover:text-primary"
                >
                  <LogIn className="h-6 w-6" />
                  <span>Login</span>
                </Link>
              )}
            </div>
          </nav>
        </div>
      </SheetContent>
    </Sheet>
  )
}