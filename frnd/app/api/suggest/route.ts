import { NextResponse } from 'next/server';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const q = searchParams.get('q') || '';

  // Return mock suggestions based on query or generic ones
  let suggestions = [
    "Масло подсолнечное рафинированое",
    "Масло подсолнечное рафинированное дезодорированное \"Золотая семечка\"",
    "Масло подсолнечное",
    "Масло подсолнечное Слобода рафинированное 1 л",
    "Масло Роснефть И-20А (216,5 л)"
  ];

  if (q && q.length > 0) {
    suggestions = suggestions.filter(s => s.toLowerCase().includes(q.toLowerCase()));
  }

  // Simulate network delay
  await new Promise((resolve) => setTimeout(resolve, 300));

  return NextResponse.json(suggestions.slice(0, 5));
}
