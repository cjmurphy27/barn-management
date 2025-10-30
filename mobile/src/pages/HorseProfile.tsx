import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { horseApi, medicalApi, feedApi, trainingApi, apiClient, buildApiUrl } from '../services/api'

interface Horse {
  id: string
  name: string
  barn_name?: string
  breed?: string
  color?: string
  gender?: 'mare' | 'stallion' | 'gelding'
  age_years?: number
  age_display?: string
  height_hands?: string
  weight_lbs?: number
  body_condition_score?: number

  // Registration & Identification
  registration_number?: string
  registration_organization?: string
  microchip_number?: string
  passport_number?: string

  // Location & Management
  current_location?: string
  stall_number?: string
  pasture_group?: string
  boarding_type?: string
  owner_name?: string
  owner_contact?: string

  // Training & Disciplines
  training_level?: string
  disciplines?: string
  trainer_name?: string
  trainer_contact?: string

  // Care Schedule
  feeding_schedule?: string
  exercise_schedule?: string
  feeding_notes?: string
  training_notes?: string

  // Health Information
  current_health_status?: 'Excellent' | 'Good' | 'Fair' | 'Poor' | 'Critical'
  allergies?: string
  medications?: string
  special_needs?: string
  veterinarian_name?: string
  veterinarian_contact?: string
  farrier_name?: string
  emergency_contact_name?: string
  emergency_contact_phone?: string

  // Health History
  last_vet_visit?: string
  last_dental?: string
  last_farrier?: string

  // Additional Fields
  markings?: string
  physical_notes?: string
  notes?: string
  special_instructions?: string
  profile_photo_path?: string
  is_active?: boolean
  is_retired?: boolean
  is_for_sale?: boolean
  created_at: string
  updated_at: string

  // Legacy/Mobile fields
  status?: 'active' | 'inactive' | 'sold'
  photo_url?: string
}

interface Document {
  id: string
  filename: string
  file_type: string
  file_size: number
  upload_date: string
  category: string
  description?: string
  document_category?: string
  title?: string
}

interface User {
  user_id: string
  email: string
  organizations: Array<{
    barn_id: string
    barn_name: string
    user_role: string
    permissions: string[]
  }>
}

interface HorseProfileProps {
  user: User
  selectedBarnId: string | null
}

export default function HorseProfile({ user, selectedBarnId }: HorseProfileProps) {
  const { id } = useParams<{ id: string }>()
  const [horse, setHorse] = useState<Horse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState('basic')
  const [photoData, setPhotoData] = useState<string | null>(null)
  const [photoLoading, setPhotoLoading] = useState(false)
  const [documents, setDocuments] = useState<Document[]>([])
  const [documentsLoading, setDocumentsLoading] = useState(false)
  const [uploadingDocument, setUploadingDocument] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [editFormData, setEditFormData] = useState<Partial<Horse>>({})
  const [saving, setSaving] = useState(false)
  const [uploadingPhoto, setUploadingPhoto] = useState(false)

  // Enhanced document upload state
  const [documentCategory, setDocumentCategory] = useState('')
  const [documentTitle, setDocumentTitle] = useState('')
  const [documentDescription, setDocumentDescription] = useState('')
  const [takingPhoto, setTakingPhoto] = useState(false)
  const [cameraStream, setCameraStream] = useState<MediaStream | null>(null)
  const [showCamera, setShowCamera] = useState(false)
  const [stagedFile, setStagedFile] = useState<File | null>(null)
  const [savingDocument, setSavingDocument] = useState(false)

  useEffect(() => {
    if (id && user && selectedBarnId) {
      loadHorseData()
    }
  }, [id, user, selectedBarnId])

  const loadHorseData = async () => {
    if (!selectedBarnId) {
      console.log('No barn selected, skipping horse loading')
      setLoading(false)
      return
    }

    setLoading(true)
    setError(null)

    try {
      const accessToken = localStorage.getItem('access_token')
      if (!accessToken) {
        throw new Error('Not authenticated')
      }

      apiClient.setToken(accessToken)

      // Use the selected barn ID directly
      const response = await horseApi.getById(id!, selectedBarnId)

      if (response.success) {
        const horseData = response.data as Horse
        setHorse(horseData)

        // Load horse photo if profile_photo_path exists
        if (horseData.profile_photo_path) {
          loadHorsePhoto(horseData.id, selectedBarnId)
        }

        // Initialize edit form data
        setEditFormData(horseData)

        // Load documents
        loadDocuments(horseData.id, selectedBarnId)
      } else {
        throw new Error(response.error || 'Failed to load horse data')
      }
    } catch (error) {
      console.error('Failed to load horse:', error)
      setError(error instanceof Error ? error.message : 'Failed to load horse')
    }

    setLoading(false)
  }

  const loadHorsePhoto = async (horseId: string, organizationId: string) => {
    setPhotoLoading(true)
    try {
      const accessToken = localStorage.getItem('access_token')
      if (!accessToken) return

      const headers: Record<string, string> = accessToken === 'dev_token_placeholder'
        ? {}
        : { 'Authorization': `Bearer ${accessToken}` }

      const photoUrl = buildApiUrl(`/api/v1/horses/${horseId}/photo?organization_id=${organizationId}`)
      const response = await fetch(photoUrl, { headers })

      if (response.ok) {
        const blob = await response.blob()
        const photoDataUrl = URL.createObjectURL(blob)
        setPhotoData(photoDataUrl)
      }
    } catch (error) {
      console.error('Failed to load horse photo:', error)
    }
    setPhotoLoading(false)
  }

  const loadDocuments = async (horseId: string, organizationId: string) => {
    setDocumentsLoading(true)
    try {
      const accessToken = localStorage.getItem('access_token')
      if (!accessToken) return

      const headers: Record<string, string> = accessToken === 'dev_token_placeholder'
        ? {}
        : { 'Authorization': `Bearer ${accessToken}` }

      const documentsUrl = buildApiUrl(`/api/v1/horses/${horseId}/documents?organization_id=${organizationId}`)
      const response = await fetch(documentsUrl, { headers })

      if (response.ok) {
        const documentsData = await response.json()
        setDocuments(documentsData.documents || [])
      }
    } catch (error) {
      console.error('Failed to load documents:', error)
    }
    setDocumentsLoading(false)
  }

  const handlePhotoUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file || !horse || !selectedBarnId) return

    // Validate file type
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file')
      return
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      alert('Image file size must be less than 10MB')
      return
    }

    setUploadingPhoto(true)
    try {
      const accessToken = localStorage.getItem('access_token')
      if (!accessToken) {
        throw new Error('Not authenticated')
      }

      const formData = new FormData()
      formData.append('photo', file)

      const headers: Record<string, string> = accessToken === 'dev_token_placeholder'
        ? {}
        : { 'Authorization': `Bearer ${accessToken}` }

      const uploadUrl = buildApiUrl(`/api/v1/horses/${horse.id}/photo?organization_id=${selectedBarnId}`)
      const response = await fetch(uploadUrl, {
        method: 'POST',
        headers,
        body: formData
      })

      if (response.ok) {
        // Reload the complete horse data from the backend to get the correct profile_photo_path
        await loadHorseData()
      } else {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || 'Upload failed')
      }
    } catch (error) {
      console.error('Failed to upload photo:', error)
      alert(`Failed to upload photo: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
    setUploadingPhoto(false)
    // Reset file input
    event.target.value = ''
  }

  const handleFileSelection = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    // Validate file type
    const allowedTypes = ['.pdf', '.doc', '.docx', '.txt', '.jpg', '.jpeg', '.png', '.tiff', '.gif', '.mp4', '.mov']
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase()
    if (!allowedTypes.includes(fileExtension)) {
      alert('File type not supported. Please select a PDF, DOC, TXT, image, or video file.')
      return
    }

    // Validate file size (max 50MB)
    if (file.size > 50 * 1024 * 1024) {
      alert('File size must be less than 50MB')
      return
    }

    setStagedFile(file)
    // Don't reset file input here - let it show the selected file
  }

  const saveDocument = async () => {
    if (!stagedFile || !horse || !selectedBarnId) return

    setSavingDocument(true)
    try {
      const accessToken = localStorage.getItem('access_token')
      if (!accessToken) {
        throw new Error('Not authenticated')
      }

      const formData = new FormData()
      formData.append('file', stagedFile)

      // Add category if selected
      if (documentCategory) {
        formData.append('document_category', documentCategory)
      }

      // Add title if provided
      if (documentTitle) {
        formData.append('title', documentTitle)
      }

      // Add description if provided
      if (documentDescription) {
        formData.append('description', documentDescription)
      }

      const headers: Record<string, string> = accessToken === 'dev_token_placeholder'
        ? {}
        : { 'Authorization': `Bearer ${accessToken}` }

      const uploadUrl = buildApiUrl(`/api/v1/horses/${horse.id}/documents?organization_id=${selectedBarnId}`)
      const response = await fetch(uploadUrl, {
        method: 'POST',
        headers,
        body: formData
      })

      if (response.ok) {
        // Clear form fields and staged file
        setDocumentCategory('')
        setDocumentTitle('')
        setDocumentDescription('')
        setStagedFile(null)

        // Reset file input
        const fileInput = document.getElementById('file-upload') as HTMLInputElement
        if (fileInput) fileInput.value = ''

        // Reload documents
        loadDocuments(horse.id, selectedBarnId)
      } else {
        throw new Error('Upload failed')
      }
    } catch (error) {
      console.error('Failed to upload document:', error)
      alert('Failed to upload document. Please try again.')
    }
    setSavingDocument(false)
  }

  const clearDocumentForm = () => {
    setDocumentCategory('')
    setDocumentTitle('')
    setDocumentDescription('')
    setStagedFile(null)
    const fileInput = document.getElementById('file-upload') as HTMLInputElement
    if (fileInput) fileInput.value = ''
  }

  const deleteDocument = async (documentId: string) => {
    if (!horse || !selectedBarnId) return

    try {
      const accessToken = localStorage.getItem('access_token')
      if (!accessToken) return

      const headers: Record<string, string> = accessToken === 'dev_token_placeholder'
        ? {}
        : { 'Authorization': `Bearer ${accessToken}` }

      const deleteUrl = buildApiUrl(`/api/v1/horses/${horse.id}/documents/${documentId}?organization_id=${selectedBarnId}`)
      const response = await fetch(deleteUrl, {
        method: 'DELETE',
        headers
      })

      if (response.ok) {
        // Reload documents
        loadDocuments(horse.id, selectedBarnId)
      }
    } catch (error) {
      console.error('Failed to delete document:', error)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const getFileIcon = (fileType: string) => {
    const type = fileType.toLowerCase()
    if (type.includes('pdf')) return '📄'
    if (type.includes('image')) return '🖼️'
    if (type.includes('video')) return '🎥'
    if (type.includes('text') || type.includes('document')) return '📝'
    return '📎'
  }

  // Document categories from Streamlit
  const documentCategories = {
    "medical_record": "🏥 Medical Record",
    "veterinary_report": "👩‍⚕️ Veterinary Report",
    "vaccination_record": "💉 Vaccination Record",
    "training_notes": "🏃 Training Notes",
    "feed_evaluation": "🌾 Feed Evaluation",
    "behavioral_notes": "🧠 Behavioral Notes",
    "breeding_record": "🐎 Breeding Record",
    "ownership_papers": "📋 Ownership Papers",
    "insurance_document": "🛡️ Insurance Document",
    "competition_record": "🏆 Competition Record",
    "general": "📄 General"
  }

  // Camera functionality
  const startCamera = async () => {
    try {
      setTakingPhoto(true)
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' },
        audio: false
      })
      setCameraStream(stream)
      setShowCamera(true)
    } catch (error) {
      console.error('Error accessing camera:', error)
      alert('Unable to access camera. Please check permissions.')
      setTakingPhoto(false)
    }
  }

  const stopCamera = () => {
    if (cameraStream) {
      cameraStream.getTracks().forEach(track => track.stop())
      setCameraStream(null)
    }
    setShowCamera(false)
    setTakingPhoto(false)
  }

  const capturePhoto = async () => {
    if (!cameraStream || !horse || !selectedBarnId) return

    try {
      const video = document.getElementById('camera-video') as HTMLVideoElement
      const canvas = document.createElement('canvas')
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight

      const ctx = canvas.getContext('2d')
      if (!ctx) return

      ctx.drawImage(video, 0, 0)

      canvas.toBlob(async (blob) => {
        if (!blob) return

        // Create a File object from the blob
        const fileName = `camera-capture-${Date.now()}.jpg`
        const file = new File([blob], fileName, { type: 'image/jpeg' })

        // Stage the captured file
        setStagedFile(file)

        // Stop camera
        stopCamera()
      }, 'image/jpeg', 0.8)

    } catch (error) {
      console.error('Error capturing photo:', error)
      alert('Failed to capture photo. Please try again.')
      setTakingPhoto(false)
    }
  }

  const getCategoryIcon = (category: string) => {
    return documentCategories[category as keyof typeof documentCategories]?.split(' ')[0] || '📎'
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800'
      case 'inactive': return 'bg-yellow-100 text-yellow-800'
      case 'sold': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getGenderIcon = (gender?: string) => {
    switch (gender) {
      case 'mare': return '♀'
      case 'stallion': return '♂'
      case 'gelding': return '⚲'
      default: return '?'
    }
  }

  const getHealthStatusColor = (status: string) => {
    switch (status) {
      case 'Excellent': return 'bg-green-100 text-green-800'
      case 'Good': return 'bg-blue-100 text-blue-800'
      case 'Fair': return 'bg-yellow-100 text-yellow-800'
      case 'Poor': return 'bg-orange-100 text-orange-800'
      case 'Critical': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getHealthStatusEmoji = (status: string) => {
    switch (status) {
      case 'Excellent': return '🟢'
      case 'Good': return '🔵'
      case 'Fair': return '🟡'
      case 'Poor': return '🟠'
      case 'Critical': return '🔴'
      default: return '⚪'
    }
  }

  const handleSaveChanges = async () => {
    if (!horse || !selectedBarnId) return

    setSaving(true)
    try {
      const accessToken = localStorage.getItem('access_token')
      if (!accessToken) {
        throw new Error('Not authenticated')
      }

      const headers: Record<string, string> = accessToken === 'dev_token_placeholder'
        ? { 'Content-Type': 'application/json' }
        : {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        }

      const response = await fetch(
        buildApiUrl(`/api/v1/horses/${horse.id}?organization_id=${selectedBarnId}`),
        {
          method: 'PUT',
          headers,
          body: JSON.stringify(editFormData)
        }
      )

      if (response.ok) {
        const updatedHorse = await response.json()
        setHorse(updatedHorse)
        setEditFormData(updatedHorse)
        setIsEditing(false)
      } else {
        throw new Error('Failed to update horse')
      }
    } catch (error) {
      console.error('Error updating horse:', error)
      alert('Failed to save changes. Please try again.')
    }
    setSaving(false)
  }

  const handleCancelEdit = () => {
    setEditFormData(horse || {})
    setIsEditing(false)
  }

  const handleInputChange = (field: keyof Horse, value: string | number) => {
    setEditFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading horse...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 mb-4">
          <svg className="w-12 h-12 mx-auto" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">Error Loading Horse</h3>
        <p className="text-gray-600 mb-4">{error}</p>
        <div className="space-x-3">
          <button
            onClick={loadHorseData}
            className="btn-primary"
          >
            Try Again
          </button>
          <Link
            to="/horses"
            className="btn-secondary"
          >
            Back to Horses
          </Link>
        </div>
      </div>
    )
  }

  if (!horse) {
    return (
      <div className="text-center py-12">
        <h3 className="text-lg font-medium text-gray-900 mb-2">Horse Not Found</h3>
        <p className="text-gray-600 mb-4">The horse you're looking for doesn't exist.</p>
        <Link to="/horses" className="btn-primary">
          Back to Horses
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header with Back Button */}
      <div className="flex items-center justify-between">
        <Link
          to="/horses"
          className="flex items-center text-primary-600 hover:text-primary-700"
        >
          <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clipRule="evenodd" />
          </svg>
          Back to Horses
        </Link>
        <div className="flex items-center space-x-3">
          {isEditing ? (
            <div className="flex items-center space-x-2">
              <button
                onClick={handleSaveChanges}
                disabled={saving}
                className="bg-green-600 text-white text-sm font-medium py-2 px-4 rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2 disabled:opacity-50"
              >
                {saving ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>Saving...</span>
                  </>
                ) : (
                  <>
                    <span>💾</span>
                    <span>Save</span>
                  </>
                )}
              </button>
              <button
                onClick={handleCancelEdit}
                disabled={saving}
                className="bg-gray-500 text-white text-sm font-medium py-2 px-4 rounded-lg hover:bg-gray-600 transition-colors flex items-center space-x-2 disabled:opacity-50"
              >
                <span>❌</span>
                <span>Cancel</span>
              </button>
            </div>
          ) : (
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setIsEditing(true)}
                className="bg-orange-500 text-white text-sm font-medium py-2 px-4 rounded-lg hover:bg-orange-600 transition-colors flex items-center space-x-2"
              >
                <span>✏️</span>
                <span>Edit</span>
              </button>
              <Link
                to={`/horses/${horse.id}/ai`}
                className="bg-gradient-to-r from-blue-500 to-purple-600 text-white text-sm font-medium py-2 px-4 rounded-lg hover:from-blue-600 hover:to-purple-700 transition-colors flex items-center space-x-2"
              >
                <span>🤖</span>
                <span>Ask AI</span>
              </Link>
            </div>
          )}
          {horse.status && (
            <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(horse.status)}`}>
              {horse.status}
            </span>
          )}
        </div>
      </div>

      {/* Horse Header */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-start space-x-4">
          {/* Horse Photo */}
          <div className="flex-shrink-0 relative">
            {photoLoading ? (
              <div className="w-24 h-24 bg-gray-100 rounded-lg flex items-center justify-center">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
              </div>
            ) : photoData ? (
              <img
                src={photoData}
                alt={horse.name}
                className="w-24 h-24 rounded-lg object-cover"
              />
            ) : horse.photo_url ? (
              <img
                src={horse.photo_url}
                alt={horse.name}
                className="w-24 h-24 rounded-lg object-cover"
              />
            ) : (
              <div className="w-24 h-24 bg-primary-100 rounded-lg flex items-center justify-center">
                <span className="text-primary-600 font-semibold text-2xl">
                  {getGenderIcon(horse.gender)}
                </span>
              </div>
            )}
            {/* Photo Upload Button - only show when editing */}
            {isEditing && (
              <div className="absolute -bottom-2 -right-2">
                <label htmlFor="photo-upload" className="cursor-pointer">
                  <div className="bg-primary-600 hover:bg-primary-700 text-white rounded-full p-2 shadow-lg transition-colors">
                    {uploadingPhoto ? (
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    ) : (
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                    )}
                  </div>
                  <input
                    id="photo-upload"
                    name="photo-upload"
                    type="file"
                    className="sr-only"
                    onChange={handlePhotoUpload}
                    disabled={uploadingPhoto}
                    accept="image/*"
                  />
                </label>
              </div>
            )}
          </div>

          {/* Horse Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">{horse.name}</h1>
                {horse.barn_name && (
                  <p className="text-lg text-gray-600 font-medium">{horse.barn_name}</p>
                )}
              </div>
              {horse.current_health_status && (
                <div className={`px-3 py-1 rounded-full text-sm font-medium ${getHealthStatusColor(horse.current_health_status)}`}>
                  {getHealthStatusEmoji(horse.current_health_status)} {horse.current_health_status}
                </div>
              )}
            </div>
            <div className="mt-2 space-y-1">
              {horse.breed && (
                <p className="text-gray-600">
                  <span className="font-medium">Breed:</span> {horse.breed}
                </p>
              )}
              {horse.age_display && (
                <p className="text-gray-600">
                  <span className="font-medium">Age:</span> {horse.age_display}
                </p>
              )}
              {horse.color && (
                <p className="text-gray-600">
                  <span className="font-medium">Color:</span> {horse.color}
                </p>
              )}
              {horse.gender && (
                <p className="text-gray-600">
                  <span className="font-medium">Gender:</span> {horse.gender}
                </p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="border-b border-gray-200 overflow-x-auto sticky top-0 z-10 bg-white">
          <nav className="-mb-px flex space-x-8 px-6 min-w-max scroll-smooth snap-x snap-mandatory">
            {[
              { id: 'basic', name: 'Basic Info' },
              { id: 'physical', name: 'Physical' },
              { id: 'management', name: 'Management' },
              { id: 'health', name: 'Health' },
              { id: 'notes', name: 'Notes' },
              { id: 'documents', name: 'Documents' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`${
                  activeTab === tab.id
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-4 px-4 border-b-2 font-medium text-sm flex-shrink-0 snap-start`}
              >
                {tab.name}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6 min-h-[600px] md:min-h-[400px]">
          {activeTab === 'basic' && (
            <div className="space-y-6">
              {isEditing ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                    <input
                      type="text"
                      value={editFormData.name || ''}
                      onChange={(e) => handleInputChange('name', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Breed</label>
                    <input
                      type="text"
                      value={editFormData.breed || ''}
                      onChange={(e) => handleInputChange('breed', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Color</label>
                    <input
                      type="text"
                      value={editFormData.color || ''}
                      onChange={(e) => handleInputChange('color', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Gender</label>
                    <select
                      value={editFormData.gender || ''}
                      onChange={(e) => handleInputChange('gender', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    >
                      <option value="">Select Gender</option>
                      <option value="mare">Mare</option>
                      <option value="stallion">Stallion</option>
                      <option value="gelding">Gelding</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Registration Number</label>
                    <input
                      type="text"
                      value={editFormData.registration_number || ''}
                      onChange={(e) => handleInputChange('registration_number', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Registry</label>
                    <input
                      type="text"
                      value={editFormData.registration_organization || ''}
                      onChange={(e) => handleInputChange('registration_organization', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Microchip</label>
                    <input
                      type="text"
                      value={editFormData.microchip_number || ''}
                      onChange={(e) => handleInputChange('microchip_number', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Passport</label>
                    <input
                      type="text"
                      value={editFormData.passport_number || ''}
                      onChange={(e) => handleInputChange('passport_number', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {horse.registration_number && (
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Registration Number</dt>
                      <dd className="mt-1 text-sm text-gray-900">{horse.registration_number}</dd>
                    </div>
                  )}
                  {horse.registration_organization && (
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Registry</dt>
                      <dd className="mt-1 text-sm text-gray-900">{horse.registration_organization}</dd>
                    </div>
                  )}
                  {horse.microchip_number && (
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Microchip</dt>
                      <dd className="mt-1 text-sm text-gray-900">{horse.microchip_number}</dd>
                    </div>
                  )}
                  {horse.passport_number && (
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Passport</dt>
                      <dd className="mt-1 text-sm text-gray-900">{horse.passport_number}</dd>
                    </div>
                  )}
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Status</dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      {horse.is_active ? 'Active' : 'Inactive'}
                      {horse.is_retired && ' • Retired'}
                      {horse.is_for_sale && ' • For Sale'}
                    </dd>
                  </div>
                </div>
              )}
              {!isEditing && (
                <div className="text-xs text-gray-500 border-t pt-4">
                  <p>Created: {new Date(horse.created_at).toLocaleDateString()}</p>
                  <p>Updated: {new Date(horse.updated_at).toLocaleDateString()}</p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'physical' && (
            <div className="space-y-6">
              {isEditing ? (
                <div className="space-y-6">
                  {/* Editable Physical Info Form */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Height (hands)
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        value={editFormData.height_hands || ''}
                        onChange={(e) => setEditFormData(prev => ({ ...prev, height_hands: e.target.value || undefined }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                        placeholder="15.2"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Weight (lbs)
                      </label>
                      <input
                        type="number"
                        value={editFormData.weight_lbs || ''}
                        onChange={(e) => setEditFormData(prev => ({ ...prev, weight_lbs: e.target.value ? parseInt(e.target.value) : undefined }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                        placeholder="1000"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Body Condition Score (1-9)
                      </label>
                      <select
                        value={editFormData.body_condition_score || ''}
                        onChange={(e) => setEditFormData(prev => ({ ...prev, body_condition_score: e.target.value ? parseInt(e.target.value) : undefined }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      >
                        <option value="">Select score</option>
                        {[1, 2, 3, 4, 5, 6, 7, 8, 9].map(score => (
                          <option key={score} value={score}>{score}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Markings
                    </label>
                    <textarea
                      value={editFormData.markings || ''}
                      onChange={(e) => setEditFormData(prev => ({ ...prev, markings: e.target.value }))}
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      placeholder="Describe any distinctive markings..."
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Physical Notes
                    </label>
                    <textarea
                      value={editFormData.physical_notes || ''}
                      onChange={(e) => setEditFormData(prev => ({ ...prev, physical_notes: e.target.value }))}
                      rows={4}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      placeholder="Any physical observations, injuries, or special considerations..."
                    />
                  </div>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Read-only Physical Info Display */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {horse.height_hands && (
                      <div>
                        <dt className="text-sm font-medium text-gray-500">Height</dt>
                        <dd className="mt-1 text-sm text-gray-900">{horse.height_hands} hands</dd>
                      </div>
                    )}
                    {horse.weight_lbs && (
                      <div>
                        <dt className="text-sm font-medium text-gray-500">Weight</dt>
                        <dd className="mt-1 text-sm text-gray-900">{horse.weight_lbs} lbs</dd>
                      </div>
                    )}
                    {horse.body_condition_score && (
                      <div>
                        <dt className="text-sm font-medium text-gray-500">Body Condition Score</dt>
                        <dd className="mt-1 text-sm text-gray-900">{horse.body_condition_score}/9</dd>
                      </div>
                    )}
                  </div>
                  {horse.markings && (
                    <div>
                      <dt className="text-sm font-medium text-gray-500 mb-2">Markings</dt>
                      <dd className="text-sm text-gray-900">{horse.markings}</dd>
                    </div>
                  )}
                  {horse.physical_notes && (
                    <div>
                      <dt className="text-sm font-medium text-gray-500 mb-2">Physical Notes</dt>
                      <dd className="text-sm text-gray-900">{horse.physical_notes}</dd>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {activeTab === 'management' && (
            <div className="space-y-6">
              {isEditing ? (
                <div className="space-y-6">
                  {/* Editable Management Info Form */}
                  <div className="space-y-4">
                    <h3 className="text-lg font-medium text-gray-900">Location & Care</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Current Location
                        </label>
                        <input
                          type="text"
                          value={editFormData.current_location || ''}
                          onChange={(e) => setEditFormData(prev => ({ ...prev, current_location: e.target.value }))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                          placeholder="Pasture 1, Stall 12, etc."
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Stall Number
                        </label>
                        <input
                          type="text"
                          value={editFormData.stall_number || ''}
                          onChange={(e) => setEditFormData(prev => ({ ...prev, stall_number: e.target.value }))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                          placeholder="12"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Pasture Group
                        </label>
                        <input
                          type="text"
                          value={editFormData.pasture_group || ''}
                          onChange={(e) => setEditFormData(prev => ({ ...prev, pasture_group: e.target.value }))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                          placeholder="Group A, Mares, etc."
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Boarding Type
                        </label>
                        <select
                          value={editFormData.boarding_type || ''}
                          onChange={(e) => setEditFormData(prev => ({ ...prev, boarding_type: e.target.value }))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                        >
                          <option value="">Select boarding type</option>
                          <option value="Full Board">Full Board</option>
                          <option value="Partial Board">Partial Board</option>
                          <option value="Self Care">Self Care</option>
                          <option value="Training Board">Training Board</option>
                          <option value="Pasture Board">Pasture Board</option>
                        </select>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h3 className="text-lg font-medium text-gray-900">Owner & Training</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Owner Name
                        </label>
                        <input
                          type="text"
                          value={editFormData.owner_name || ''}
                          onChange={(e) => setEditFormData(prev => ({ ...prev, owner_name: e.target.value }))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                          placeholder="Owner's full name"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Owner Contact
                        </label>
                        <input
                          type="text"
                          value={editFormData.owner_contact || ''}
                          onChange={(e) => setEditFormData(prev => ({ ...prev, owner_contact: e.target.value }))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                          placeholder="Phone number or email"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Trainer Name
                        </label>
                        <input
                          type="text"
                          value={editFormData.trainer_name || ''}
                          onChange={(e) => setEditFormData(prev => ({ ...prev, trainer_name: e.target.value }))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                          placeholder="Trainer's full name"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Trainer Contact
                        </label>
                        <input
                          type="text"
                          value={editFormData.trainer_contact || ''}
                          onChange={(e) => setEditFormData(prev => ({ ...prev, trainer_contact: e.target.value }))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                          placeholder="Phone number or email"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Training Level
                        </label>
                        <select
                          value={editFormData.training_level || ''}
                          onChange={(e) => setEditFormData(prev => ({ ...prev, training_level: e.target.value }))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                        >
                          <option value="">Select training level</option>
                          <option value="Green">Green</option>
                          <option value="Beginner">Beginner</option>
                          <option value="Intermediate">Intermediate</option>
                          <option value="Advanced">Advanced</option>
                          <option value="Competition">Competition</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Disciplines
                        </label>
                        <input
                          type="text"
                          value={editFormData.disciplines || ''}
                          onChange={(e) => setEditFormData(prev => ({ ...prev, disciplines: e.target.value }))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                          placeholder="Dressage, Jumping, Trail, etc."
                        />
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h3 className="text-lg font-medium text-gray-900">Schedule</h3>
                    <div className="space-y-3">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Feeding Schedule
                        </label>
                        <textarea
                          value={editFormData.feeding_schedule || ''}
                          onChange={(e) => setEditFormData(prev => ({ ...prev, feeding_schedule: e.target.value }))}
                          rows={3}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                          placeholder="6 AM: 2 lbs grain, 1 flake hay..."
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Exercise Schedule
                        </label>
                        <textarea
                          value={editFormData.exercise_schedule || ''}
                          onChange={(e) => setEditFormData(prev => ({ ...prev, exercise_schedule: e.target.value }))}
                          rows={3}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                          placeholder="Monday: Dressage training, Tuesday: Trail ride..."
                        />
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Read-only Management Info Display */}
                  <div className="space-y-4">
                    <h3 className="text-lg font-medium text-gray-900">Location & Care</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {horse.current_location && (
                        <div>
                          <dt className="text-sm font-medium text-gray-500">Current Location</dt>
                          <dd className="mt-1 text-sm text-gray-900">{horse.current_location}</dd>
                        </div>
                      )}
                      {horse.stall_number && (
                        <div>
                          <dt className="text-sm font-medium text-gray-500">Stall Number</dt>
                          <dd className="mt-1 text-sm text-gray-900">{horse.stall_number}</dd>
                        </div>
                      )}
                      {horse.pasture_group && (
                        <div>
                          <dt className="text-sm font-medium text-gray-500">Pasture Group</dt>
                          <dd className="mt-1 text-sm text-gray-900">{horse.pasture_group}</dd>
                        </div>
                      )}
                      {horse.boarding_type && (
                        <div>
                          <dt className="text-sm font-medium text-gray-500">Boarding Type</dt>
                          <dd className="mt-1 text-sm text-gray-900">{horse.boarding_type}</dd>
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="space-y-4">
                    <h3 className="text-lg font-medium text-gray-900">Owner & Training</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {horse.owner_name && (
                        <div>
                          <dt className="text-sm font-medium text-gray-500">Owner</dt>
                          <dd className="mt-1 text-sm text-gray-900">{horse.owner_name}</dd>
                          {horse.owner_contact && (
                            <dd className="text-xs text-gray-600">{horse.owner_contact}</dd>
                          )}
                        </div>
                      )}
                      {horse.trainer_name && (
                        <div>
                          <dt className="text-sm font-medium text-gray-500">Trainer</dt>
                          <dd className="mt-1 text-sm text-gray-900">{horse.trainer_name}</dd>
                          {horse.trainer_contact && (
                            <dd className="text-xs text-gray-600">{horse.trainer_contact}</dd>
                          )}
                        </div>
                      )}
                      {horse.training_level && (
                        <div>
                          <dt className="text-sm font-medium text-gray-500">Training Level</dt>
                          <dd className="mt-1 text-sm text-gray-900">{horse.training_level}</dd>
                        </div>
                      )}
                      {horse.disciplines && (
                        <div>
                          <dt className="text-sm font-medium text-gray-500">Disciplines</dt>
                          <dd className="mt-1 text-sm text-gray-900">{horse.disciplines}</dd>
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="space-y-4">
                    <h3 className="text-lg font-medium text-gray-900">Schedule</h3>
                    <div className="space-y-3">
                      {horse.feeding_schedule && (
                        <div>
                          <dt className="text-sm font-medium text-gray-500">Feeding Schedule</dt>
                          <dd className="mt-1 text-sm text-gray-900">{horse.feeding_schedule}</dd>
                        </div>
                      )}
                      {horse.exercise_schedule && (
                        <div>
                          <dt className="text-sm font-medium text-gray-500">Exercise Schedule</dt>
                          <dd className="mt-1 text-sm text-gray-900">{horse.exercise_schedule}</dd>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'health' && (
            <div className="space-y-6">
              {isEditing ? (
                <div className="space-y-6">
                  {/* Editable Health Info Form */}
                  <div className="space-y-4">
                    <h3 className="text-lg font-medium text-gray-900">Current Health</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Allergies
                        </label>
                        <textarea
                          value={editFormData.allergies || ''}
                          onChange={(e) => setEditFormData(prev => ({ ...prev, allergies: e.target.value }))}
                          rows={3}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                          placeholder="List any known allergies..."
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Current Medications
                        </label>
                        <textarea
                          value={editFormData.medications || ''}
                          onChange={(e) => setEditFormData(prev => ({ ...prev, medications: e.target.value }))}
                          rows={3}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                          placeholder="List current medications and doses..."
                        />
                      </div>
                      <div className="col-span-2">
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Special Needs
                        </label>
                        <textarea
                          value={editFormData.special_needs || ''}
                          onChange={(e) => setEditFormData(prev => ({ ...prev, special_needs: e.target.value }))}
                          rows={3}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                          placeholder="Any special care instructions or needs..."
                        />
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h3 className="text-lg font-medium text-gray-900">Veterinary Team</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Veterinarian Name
                        </label>
                        <input
                          type="text"
                          value={editFormData.veterinarian_name || ''}
                          onChange={(e) => setEditFormData(prev => ({ ...prev, veterinarian_name: e.target.value }))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                          placeholder="Dr. Smith"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Veterinarian Contact
                        </label>
                        <input
                          type="text"
                          value={editFormData.veterinarian_contact || ''}
                          onChange={(e) => setEditFormData(prev => ({ ...prev, veterinarian_contact: e.target.value }))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                          placeholder="Phone number or email"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Farrier Name
                        </label>
                        <input
                          type="text"
                          value={editFormData.farrier_name || ''}
                          onChange={(e) => setEditFormData(prev => ({ ...prev, farrier_name: e.target.value }))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                          placeholder="Farrier's name"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Emergency Contact Name
                        </label>
                        <input
                          type="text"
                          value={editFormData.emergency_contact_name || ''}
                          onChange={(e) => setEditFormData(prev => ({ ...prev, emergency_contact_name: e.target.value }))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                          placeholder="Emergency contact name"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Emergency Contact Phone
                        </label>
                        <input
                          type="tel"
                          value={editFormData.emergency_contact_phone || ''}
                          onChange={(e) => setEditFormData(prev => ({ ...prev, emergency_contact_phone: e.target.value }))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                          placeholder="(555) 123-4567"
                        />
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h3 className="text-lg font-medium text-gray-900">Recent Care</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Last Vet Visit
                        </label>
                        <input
                          type="date"
                          value={editFormData.last_vet_visit ? new Date(editFormData.last_vet_visit).toISOString().split('T')[0] : ''}
                          onChange={(e) => setEditFormData(prev => ({ ...prev, last_vet_visit: e.target.value ? new Date(e.target.value).toISOString() : undefined }))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Last Dental
                        </label>
                        <input
                          type="date"
                          value={editFormData.last_dental ? new Date(editFormData.last_dental).toISOString().split('T')[0] : ''}
                          onChange={(e) => setEditFormData(prev => ({ ...prev, last_dental: e.target.value ? new Date(e.target.value).toISOString() : undefined }))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Last Farrier
                        </label>
                        <input
                          type="date"
                          value={editFormData.last_farrier ? new Date(editFormData.last_farrier).toISOString().split('T')[0] : ''}
                          onChange={(e) => setEditFormData(prev => ({ ...prev, last_farrier: e.target.value ? new Date(e.target.value).toISOString() : undefined }))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Read-only Health Info Display */}
                  <div className="space-y-4">
                    <h3 className="text-lg font-medium text-gray-900">Current Health</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {horse.allergies && (
                        <div>
                          <dt className="text-sm font-medium text-gray-500">Allergies</dt>
                          <dd className="mt-1 text-sm text-gray-900">{horse.allergies}</dd>
                        </div>
                      )}
                      {horse.medications && (
                        <div>
                          <dt className="text-sm font-medium text-gray-500">Current Medications</dt>
                          <dd className="mt-1 text-sm text-gray-900">{horse.medications}</dd>
                        </div>
                      )}
                      {horse.special_needs && (
                        <div className="col-span-2">
                          <dt className="text-sm font-medium text-gray-500">Special Needs</dt>
                          <dd className="mt-1 text-sm text-gray-900">{horse.special_needs}</dd>
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="space-y-4">
                    <h3 className="text-lg font-medium text-gray-900">Veterinary Team</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {horse.veterinarian_name && (
                        <div>
                          <dt className="text-sm font-medium text-gray-500">Veterinarian</dt>
                          <dd className="mt-1 text-sm text-gray-900">{horse.veterinarian_name}</dd>
                          {horse.veterinarian_contact && (
                            <dd className="text-xs text-gray-600">{horse.veterinarian_contact}</dd>
                          )}
                        </div>
                      )}
                      {horse.farrier_name && (
                        <div>
                          <dt className="text-sm font-medium text-gray-500">Farrier</dt>
                          <dd className="mt-1 text-sm text-gray-900">{horse.farrier_name}</dd>
                        </div>
                      )}
                      {horse.emergency_contact_name && (
                        <div>
                          <dt className="text-sm font-medium text-gray-500">Emergency Contact</dt>
                          <dd className="mt-1 text-sm text-gray-900">{horse.emergency_contact_name}</dd>
                          {horse.emergency_contact_phone && (
                            <dd className="text-xs text-gray-600">{horse.emergency_contact_phone}</dd>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="space-y-4">
                    <h3 className="text-lg font-medium text-gray-900">Recent Care</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {horse.last_vet_visit && (
                        <div>
                          <dt className="text-sm font-medium text-gray-500">Last Vet Visit</dt>
                          <dd className="mt-1 text-sm text-gray-900">{new Date(horse.last_vet_visit).toLocaleDateString()}</dd>
                        </div>
                      )}
                      {horse.last_dental && (
                        <div>
                          <dt className="text-sm font-medium text-gray-500">Last Dental</dt>
                          <dd className="mt-1 text-sm text-gray-900">{new Date(horse.last_dental).toLocaleDateString()}</dd>
                        </div>
                      )}
                      {horse.last_farrier && (
                        <div>
                          <dt className="text-sm font-medium text-gray-500">Last Farrier</dt>
                          <dd className="mt-1 text-sm text-gray-900">{new Date(horse.last_farrier).toLocaleDateString()}</dd>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'notes' && (
            <div className="space-y-6">
              {isEditing ? (
                <div className="space-y-6">
                  {/* Editable Notes Form */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      General Notes
                    </label>
                    <textarea
                      value={editFormData.notes || ''}
                      onChange={(e) => setEditFormData(prev => ({ ...prev, notes: e.target.value }))}
                      rows={5}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      placeholder="General notes about the horse..."
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Special Instructions
                    </label>
                    <textarea
                      value={editFormData.special_instructions || ''}
                      onChange={(e) => setEditFormData(prev => ({ ...prev, special_instructions: e.target.value }))}
                      rows={4}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      placeholder="Any special instructions for handlers..."
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Feeding Notes
                    </label>
                    <textarea
                      value={editFormData.feeding_notes || ''}
                      onChange={(e) => setEditFormData(prev => ({ ...prev, feeding_notes: e.target.value }))}
                      rows={4}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      placeholder="Feeding preferences, restrictions, observations..."
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Training Notes
                    </label>
                    <textarea
                      value={editFormData.training_notes || ''}
                      onChange={(e) => setEditFormData(prev => ({ ...prev, training_notes: e.target.value }))}
                      rows={4}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      placeholder="Training progress, behavioral notes, goals..."
                    />
                  </div>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Read-only Notes Display */}
                  {horse.notes && (
                    <div>
                      <dt className="text-sm font-medium text-gray-500 mb-2">General Notes</dt>
                      <dd className="text-sm text-gray-900 whitespace-pre-wrap">{horse.notes}</dd>
                    </div>
                  )}
                  {horse.special_instructions && (
                    <div>
                      <dt className="text-sm font-medium text-gray-500 mb-2">Special Instructions</dt>
                      <dd className="text-sm text-gray-900 whitespace-pre-wrap">{horse.special_instructions}</dd>
                    </div>
                  )}
                  {horse.feeding_notes && (
                    <div>
                      <dt className="text-sm font-medium text-gray-500 mb-2">Feeding Notes</dt>
                      <dd className="text-sm text-gray-900 whitespace-pre-wrap">{horse.feeding_notes}</dd>
                    </div>
                  )}
                  {horse.training_notes && (
                    <div>
                      <dt className="text-sm font-medium text-gray-500 mb-2">Training Notes</dt>
                      <dd className="text-sm text-gray-900 whitespace-pre-wrap">{horse.training_notes}</dd>
                    </div>
                  )}
                  {!horse.notes && !horse.special_instructions && !horse.feeding_notes && !horse.training_notes && (
                    <div className="text-center py-8">
                      <p className="text-gray-500">No notes available</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {activeTab === 'documents' && (
            <div className="space-y-6">
              {/* Enhanced Upload Section */}
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <div className="mb-4">
                  <h3 className="text-lg font-medium text-gray-900 mb-2">📚 Upload Documents & Photos</h3>
                  <p className="text-sm text-gray-500">
                    💡 Upload veterinary reports, training notes, photos of injuries, or any documents related to {horse?.name}.
                    Photos and documents will be analyzed by AI to help with health tracking and management.
                  </p>
                </div>

                {/* Upload Method Selection */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                  {/* File Upload */}
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 hover:border-primary-400 transition-colors">
                    <div className="text-center">
                      <svg className="mx-auto h-8 w-8 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                        <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                      <div className="mt-2">
                        <label htmlFor="file-upload" className="cursor-pointer">
                          <span className="text-sm font-medium text-gray-900">
                            📁 {stagedFile ? stagedFile.name : 'Browse Files'}
                          </span>
                          <input
                            id="file-upload"
                            name="file-upload"
                            type="file"
                            className="sr-only"
                            onChange={handleFileSelection}
                            disabled={savingDocument}
                            accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.tiff,.gif,.mp4,.mov"
                          />
                        </label>
                        <p className="text-xs text-gray-500 mt-1">
                          PDF, DOC, TXT, Images, Videos
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Camera Capture */}
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 hover:border-primary-400 transition-colors">
                    <div className="text-center">
                      <svg className="mx-auto h-8 w-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                      <div className="mt-2">
                        <button
                          onClick={startCamera}
                          disabled={takingPhoto || savingDocument}
                          className="text-sm font-medium text-gray-900 hover:text-primary-600 disabled:opacity-50"
                        >
                          📸 {takingPhoto ? 'Opening Camera...' : 'Take Photo'}
                        </button>
                        <p className="text-xs text-gray-500 mt-1">
                          Capture injuries, conditions, etc.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Metadata Form */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Category (Optional)
                    </label>
                    <select
                      value={documentCategory}
                      onChange={(e) => setDocumentCategory(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    >
                      <option value="">Select Category</option>
                      {Object.entries(documentCategories).map(([key, label]) => (
                        <option key={key} value={key}>{label}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Title (Optional)
                    </label>
                    <input
                      type="text"
                      value={documentTitle}
                      onChange={(e) => setDocumentTitle(e.target.value)}
                      placeholder="e.g., Annual Vaccination Record 2024"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description (Optional)
                  </label>
                  <textarea
                    value={documentDescription}
                    onChange={(e) => setDocumentDescription(e.target.value)}
                    placeholder="Brief description of the document content..."
                    rows={2}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>

                {/* Action Buttons */}
                {stagedFile && (
                  <div className="flex space-x-3 pt-4 border-t border-gray-200">
                    <button
                      onClick={saveDocument}
                      disabled={savingDocument}
                      className="flex-1 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
                    >
                      {savingDocument ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                          <span>Saving...</span>
                        </>
                      ) : (
                        <>
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
                          </svg>
                          <span>Save Document</span>
                        </>
                      )}
                    </button>
                    <button
                      onClick={clearDocumentForm}
                      disabled={savingDocument}
                      className="flex-1 bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
                    >
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                      <span>Clear</span>
                    </button>
                  </div>
                )}
              </div>

              {/* Camera Modal */}
              {showCamera && (
                <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
                  <div className="bg-white rounded-lg p-6 max-w-lg w-full mx-4">
                    <div className="flex justify-between items-center mb-4">
                      <h3 className="text-lg font-medium">📸 Capture Photo</h3>
                      <button
                        onClick={stopCamera}
                        className="text-gray-400 hover:text-gray-600"
                      >
                        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                    <div className="text-center">
                      <video
                        id="camera-video"
                        autoPlay
                        playsInline
                        ref={(video) => {
                          if (video && cameraStream) {
                            video.srcObject = cameraStream
                          }
                        }}
                        className="w-full rounded-lg mb-4"
                      />
                      <div className="flex justify-center space-x-4">
                        <button
                          onClick={stopCamera}
                          className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                        >
                          Cancel
                        </button>
                        <button
                          onClick={capturePhoto}
                          disabled={uploadingDocument}
                          className="px-4 py-2 bg-primary-600 text-white rounded-md text-sm font-medium hover:bg-primary-700 disabled:opacity-50 flex items-center space-x-2"
                        >
                          {uploadingDocument ? (
                            <>
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                              <span>Uploading...</span>
                            </>
                          ) : (
                            <>
                              <span>📸</span>
                              <span>Capture</span>
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Documents List */}
              {documentsLoading ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
                  <p className="mt-2 text-gray-600">Loading documents...</p>
                </div>
              ) : documents.length === 0 ? (
                <div className="text-center py-8">
                  <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No documents</h3>
                  <p className="mt-1 text-sm text-gray-500">Upload your first document or take a photo to get started.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  <h3 className="text-lg font-medium text-gray-900">📋 Documents & Photos</h3>
                  {documents.map((doc) => (
                    <div key={doc.id} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                      <div className="flex items-start justify-between">
                        <div className="flex items-start space-x-3 flex-1 min-w-0">
                          <span className="text-2xl mt-1">
                            {doc.document_category ? getCategoryIcon(doc.document_category) : getFileIcon(doc.file_type)}
                          </span>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center space-x-2 mb-1">
                              <p className="text-sm font-medium text-gray-900 truncate">
                                {doc.title || doc.filename}
                              </p>
                              {doc.document_category && (
                                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                  {documentCategories[doc.document_category as keyof typeof documentCategories]?.replace(/^[^\s]+ /, '') || doc.document_category}
                                </span>
                              )}
                            </div>
                            <div className="flex items-center space-x-2 text-xs text-gray-500 mb-1">
                              <span>{formatFileSize(doc.file_size)}</span>
                              <span>•</span>
                              <span>{new Date(doc.upload_date).toLocaleDateString()}</span>
                            </div>
                            {doc.description && (
                              <p className="text-xs text-gray-600 mt-1">
                                {doc.description}
                              </p>
                            )}
                            {doc.title && doc.title !== doc.filename && (
                              <p className="text-xs text-gray-500 mt-1">
                                File: {doc.filename}
                              </p>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center space-x-2 ml-4">
                          <button
                            onClick={() => {
                              const downloadUrl = buildApiUrl(`/api/v1/horses/${horse!.id}/documents/${doc.id}/download?organization_id=${selectedBarnId}`)
                              const accessToken = localStorage.getItem('access_token')
                              const headers: Record<string, string> = accessToken && accessToken !== 'dev_token_placeholder' ? { 'Authorization': `Bearer ${accessToken}` } : {}

                              fetch(downloadUrl, { headers })
                                .then(response => response.blob())
                                .then(blob => {
                                  const url = URL.createObjectURL(blob)
                                  const a = document.createElement('a')
                                  a.href = url
                                  a.download = doc.filename
                                  a.click()
                                  URL.revokeObjectURL(url)
                                })
                                .catch(console.error)
                            }}
                            className="p-2 text-gray-400 hover:text-gray-600 rounded-md hover:bg-gray-200"
                            title="Download"
                          >
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                          </button>
                          <button
                            onClick={() => {
                              if (confirm('Are you sure you want to delete this document?')) {
                                deleteDocument(doc.id)
                              }
                            }}
                            className="p-2 text-red-400 hover:text-red-600 rounded-md hover:bg-red-50"
                            title="Delete"
                          >
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}