import React, { useState } from 'react'
import { providerAPI, validationAPI } from '../services/api'
import './UploadPage.css'

function UploadPage() {
  const [csvFile, setCsvFile] = useState(null)
  const [pdfFile, setPdfFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [message, setMessage] = useState(null)
  const [messageType, setMessageType] = useState(null)

  const handleCSVUpload = async (e) => {
    const file = e.target.files[0]
    if (file && file.type === 'text/csv') {
      setCsvFile(file)
    } else {
      setMessage('Please select a valid CSV file')
      setMessageType('error')
    }
  }

  const handlePDFUpload = async (e) => {
    const file = e.target.files[0]
    if (file && file.type === 'application/pdf') {
      setPdfFile(file)
    } else {
      setMessage('Please select a valid PDF file')
      setMessageType('error')
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!csvFile) {
      setMessage('Please select a CSV file to upload')
      setMessageType('error')
      return
    }

    setUploading(true)
    setMessage(null)

    try {
      // Upload CSV
      const csvResult = await providerAPI.uploadCSV(csvFile)
      
      // Upload PDF if provided
      if (pdfFile) {
        await validationAPI.uploadPDF(pdfFile)
      }

      setMessage(`Successfully uploaded ${csvResult.uploaded} providers`)
      setMessageType('success')
      
      // Reset form
      setCsvFile(null)
      setPdfFile(null)
      e.target.reset()
    } catch (error) {
      setMessage(error.response?.data?.detail || 'Error uploading files')
      setMessageType('error')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="upload-page">
      <div className="page-header">
        <h1>Upload Provider Data</h1>
        <p>Upload CSV files and PDF documents for provider validation</p>
      </div>

      <div className="card">
        <form onSubmit={handleSubmit}>
          {message && (
            <div className={messageType === 'error' ? 'error' : 'success'}>
              {message}
            </div>
          )}

          <div className="form-group">
            <label className="label">CSV File (Required)</label>
            <input
              type="file"
              accept=".csv"
              onChange={handleCSVUpload}
              className="input"
              disabled={uploading}
            />
            {csvFile && (
              <p className="file-info">Selected: {csvFile.name}</p>
            )}
          </div>

          <div className="form-group">
            <label className="label">PDF Document (Optional)</label>
            <input
              type="file"
              accept=".pdf"
              onChange={handlePDFUpload}
              className="input"
              disabled={uploading}
            />
            {pdfFile && (
              <p className="file-info">Selected: {pdfFile.name}</p>
            )}
            <p className="help-text">
              Upload scanned PDFs for OCR extraction of provider information
            </p>
          </div>

          <button
            type="submit"
            className="button"
            disabled={uploading || !csvFile}
          >
            {uploading ? 'Uploading...' : 'Upload Files'}
          </button>
        </form>
      </div>

      <div className="card">
        <h2>CSV Format Requirements</h2>
        <p>Your CSV file should include the following columns:</p>
        <ul className="format-list">
          <li>NPI</li>
          <li>First Name</li>
          <li>Last Name</li>
          <li>Organization Name</li>
          <li>Provider Type</li>
          <li>Specialty</li>
          <li>Address Line 1</li>
          <li>Address Line 2</li>
          <li>City</li>
          <li>State</li>
          <li>ZIP Code</li>
          <li>Phone</li>
          <li>Email</li>
          <li>Website</li>
          <li>License Number</li>
          <li>License State</li>
          <li>Practice Name</li>
        </ul>
      </div>
    </div>
  )
}

export default UploadPage

