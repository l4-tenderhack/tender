import { expect, test, describe } from "bun:test";
import { searchCte, getSmartPrice } from "./api";

// Since we're running in Bun and not in Next.js browser context, 
// we need to handle the fact that /api-external and /api-analytics 
// are relative paths that usually get rewritten by Next.js.
// We'll mock the global fetch to point to the real domain for this test.

const BASE_DOMAIN = "https://akim.larek.tech";

describe("User Flow Integration (Search -> Smart Price)", () => {
  const originalFetch = global.fetch;

  test("User searches for 'бумага' and checks smart price of the first result", async () => {
    // 1. Mock fetch to intercept relative calls and redirect to real domain
    global.fetch = async (input: string | Request | URL, init?: RequestInit) => {
      let url = typeof input === 'string' ? input : (input instanceof Request ? input.url : input.toString());
      
      // All requests now go to the unified Akim backend via /api prefix
      if (url.includes('/api/v1/')) {
        url = url.replace(/\/api\/v1\//, "https://akim.larek.tech/api/v1/");
      }
      
      return originalFetch(url, init);
    };

    try {
      // 2. User searches for "бумага"
      console.log("Searching for 'бумага' via Hybrid Search...");
      let searchResult: any;
      try {
        searchResult = await searchCte({ query: "бумага" });
      } catch (err: any) {
        console.error("Search failed with error:", err);
        throw err;
      }
      
      // Verify we got results in the new structure
      const results = searchResult.results || [];
      expect(results.length).toBeGreaterThan(0);
      
      const firstProduct = results[0];
      const cteId = firstProduct.cte_id;
      console.log(`Found product: ${firstProduct.description} (ID: ${cteId})`);
      expect(cteId).toBeDefined();

      // 3. User requests Smart Price for this specific CTE ID
      console.log(`Requesting smart price for CTE ${cteId}...`);
      
      // Default dates as implemented in the component
      const d = new Date();
      d.setFullYear(d.getFullYear() - 1);
      const dateFrom = d.toISOString().split('T')[0];
      const dateTo = new Date().toISOString().split('T')[0];

      const smartData = await getSmartPrice(Number(cteId), dateFrom, dateTo);
      
      // 4. Verify smart price data
      expect(smartData).toBeDefined();
      expect(smartData?.cte_id).toBe(Number(cteId));
      expect(smartData?.mean_price).toBeDefined();
      
      console.log(`Smart Price for ${cteId}: ${smartData?.mean_price} руб.`);
      console.log(`Sample size: ${smartData?.sample_size_total}`);

    } catch (e: any) {
      if (e.status === 422) {
        console.warn("Integration test note: Backend returned 422 (Insufficient data), which is a valid business logic response.");
        expect(e.detail).toBeDefined();
      } else {
        throw e;
      }
    } finally {
      global.fetch = originalFetch;
    }
  }, 30000); // Increased timeout for real API calls
});
