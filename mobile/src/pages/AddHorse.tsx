import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { horseApi, apiClient, buildApiUrl } from '../services/api'

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

interface AddHorseProps {
  user: User
  selectedBarnId: string | null
}

interface HorseData {
  name: string
  breed?: string
  color?: string
  gender?: 'mare' | 'stallion' | 'gelding'
  age_years?: number
  height_hands?: string
  weight_lbs?: number
  registration_number?: string
  registration_organization?: string
  microchip_number?: string
  current_location?: string
  stall_number?: string
  owner_name?: string
  owner_contact?: string
  trainer_name?: string
  trainer_contact?: string
  notes?: string
}

export default function AddHorse({ user, selectedBarnId }: AddHorseProps) {
  const navigate = useNavigate()
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [profilePhoto, setProfilePhoto] = useState<File | null>(null)
  const [profilePhotoPreview, setProfilePhotoPreview] = useState<string | null>(null)
  const [uploadingPhoto, setUploadingPhoto] = useState(false)
  const [formData, setFormData] = useState<HorseData>({
    name: '',
    breed: '',
    color: '',
    gender: undefined,
    age_years: undefined,
    height_hands: '',
    weight_lbs: undefined,
    registration_number: '',
    registration_organization: '',
    microchip_number: '',
    current_location: '',
    stall_number: '',
    owner_name: '',
    owner_contact: '',
    trainer_name: '',
    trainer_contact: '',
    notes: ''
  })

  const handleInputChange = (field: keyof HorseData, value: string | number | undefined) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handlePhotoSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    // Validate file type
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file')
      return
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      alert('Please select a file smaller than 10MB')
      return
    }

    setProfilePhoto(file)

    // Create preview URL
    const reader = new FileReader()
    reader.onload = (e) => {
      setProfilePhotoPreview(e.target?.result as string)
    }
    reader.readAsDataURL(file)
  }

  const removePhoto = () => {
    setProfilePhoto(null)
    setProfilePhotoPreview(null)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!formData.name.trim()) {
      setError('Horse name is required')
      return
    }

    if (!selectedBarnId) {
      setError('No barn selected')
      return
    }

    setSaving(true)
    setError(null)

    try {
      const accessToken = localStorage.getItem('access_token')
      if (!accessToken) {
        throw new Error('Not authenticated')
      }

      apiClient.setToken(accessToken)

      // Clean up form data - remove empty strings and undefined values
      const cleanedData = Object.entries(formData).reduce((acc, [key, value]) => {
        if (value !== '' && value !== undefined && value !== null) {
          acc[key] = value
        }
        return acc
      }, {} as any)

      const response = await horseApi.create(cleanedData, selectedBarnId)

      if (response.success) {
        const newHorse = response.data as any
        const horseId = newHorse.id

        // Upload photo if one was selected
        if (profilePhoto) {
          setUploadingPhoto(true)
          try {
            const formData = new FormData()
            formData.append('photo', profilePhoto)

            const photoUrl = buildApiUrl(`/api/v1/horses/${horseId}/photo?organization_id=${selectedBarnId}`)
            const headers: Record<string, string> = accessToken && accessToken !== 'dev_token_placeholder'
              ? { 'Authorization': `Bearer ${accessToken}` }
              : {}

            const photoResponse = await fetch(photoUrl, {
              method: 'POST',
              headers,
              body: formData
            })

            if (!photoResponse.ok) {
              console.error('Failed to upload photo, but horse was created successfully')
            }
          } catch (photoError) {
            console.error('Failed to upload photo:', photoError)
          }
          setUploadingPhoto(false)
        }

        // Navigate to the new horse's profile
        navigate(`/horses/${horseId}`)
      } else {
        throw new Error(response.error || 'Failed to create horse')
      }
    } catch (error) {
      console.error('Error creating horse:', error)
      setError(error instanceof Error ? error.message : 'Failed to create horse')
    }

    setSaving(false)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
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
        <h1 className="text-2xl font-bold text-gray-900">Add New Horse</h1>
      </div>

      {/* Form */}
      <div className="bg-white rounded-lg border border-gray-200 p-6 lg:p-8">
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-red-800">{error}</p>
              </div>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Information */}
          <div>
            <h3 className="text-lg md:text-xl font-medium text-gray-900 mb-4">Basic Information</h3>

            {/* Profile Photo Upload */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">Profile Photo</label>
              <div className="flex items-center space-x-4">
                {profilePhotoPreview ? (
                  <div className="relative">
                    <img
                      src={profilePhotoPreview}
                      alt="Horse profile preview"
                      className="w-20 h-20 md:w-24 md:h-24 rounded-full object-cover border border-gray-300"
                    />
                    <button
                      type="button"
                      onClick={removePhoto}
                      className="absolute -top-2 -right-2 bg-red-500 hover:bg-red-600 text-white rounded-full p-1 text-xs"
                    >
                      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                ) : (
                  <div className="w-20 h-20 md:w-24 md:h-24 bg-gray-100 rounded-full flex items-center justify-center border border-gray-300">
                    <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                  </div>
                )}
                <div>
                  <label htmlFor="photo-upload" className="cursor-pointer">
                    <div className="bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 px-4 py-2 rounded-md text-sm font-medium transition-colors">
                      {profilePhoto ? 'Change Photo' : 'Upload Photo'}
                    </div>
                    <input
                      id="photo-upload"
                      name="photo-upload"
                      type="file"
                      className="sr-only"
                      onChange={handlePhotoSelect}
                      accept="image/*"
                    />
                  </label>
                  <p className="text-xs text-gray-500 mt-1">JPG, PNG, GIF up to 10MB</p>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Breed</label>
                <input
                  type="text"
                  value={formData.breed}
                  onChange={(e) => handleInputChange('breed', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Color</label>
                <input
                  type="text"
                  value={formData.color}
                  onChange={(e) => handleInputChange('color', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Gender</label>
                <select
                  value={formData.gender || ''}
                  onChange={(e) => handleInputChange('gender', e.target.value || undefined)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                >
                  <option value="">Select Gender</option>
                  <option value="Mare">Mare</option>
                  <option value="Stallion">Stallion</option>
                  <option value="Gelding">Gelding</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Age (years)</label>
                <input
                  type="number"
                  min="0"
                  max="50"
                  value={formData.age_years || ''}
                  onChange={(e) => handleInputChange('age_years', e.target.value ? parseInt(e.target.value) : undefined)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Height (hands)</label>
                <input
                  type="text"
                  placeholder="e.g., 15.2"
                  value={formData.height_hands}
                  onChange={(e) => handleInputChange('height_hands', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Weight (lbs)</label>
                <input
                  type="number"
                  min="0"
                  max="3000"
                  value={formData.weight_lbs || ''}
                  onChange={(e) => handleInputChange('weight_lbs', e.target.value ? parseInt(e.target.value) : undefined)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
            </div>
          </div>

          {/* Registration */}
          <div>
            <h3 className="text-lg md:text-xl font-medium text-gray-900 mb-4">Registration & Identification</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Registration Number</label>
                <input
                  type="text"
                  value={formData.registration_number}
                  onChange={(e) => handleInputChange('registration_number', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Registry</label>
                <input
                  type="text"
                  placeholder="e.g., AQHA, APHA, etc."
                  value={formData.registration_organization}
                  onChange={(e) => handleInputChange('registration_organization', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
              <div className="md:col-span-1">
                <label className="block text-sm font-medium text-gray-700 mb-1">Microchip Number</label>
                <input
                  type="text"
                  value={formData.microchip_number}
                  onChange={(e) => handleInputChange('microchip_number', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
            </div>
          </div>

          {/* Location & Management */}
          <div>
            <h3 className="text-lg md:text-xl font-medium text-gray-900 mb-4">Location & Management</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Current Location</label>
                <input
                  type="text"
                  placeholder="e.g., Main Barn, Pasture A"
                  value={formData.current_location}
                  onChange={(e) => handleInputChange('current_location', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Stall Number</label>
                <input
                  type="text"
                  placeholder="e.g., A-12"
                  value={formData.stall_number}
                  onChange={(e) => handleInputChange('stall_number', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
            </div>
          </div>

          {/* Owner & Trainer */}
          <div>
            <h3 className="text-lg md:text-xl font-medium text-gray-900 mb-4">Owner & Trainer</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Owner Name</label>
                <input
                  type="text"
                  value={formData.owner_name}
                  onChange={(e) => handleInputChange('owner_name', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Owner Contact</label>
                <input
                  type="text"
                  placeholder="Phone or email"
                  value={formData.owner_contact}
                  onChange={(e) => handleInputChange('owner_contact', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Trainer Name</label>
                <input
                  type="text"
                  value={formData.trainer_name}
                  onChange={(e) => handleInputChange('trainer_name', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Trainer Contact</label>
                <input
                  type="text"
                  placeholder="Phone or email"
                  value={formData.trainer_contact}
                  onChange={(e) => handleInputChange('trainer_contact', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
            </div>
          </div>

          {/* Notes */}
          <div>
            <h3 className="text-lg md:text-xl font-medium text-gray-900 mb-4">Notes</h3>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">General Notes</label>
              <textarea
                rows={4}
                value={formData.notes}
                onChange={(e) => handleInputChange('notes', e.target.value)}
                placeholder="Any additional information about this horse..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
          </div>

          {/* Form Actions */}
          <div className="flex items-center justify-end space-x-3 pt-6 border-t border-gray-200">
            <Link
              to="/horses"
              className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled={saving || uploadingPhoto}
              className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              {saving ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Creating Horse...</span>
                </>
              ) : uploadingPhoto ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Uploading Photo...</span>
                </>
              ) : (
                <>
                  <span>🐴</span>
                  <span>Create Horse</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}