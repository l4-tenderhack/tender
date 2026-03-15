export interface SearchQuery {
  query: string;
  category?: string | null;
  manufacturer?: string | null;
  price_min?: number | null;
  price_max?: number | null;
  characteristics?: Record<string, string> | null;
  limit?: number;
  offset?: number;
}

export interface SearchResult {
  cte_id: string;
  category: string;
  manufacturer: string;
  description: string;
  price: number;
  characteristics: Record<string, any>;
  score: number;
  category_boost: number;
  region?: string;
  date?: string | null;
}

export interface SearchResponse {
  total: number;
  execution_time_ms: number;
  results: SearchResult[];
}

export interface SuggestResponse {
  suggestions: string[];
}

export interface FacetItem {
  value: string;
  count: number;
}

export interface FacetsResponse {
  category?: FacetItem[];
  manufacturer?: FacetItem[];
  characteristics?: Record<string, FacetItem[]>;
}

export interface DocumentSource {
  name: string;
  supplier: string;
  price: number;
  date: string;
}

export interface GenerateDocRequest {
  cte_id: number;
  customer?: string;
  subject?: string;
  quantity?: number;
  unit?: string;
  date_from?: string | null;
  date_to?: string | null;
  sources?: DocumentSource[];
  nmck?: number;
  top_n?: number | null;
  score_threshold?: number | null;
}

export interface SearchNmckResponse {
  cte_id: number;
  cte_name: string | null;
  nmck_per_unit: string;
  price_min: string;
  price_max: string;
  mean_price: string;
  median_price: string;
  std_dev: string;
  coefficient_of_variation: string;
  is_homogeneous: boolean;
  confidence_interval_low: string;
  confidence_interval_high: string;
  sample_size_total: number;
  sample_size_filtered: number;
  outliers_removed: number;
  warnings: string[];
  method: string;
  contracts: ContractOut[];
  total_contracts: number;
}

export interface CteSearchRequest {
  query: string;
  n?: number;
  date_from?: string | null;
  date_to?: string | null;
  region?: string | null;
  inn?: string | null;
  score_threshold?: number | null;
}

export interface CteMatch {
  cte_id: string;
  cte_name: string;
  category: string;
  manufacturer: string;
  description: string;
  price: number;
  region: string;
  date: string | null;
  characteristics: Record<string, any>;
  score: number;
  category_boost: number;
}

export interface ContractItemOut {
  cte_id: number;
  cte_position_name: string | null;
  unit_price: string | null;
  quantity: string | null;
  unit_name: string | null;
}

export interface ContractOut {
  contract_id: number;
  contract_external_id: number;
  purchase_name: string;
  signed_at: string | null;
  buyer_inn: string | null;
  buyer_region: string | null;
  supplier_inn: string | null;
  items: ContractItemOut[];
}

export interface CteSearchResponse {
  query: string;
  matched_ctes: CteMatch[];
  contracts: ContractOut[];
  total_contracts: number;
  available_characteristics: Record<string, string[]>;
}

// Consts
const API_BASE_URL = '/api/v1';

export async function searchCte(query: SearchQuery): Promise<SearchResponse> {
  try {
    const body: any = {
      query: query.query,
      limit: query.limit ?? 20,
      offset: query.offset ?? 0,
    };

    if (query.category) body.category = query.category;
    if (query.manufacturer) body.manufacturer = query.manufacturer;
    if (query.price_min) body.price_min = query.price_min;
    if (query.price_max) body.price_max = query.price_max;
    if (query.characteristics) body.characteristics = query.characteristics;

    const response = await fetch(`${API_BASE_URL}/search/hybrid`, {
      method: 'POST',
      headers: {
        'accept': 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`Hybrid Search API Error ${response.status}: ${errorText}`);
      throw new Error(`API error: ${response.status} - ${errorText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to search CTE:', error);
    throw error;
  }
}

export async function getSuggest(prefix: string, limit: number = 10): Promise<string[]> {
  try {
    const queryParams = new URLSearchParams({
      prefix,
      limit: limit.toString()
    });
    
    const response = await fetch(`${API_BASE_URL}/search/suggest?${queryParams.toString()}`, {
      method: 'GET',
      headers: { 'accept': 'application/json' }
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data: SuggestResponse = await response.json();
    return data.suggestions;
  } catch (error) {
    console.error('Failed to get suggestions:', error);
    return [];
  }
}

export async function cteSearch(request: CteSearchRequest): Promise<CteSearchResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/cte-search`, {
      method: 'POST',
      headers: {
        'accept': 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`CTE Search API Error ${response.status}: ${errorText}`);
      throw new Error(`API error: ${response.status} - ${errorText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to search CTE:', error);
    throw error;
  }
}

export async function getFacets(q: string = '', category?: string, limit: number = 20): Promise<FacetsResponse> {
  try {
    const queryParams = new URLSearchParams({
      limit: limit.toString()
    });
    if (q) queryParams.append('q', q);
    if (category) queryParams.append('category', category);

    const response = await fetch(`${API_BASE_URL}/search/facets?${queryParams.toString()}`, {
      method: 'GET',
      headers: { 'accept': 'application/json' }
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to get facets:', error);
    return {};
  }
}

export async function generateNmckDoc(request: GenerateDocRequest, filename: string = 'nmck_report.docx'): Promise<void> {
  try {
    const response = await fetch(`${API_BASE_URL}/generate_doc`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  } catch (error) {
    console.error('Failed to generate NMCK document:', error);
    throw error;
  }
}

export interface ManualContractInput {
  unit_price: number;
  signed_at: string | null;
  supplier_inn: string | null;
}

export interface ManualNmckRequest {
  cte_id: number;
  contracts: ManualContractInput[];
}

export interface ManualNmckResponse {
  cte_id: number;
  cte_name: string | null;
  contracts: ManualContractInput[];
  nmck_per_unit: string;
  price_min: string;
  price_max: string;
  mean_price: string;
  median_price: string;
  std_dev: string;
  coefficient_of_variation: string;
  is_homogeneous: boolean;
  confidence_interval_low: string;
  confidence_interval_high: string;
  sample_size_total: number;
  sample_size_filtered: number;
  outliers_removed: number;
  warnings: string[];
  method: string;
}

export async function submitManualNmck(request: ManualNmckRequest): Promise<SearchNmckResponse> {
  const response = await fetch(`${API_BASE_URL}/nmck/manual`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorText = await response.text();
    let detail: unknown = errorText;
    try { detail = JSON.parse(errorText).detail; } catch {}
    throw { status: response.status, detail };
  }

  return response.json();
}

export async function getSmartPrice(
  cteId: string | number,
  dateFrom?: string,
  dateTo?: string,
  topN?: number | null,
  scoreThreshold?: number | null
): Promise<SearchNmckResponse> {
  try {
    const params = new URLSearchParams();
    if (dateFrom) params.append('date_from', dateFrom);
    if (dateTo) params.append('date_to', dateTo);
    if (topN != null && Number.isFinite(topN)) params.append('top_n', String(topN));
    if (scoreThreshold != null && Number.isFinite(scoreThreshold)) params.append('score_threshold', String(scoreThreshold));

    const response = await fetch(`${API_BASE_URL}/nmck/${cteId}?${params.toString()}`, {
      method: 'GET',
      headers: {
        'accept': 'application/json',
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`API Error ${response.status} for ${cteId}: ${errorText}`);
      if (response.status === 422) {
        let errorData;
        try {
          errorData = JSON.parse(errorText);
        } catch (e) {
          errorData = { detail: errorText };
        }
        throw { status: 422, detail: errorData.detail };
      }
      throw new Error(`API error: ${response.status} - ${errorText}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`Failed to get smart price for ${cteId}:`, error);
    throw error;
  }
}
