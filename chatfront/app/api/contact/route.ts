import { writeFile, mkdir, access } from 'fs/promises'
import { NextResponse } from 'next/server'
import path from 'path'

interface ContactForm {
  firstName: string
  lastName: string
  email: string
  message: string
}

export async function POST(req: Request) {
  try {
    const data: ContactForm = await req.json()
    
    // Create timestamp
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
    
    // Create filename with timestamp
    const filename = `${data.firstName}_${data.lastName}_${timestamp}.md`
    const filePath = path.join(process.cwd(), 'app/data/contact', filename)
    
    // Ensure directory exists
    await createDirectoryIfNotExists(path.join(process.cwd(), 'app/data/contact'))
    
    // Create markdown content
    const markdown = `---
first_name: ${data.firstName}
last_name: ${data.lastName}
email: ${data.email}
date: ${new Date().toISOString()}
---
${data.message}
`
    
    // Write file
    await writeFile(filePath, markdown, 'utf-8')
    
    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('Failed to save contact form:', error)
    return NextResponse.json(
      { error: 'Failed to save contact form' },
      { status: 500 }
    )
  }
}

async function createDirectoryIfNotExists(dirPath: string) {
  try {
    await access(dirPath)
  } catch {
    await mkdir(dirPath, { recursive: true })
  }
} 