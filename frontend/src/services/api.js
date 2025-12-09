/**
 * API service layer for MedAtlas frontend.
 * Handles all API calls to the FastAPI backend.
 */

import axios from 'axios'

const API_BASE_URL = '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * Provider API endpoints
 */
export const providerAPI = {
  /**
   * Upload provider CSV file
   */
  uploadCSV: async (file) => {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  /**
   * Get all providers (simplified endpoint)
   */
  getProviders: async () => {
    const response = await api.get('/providers')
    return response.data
  },

  /**
   * Get provider by ID
   */
  getProvider: async (providerId) => {
    const response = await api.get(`/provider/${providerId}`)
    return response.data
  },

  /**
   * Get summary statistics
   */
  getSummary: async () => {
    const response = await api.get('/summary')
    return response.data
  },
}

/**
 * Validation API endpoints
 */
export const validationAPI = {
  /**
   * Run validation pipeline for all providers
   */
  runValidation: async () => {
    const response = await api.post('/validate')
    return response.data
  },

  /**
   * Validate a single provider
   */
  validateProvider: async (providerId, npi = null, forceRevalidate = false) => {
    const response = await api.post('/validate-provider', {
      provider_id: providerId,
      npi: npi,
      force_revalidate: forceRevalidate,
    })
    return response.data
  },

  /**
   * Upload PDF for OCR extraction
   */
  uploadPDF: async (file) => {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await api.post('/upload-pdf', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },
}

/**
 * Discrepancy API endpoints
 */
export const discrepancyAPI = {
  /**
   * Get discrepancies
   */
  getDiscrepancies: async (providerId = null, status = null) => {
    const params = {}
    if (providerId) params.provider_id = providerId
    if (status) params.status = status
    
    const response = await api.get('/discrepancies', { params })
    return response.data
  },

  /**
   * Get discrepancy by ID
   */
  getDiscrepancy: async (discrepancyId) => {
    const response = await api.get(`/discrepancies/${discrepancyId}`)
    return response.data
  },

  /**
   * Update discrepancy
   */
  updateDiscrepancy: async (discrepancyId, status = null, notes = null) => {
    const response = await api.patch(`/discrepancies/${discrepancyId}`, {
      status,
      notes,
    })
    return response.data
  },
}

/**
 * Export API endpoints
 */
export const exportAPI = {
  /**
   * Export directory
   */
  exportDirectory: async (format = 'csv', providerIds = null, includeDiscrepancies = true) => {
    const response = await api.post('/export', {
      format,
      provider_ids: providerIds,
      include_discrepancies: includeDiscrepancies,
    })
    return response.data
  },

  /**
   * Download export file
   */
  downloadExport: async (filename) => {
    const response = await api.get(`/export/download/${filename}`, {
      responseType: 'blob',
    })
    return response.data
  },
}

/**
 * Standalone export functions for convenience
 */
export const getProviders = () => providerAPI.getProviders()
export const runValidation = () => validationAPI.runValidation()

export default api

