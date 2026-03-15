import { NextResponse } from 'next/server';

export async function GET(request: Request) {
  const mockFacets = {
    categories: [
      { label: "Масло подсолнечное рафинированное", count: 8 },
      { label: "Семена масличные и маслосодержащие плоды", count: 2 },
      { label: "Масла индустриальные", count: 1 }
    ],
    manufacturers: [
      { label: "ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ МАСЛОЭКСТРАКЦИОННЫЙ ЗАВОД ЮГ РУСИ", count: 2 },
      { label: "ООО \"Аквилон\"", count: 2 },
      { label: "Слобода", count: 2 },
      { label: "Националь", count: 1 },
      { label: "ПУБЛИЧНОЕ АКЦИОНЕРНОЕ ОБЩЕСТВО НК \"РОСНЕФТЬ\" - МЗ \"НЕФТЕПРОДУКТ\"", count: 1 }
    ]
  };

  await new Promise((resolve) => setTimeout(resolve, 300));

  return NextResponse.json(mockFacets);
}
