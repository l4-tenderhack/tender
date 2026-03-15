import { expect, test, describe, afterEach, mock } from "bun:test";
import { getSmartPrice, searchCte, cteSearch } from "./api";

// Mock global fetch
const originalFetch = global.fetch;

describe("getSmartPrice", () => {
  afterEach(() => {
    global.fetch = originalFetch;
  });

  test("should send GET request with correct URL and parameters", async () => {
    const mockFetch = mock(() =>
      Promise.resolve(
        new Response(JSON.stringify({ nmck_per_unit: 1000, warnings: [] }), { status: 200 })
      )
    );
    global.fetch = mockFetch;

    await getSmartPrice(123, "2023-01-01", "2023-12-31");

    const callArgs = mockFetch.mock.calls[0];
    const url = callArgs[0] as string;
    const options = callArgs[1] as RequestInit;

    expect(url).toContain("/nmck/123");
    expect(url).toContain("date_from=2023-01-01");
    expect(url).toContain("date_to=2023-12-31");
    expect(options.method).toBe("GET");
  });

  test("should return data on successful response", async () => {
    const mockResponse = { mean_price: "450.0", cte_id: 123 };
    global.fetch = mock(() =>
      Promise.resolve(
        new Response(JSON.stringify(mockResponse), { status: 200 })
      )
    );

    const result = await getSmartPrice(123);
    expect(result).toEqual(mockResponse);
  });

  test("should throw structured error on 422 response", async () => {
    const errorDetail = "Insufficient data for calculation";
    global.fetch = mock(() =>
      Promise.resolve(
        new Response(JSON.stringify({ detail: errorDetail }), { status: 422 })
      )
    );

    try {
      await getSmartPrice(123);
      expect(true).toBe(false); // Should not reach here
    } catch (e: any) {
      expect(e.status).toBe(422);
      expect(e.detail).toBe(errorDetail);
    }
  });

  test("should throw generic error on other non-ok responses", async () => {
    global.fetch = mock(() =>
      Promise.resolve(
        new Response("Not Found", { status: 404 })
      )
    );

    try {
      await getSmartPrice(123);
      expect(true).toBe(false);
    } catch (e: any) {
      expect(e.message).toContain("API error: 404");
    }
  });
});

describe("searchCte", () => {
  afterEach(() => {
    global.fetch = originalFetch;
  });

  test("should send POST request with correct payload for hybrid search", async () => {
    const mockFetch = mock(() =>
      Promise.resolve(
        new Response(JSON.stringify({ total: 0, execution_time_ms: 5, results: [] }), { status: 200 })
      )
    );
    global.fetch = mockFetch;
    
    await searchCte({ query: "бумага", limit: 10 });
    
    const callArgs = mockFetch.mock.calls[0];
    const url = callArgs[0] as string;
    const options = callArgs[1] as RequestInit;
    
    expect(options.method).toBe("POST");
    expect(url).toContain("/api/v1/search/hybrid");
    
    const body = JSON.parse(options.body as string);
    expect(body.query).toBe("бумага");
    expect(body.limit).toBe(10);
    expect(body.offset).toBe(0);
  });

  test("should return results array from hybrid search", async () => {
    const mockResults = [{ 
      cte_id: "1", 
      description: "Бумага SvetoCopy", 
      price: 300,
      category: "Бумага",
      manufacturer: "SvetoCopy",
      characteristics: {},
      score: 0.9,
      category_boost: 1.0
    }];
    
    global.fetch = mock(() =>
      Promise.resolve(
        new Response(JSON.stringify({ 
          total: 1, 
          execution_time_ms: 10, 
          results: mockResults
        }), { status: 200 })
      )
    );

    const result = await searchCte({ query: "бумага" });
    expect(result.results).toEqual(mockResults as any);
    expect(result.total).toBe(1);
  });
});

describe("cteSearch", () => {
  afterEach(() => {
    global.fetch = originalFetch;
  });

  test("should send POST request to /cte-search with correct payload", async () => {
    const mockFetch = mock(() =>
      Promise.resolve(
        new Response(JSON.stringify({ 
          query: "бумага", 
          matched_ctes: [], 
          contracts: [], 
          total_contracts: 0, 
          available_characteristics: {} 
        }), { status: 200 })
      )
    );
    global.fetch = mockFetch;
    
    await cteSearch({ query: "бумага", n: 5 });
    
    const callArgs = mockFetch.mock.calls[0];
    const url = callArgs[0] as string;
    const options = callArgs[1] as RequestInit;
    
    expect(options.method).toBe("POST");
    expect(url).toContain("/api/v1/cte-search");
    
    const body = JSON.parse(options.body as string);
    expect(body.query).toBe("бумага");
    expect(body.n).toBe(5);
  });
});
