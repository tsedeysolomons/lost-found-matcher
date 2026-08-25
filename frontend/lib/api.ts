/**
 * API client for Lost and Found backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface Report {
  id: number
  type: 'Lost' | 'Found'
  item: string
  category: string
  color: string
  location: string
  date: string
  status: string
  details: string
  created_at: string
  updated_at: string
}

export interface ComponentScores {
  item_category: number
  vector: number
  keywords: number
  location: number
  color: number
  date: number
}

export interface MatchResponse {
  lost_report: Report
  found_report: Report
  score: number
  component_scores: ComponentScores
  reasons: string[]
}

export interface ReportWithMatches {
  report: Report
  matches: MatchResponse[]
  warning?: string
}

export interface CreateReportData {
  type: 'Lost' | 'Found'
  item: string
  category: string
  color: string
  location: string
  date: string
  details?: string
}

/**
 * Create a new report and get potential matches
 */
export async function createReport(data: CreateReportData): Promise<ReportWithMatches> {
  const response = await fetch(`${API_BASE_URL}/api/reports`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'API error' }))
    throw new Error(error.detail || `API error: ${response.status}`)
  }
  
  return response.json()
}

/**
 * Get all reports with optional filtering
 */
export async function getReports(type?: 'Lost' | 'Found'): Promise<Report[]> {
  const url = new URL(`${API_BASE_URL}/api/reports`)
  if (type) {
    url.searchParams.set('report_type', type)
  }
  
  console.log('Fetching reports from:', url.toString())
  
  const response = await fetch(url.toString(), {
    cache: 'no-store', // Prevent caching issues
  })
  
  console.log('Response status:', response.status)
  
  if (!response.ok) {
    const errorText = await response.text()
    console.error('API error response:', errorText)
    throw new Error(`API error: ${response.status}`)
  }
  
  const data = await response.json()
  console.log('Fetched reports:', data)
  return data
}

/**
 * Get a single report by ID
 */
export async function getReport(reportId: number): Promise<Report> {
  const response = await fetch(`${API_BASE_URL}/api/reports/${reportId}`)
  
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`)
  }
  
  return response.json()
}

/**
 * Get potential matches for a specific report
 */
export async function getMatches(reportId: number, threshold: number = 35.0): Promise<MatchResponse[]> {
  const url = new URL(`${API_BASE_URL}/api/reports/${reportId}/matches`)
  url.searchParams.set('threshold', threshold.toString())
  
  const response = await fetch(url.toString())
  
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`)
  }
  
  return response.json()
}
