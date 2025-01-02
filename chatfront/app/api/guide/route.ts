import { NextResponse } from 'next/server';

export async function GET() {
  try {
    return NextResponse.json({});
  } catch (error) {
    console.error('Failed to fetch guide data:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Failed to fetch guide data' },
      { status: 500 }
    );
  }
}
