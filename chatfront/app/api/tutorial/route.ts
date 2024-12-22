import { NextResponse } from 'next/server';

export async function GET() {
  try {
    return NextResponse.json({});
  } catch (error) {
    console.error('Failed to fetch tutorial data:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Failed to fetch tutorial data' },
      { status: 500 }
    );
  }
} 