// src/services/api.ts

const API_BASE = import.meta.env.VITE_API_URL

// ---------- Providers ----------
export const providerAPI = {
  async getProviders() {
    const res = await fetch(`${API_BASE}/providers`)
    if (!res.ok) throw new Error("Failed to load providers")
    return res.json()
  },

  async getSummary() {
    const res = await fetch(`${API_BASE}/summary`)
    if (!res.ok) throw new Error("Failed to load summary")
    return res.json()
  },

  async validateProvider(id: number) {
    const res = await fetch(`${API_BASE}/provider/${id}/validate`, {
      method: "POST",
    })
    if (!res.ok) {
      const payload = await res.json().catch(() => null)
      throw new Error(payload?.detail || "Failed to validate provider")
    }
    return res.json()
  },
}

// ---------- Discrepancies ----------
export const discrepancyAPI = {
  async getDiscrepancies() {
    const res = await fetch(`${API_BASE}/discrepancies`)
    if (!res.ok) throw new Error("Failed to load discrepancies")
    return res.json()
  },
}

// ---------- Export ----------
export const exportAPI = {
  async exportDirectory(format: "csv" | "json" = "csv") {
    const res = await fetch(`${API_BASE}/export?format=${format}`)
    if (!res.ok) {
      const payload = await res.json().catch(() => null)
      throw new Error(payload?.detail || "Failed to export directory")
    }
    return res.json()
  },
}
