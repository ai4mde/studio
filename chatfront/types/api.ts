interface ApiResponse {
  id: number;
  content: string;
  role: 'USER' | 'ASSISTANT' | 'SYSTEM';
  created_at: string;
}

interface ApiError {
  message: string;
  status?: number;
} 