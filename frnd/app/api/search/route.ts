import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const query = body.query || '';

    // Mock response based on the provided JSON
    const mockResponse = {
      total: 10,
      execution_time_ms: 583.85,
      items: [
        {
          id: "35245718",
          name: "Масло подсолнечное рафинированое",
          category: "Масло подсолнечное рафинированное",
          supplier: "ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ МАСЛОЭКСТРАКЦИОННЫЙ ЗАВОД ЮГ РУСИ",
          price: 120.00,
          score: 0.825,
          region: "г. Ростов-на-Дону",
          image: "https://via.placeholder.com/150",
          characteristics: {}
        },
        {
          id: "35714293",
          name: "Масло подсолнечное рафинированное дезодорированное \"Золотая семечка\", 1 литр",
          category: "Масло подсолнечное рафинированное",
          supplier: "ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ МАСЛОЭКСТРАКЦИОННЫЙ ЗАВОД ЮГ РУСИ",
          price: 135.00,
          score: 0.825,
          region: "г. Ростов-на-Дону",
          image: "https://via.placeholder.com/150",
          characteristics: {}
        },
        {
          id: "21525132",
          name: "Масло подсолнечное",
          category: "Масло подсолнечное рафинированное",
          supplier: "ООО \"Аквилон\"",
          price: 115.00,
          score: 0.810,
          region: "г. Москва",
          image: "https://via.placeholder.com/150",
          characteristics: {}
        },
        {
          id: "35025348",
          name: "Масло подсолнечное Слобода рафинированное 1 л",
          category: "Масло подсолнечное рафинированное",
          supplier: "Слобода",
          price: 140.00,
          score: 0.810,
          region: "г. Москва",
          image: "https://via.placeholder.com/150",
          characteristics: {}
        },
        {
          id: "38019313",
          name: "Масло Роснефть И-20А (216,5 л)",
          category: "Масла индустриальные",
          supplier: "ПУБЛИЧНОЕ АКЦИОНЕРНОЕ ОБЩЕСТВО НК \"РОСНЕФТЬ\" - МЗ \"НЕФТЕПРОДУКТ\"",
          price: 24500.00,
          score: 0.733,
          region: "г. Рязань",
          image: "https://via.placeholder.com/150",
          characteristics: {
            "марка масла": "и-20а",
            "плотность": "0.87000"
          }
        }
      ],
      facets: {
        categories: [
          { label: "Масло подсолнечное рафинированное", count: 8 },
          { label: "Семена масличные и маслосодержащие плоды", count: 2 },
          { label: "Масла индустриальные", count: 1 }
        ]
      }
    };

    // Simulate network delay
    await new Promise((resolve) => setTimeout(resolve, 600));

    return NextResponse.json(mockResponse);
  } catch (error) {
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
