import { useState, useEffect, useRef } from 'react'
import { suppliesApi, apiClient } from '../services/api'

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

interface Supply {
  id: number
  uuid: string
  name: string
  description?: string
  category: string
  brand?: string
  unit_type: string
  package_size?: number
  package_unit?: string
  current_stock: number
  min_stock_level?: number
  reorder_point?: number
  last_cost_per_unit?: number
  storage_location?: string
  is_low_stock: boolean
  is_out_of_stock: boolean
  updated_at?: string
}

interface DashboardData {
  total_supplies: number
  low_stock_count: number
  out_of_stock_count: number
  total_inventory_value: number
  monthly_spending: number
  top_categories: Array<{ category: string; amount: number }>
  recent_transactions: Array<any>
  low_stock_items: Supply[]
}

interface SuppliesProps {
  user: User
  selectedBarnId: string | null
}

export default function Supplies({ user, selectedBarnId }: SuppliesProps) {
  const [activeTab, setActiveTab] = useState('dashboard')
  const [supplies, setSupplies] = useState<Supply[]>([])
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('')
  const [stockFilter, setStockFilter] = useState('all')
  const [showAddSupply, setShowAddSupply] = useState(false)
  const [showReceiptScanner, setShowReceiptScanner] = useState(false)

  // Receipt scanner state
  const [selectedImage, setSelectedImage] = useState<string | null>(null)
  const [processingReceipt, setProcessingReceipt] = useState(false)
  const [receiptResults, setReceiptResults] = useState<any>(null)
  const [addingToInventory, setAddingToInventory] = useState<{ [key: number]: boolean }>({})
  const fileInputRef = useRef<HTMLInputElement>(null)
  const cameraInputRef = useRef<HTMLInputElement>(null)

  // Check if device has camera capability
  const isMobileDevice = () => {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
  }

  // Add/Edit Supply Modal State
  const [showAddSupplyModal, setShowAddSupplyModal] = useState(false)
  const [editingSupply, setEditingSupply] = useState<Supply | null>(null)
  const [newSupply, setNewSupply] = useState({
    name: '',
    description: '',
    category: '',
    brand: '',
    unit_type: '',
    current_stock: '' as any,
    min_stock_level: '' as any,
    reorder_point: '' as any,
    last_cost_per_unit: '' as any,
    storage_location: ''
  })

  const categories = [
    { value: 'feed_nutrition', label: 'Feed & Nutrition' },
    { value: 'bedding', label: 'Bedding' },
    { value: 'health_medical', label: 'Health & Medical' },
    { value: 'tack_equipment', label: 'Tack & Equipment' },
    { value: 'facility_maintenance', label: 'Facility & Maintenance' },
    { value: 'grooming', label: 'Grooming' },
    { value: 'other', label: 'Other' }
  ]

  useEffect(() => {
    if (selectedBarnId) {
      if (activeTab === 'dashboard') {
        loadDashboardData()
      } else if (activeTab === 'inventory') {
        loadSupplies()
      }
    }
  }, [selectedBarnId, activeTab])

  const loadDashboardData = async () => {
    if (!selectedBarnId) return

    setLoading(true)
    try {
      const accessToken = localStorage.getItem('access_token')
      if (!accessToken) return

      apiClient.setToken(accessToken)
      const response = await suppliesApi.getDashboard(selectedBarnId)

      if (response.success) {
        setDashboardData(response.data as DashboardData)
      }
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
    }
    setLoading(false)
  }

  const loadSupplies = async () => {
    if (!selectedBarnId) return

    setLoading(true)
    try {
      const accessToken = localStorage.getItem('access_token')
      if (!accessToken) return

      apiClient.setToken(accessToken)
      const response = await suppliesApi.getAll(selectedBarnId)

      if (response.success) {
        let suppliesData = Array.isArray(response.data) ? response.data : []

        // Apply filters locally for development
        if (selectedCategory) {
          suppliesData = suppliesData.filter((s: any) => s.category === selectedCategory)
        }
        if (stockFilter === 'low') {
          suppliesData = suppliesData.filter((s: any) => s.is_low_stock)
        }
        if (searchTerm) {
          suppliesData = suppliesData.filter((s: any) =>
            s.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            s.description?.toLowerCase().includes(searchTerm.toLowerCase())
          )
        }

        setSupplies(suppliesData)
      }
    } catch (error) {
      console.error('Failed to load supplies:', error)
    }
    setLoading(false)
  }

  const getStockStatusIcon = (supply: Supply) => {
    if (supply.is_out_of_stock) return '🚨'
    if (supply.is_low_stock) return '⚠️'
    return '✅'
  }

  const getStockStatusColor = (supply: Supply) => {
    if (supply.is_out_of_stock) return 'text-red-600'
    if (supply.is_low_stock) return 'text-yellow-600'
    return 'text-green-600'
  }

  const formatCurrency = (amount: number | undefined) => {
    if (!amount) return 'N/A'
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount)
  }

  const formatLastUpdated = (dateString: string | undefined) => {
    if (!dateString) return 'Unknown'

    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  }

  const getCategoryLabel = (category: string) => {
    const cat = categories.find(c => c.value === category)
    return cat ? cat.label : category
  }

  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (e) => {
      setSelectedImage(e.target?.result as string)
    }
    reader.readAsDataURL(file)
  }

  const processReceipt = async () => {
    if (!selectedImage || !selectedBarnId) return

    setProcessingReceipt(true)
    try {
      const accessToken = localStorage.getItem('access_token')
      if (!accessToken) return

      apiClient.setToken(accessToken)

      // Convert base64 to blob
      const response = await fetch(selectedImage)
      const blob = await response.blob()

      const formData = new FormData()
      formData.append('receipt_image', blob, 'receipt.jpg')
      formData.append('organization_id', selectedBarnId)

      const result = await suppliesApi.processReceipt(formData, selectedBarnId)

      if (result.success) {
        setReceiptResults(result.data)
      } else {
        throw new Error('Failed to process receipt')
      }
    } catch (error) {
      console.error('Failed to process receipt:', error)
    }
    setProcessingReceipt(false)
  }

  const clearImage = () => {
    setSelectedImage(null)
    setReceiptResults(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
    if (cameraInputRef.current) cameraInputRef.current.value = ''
    setAddingToInventory({})
  }

  const addReceiptItemToInventory = async (item: any, index: number) => {
    if (!selectedBarnId) {
      console.error('No selectedBarnId available')
      alert('Please select a barn first.')
      return
    }

    // Skip non-inventory items like delivery charges, taxes, fees, etc.
    const nonInventoryKeywords = ['delivery', 'shipping', 'tax', 'fee', 'charge', 'discount', 'tip', 'gratuity', 'service']
    const itemName = item.description.toLowerCase()
    const isNonInventoryItem = nonInventoryKeywords.some(keyword => itemName.includes(keyword))

    if (isNonInventoryItem) {
      alert(`"${item.description}" appears to be a service charge rather than an inventory item. Skipping inventory addition.`)
      return
    }

    console.log('Starting addReceiptItemToInventory with:', { item, index, selectedBarnId })
    setAddingToInventory(prev => ({ ...prev, [index]: true }))
    try {
      const accessToken = localStorage.getItem('access_token')
      if (!accessToken) {
        console.error('No access token found')
        alert('Authentication required. Please log in again.')
        return
      }

      console.log('Setting API token and preparing data...')
      apiClient.setToken(accessToken)

      const supplyData = {
        name: item.description,
        description: '',
        category: item.category,
        brand: '',
        unit_type: item.unit || 'each',
        current_stock: parseFloat(item.quantity) || 1,
        min_stock_level: 0,
        reorder_point: 0,
        last_cost_per_unit: parseFloat(item.unit_price) || 0,
        storage_location: ''
      }

      console.log('Adding receipt item to inventory:', supplyData)

      // First check if supply already exists
      console.log('Checking for existing supplies...')
      const existingSuppliesResponse = await suppliesApi.getAll(selectedBarnId)
      console.log('Full API response:', existingSuppliesResponse)

      if (existingSuppliesResponse.success && existingSuppliesResponse.data && Array.isArray(existingSuppliesResponse.data)) {
        console.log('API response data length:', existingSuppliesResponse.data.length)
        console.log('Searching for match:', {
          itemName: item.description,
          itemCategory: item.category,
          existingSupplies: existingSuppliesResponse.data.map((s: any) => ({ name: s.name, category: s.category }))
        })

        const existingSupply = existingSuppliesResponse.data.find((supply: any) => {
          const nameMatch = supply.name.toLowerCase() === item.description.toLowerCase()
          const categoryMatch = supply.category === item.category || supply.category.toLowerCase() === item.category.toLowerCase()
          console.log('Checking supply:', { name: supply.name, category: supply.category, nameMatch, categoryMatch })
          return nameMatch && categoryMatch
        })

        if (existingSupply) {
          console.log('Found existing supply, updating stock...', existingSupply)
          // Update existing supply stock
          const quantityToAdd = parseFloat(item.quantity) || 1
          const unitPrice = parseFloat(item.unit_price) || 0
          const newStock = existingSupply.current_stock + quantityToAdd

          console.log('Update calculation:', {
            currentStock: existingSupply.current_stock,
            quantityToAdd,
            newStock,
            unitPrice,
            fallbackPrice: existingSupply.last_cost_per_unit
          })

          const updateData = {
            current_stock: Math.max(0, newStock), // Ensure non-negative
            last_cost_per_unit: unitPrice > 0 ? unitPrice : existingSupply.last_cost_per_unit
          }

          console.log('Sending update data:', updateData)

          const updateResponse = await suppliesApi.update(existingSupply.id, updateData, selectedBarnId)
          console.log('Update supply response:', updateResponse)

          if (updateResponse.success) {
            // Refresh supplies list if we're on inventory tab
            if (activeTab === 'inventory') {
              loadSupplies()
            }
            alert(`Updated ${item.description} stock! Added ${quantityToAdd} units (new total: ${Math.max(0, newStock)})`)
          } else {
            throw new Error(updateResponse.error || 'Failed to update existing item stock')
          }
          return
        }
      } else {
        console.log('API response format issue:', {
          success: existingSuppliesResponse.success,
          hasData: !!existingSuppliesResponse.data,
          dataType: typeof existingSuppliesResponse.data,
          isArray: Array.isArray(existingSuppliesResponse.data),
          fullResponse: existingSuppliesResponse
        })
      }

      // If no existing supply found, create new one
      console.log('No existing supply found, creating new one...')
      const response = await suppliesApi.create(supplyData, selectedBarnId)
      console.log('Add supply response:', response)

      if (response.success) {
        // Refresh supplies list if we're on inventory tab
        if (activeTab === 'inventory') {
          loadSupplies()
        }
        // Mark this item as added (you could remove it from the UI)
        alert(`${item.description} added to inventory successfully!`)
      } else {
        console.error('API error response:', response)
        const errorMessage = Array.isArray(response.error)
          ? response.error.join(', ')
          : response.error || 'Failed to add item to inventory'
        console.error('Formatted error message:', errorMessage)
        throw new Error(errorMessage)
      }
    } catch (error) {
      console.error('Failed to add receipt item to inventory:', error)
      console.error('Error details:', {
        error: error instanceof Error ? error.message : error,
        stack: error instanceof Error ? error.stack : undefined,
        item,
        selectedBarnId
      })
      alert(`Failed to add item to inventory: ${error instanceof Error ? error.message : 'Unknown error'}. Please try again.`)
    }
    setAddingToInventory(prev => ({ ...prev, [index]: false }))
  }

  const adjustStock = async (supplyId: number, action: 'add' | 'remove') => {
    const amount = prompt(`How much would you like to ${action}?`)
    if (!amount || isNaN(parseFloat(amount))) return

    const quantityChange = action === 'add' ? parseFloat(amount) : -parseFloat(amount)
    const reason = prompt('Reason for stock adjustment (optional):') || undefined
    let unitCost: number | undefined

    if (action === 'add') {
      const costInput = prompt('Unit cost (optional):')
      if (costInput && !isNaN(parseFloat(costInput))) {
        unitCost = parseFloat(costInput)
      }
    }

    try {
      const accessToken = localStorage.getItem('access_token')
      if (!accessToken) return

      apiClient.setToken(accessToken)
      const response = await suppliesApi.adjustStock(
        supplyId.toString(),
        quantityChange,
        reason,
        unitCost,
        selectedBarnId || undefined
      )

      if (response.success) {
        alert(`Stock ${action === 'add' ? 'added' : 'removed'} successfully`)
        loadSupplies() // Reload the supplies list
      } else {
        alert(`Failed to ${action} stock: ${response.error}`)
      }
    } catch (error) {
      console.error('Error adjusting stock:', error)
      alert(`Failed to ${action} stock. Please try again.`)
    }
  }

  const deleteSupply = async (supplyId: number) => {
    if (!confirm('Are you sure you want to delete this supply item? This action cannot be undone.')) {
      return
    }

    try {
      const accessToken = localStorage.getItem('access_token')
      if (!accessToken) return

      apiClient.setToken(accessToken)
      const response = await suppliesApi.delete(supplyId.toString(), selectedBarnId || '')

      if (response.success) {
        alert('Supply item deleted successfully')
        loadSupplies() // Reload the supplies list
      } else {
        alert(`Failed to delete supply: ${response.error}`)
      }
    } catch (error) {
      console.error('Error deleting supply:', error)
      alert('Failed to delete supply. Please try again.')
    }
  }

  const saveSupply = async () => {
    if (!selectedBarnId || !newSupply.name.trim()) return

    try {
      const accessToken = localStorage.getItem('access_token')
      if (!accessToken) return

      apiClient.setToken(accessToken)

      const payload = {
        ...newSupply,
        current_stock: newSupply.current_stock === '' as any ? 0 : Number(newSupply.current_stock),
        min_stock_level: newSupply.min_stock_level === '' as any ? 0 : Number(newSupply.min_stock_level),
        reorder_point: newSupply.reorder_point === '' as any ? 0 : Number(newSupply.reorder_point),
        last_cost_per_unit: newSupply.last_cost_per_unit === '' as any ? 0 : Number(newSupply.last_cost_per_unit),
      }

      const response = editingSupply
        ? await suppliesApi.update(editingSupply.id.toString(), payload, selectedBarnId)
        : await suppliesApi.create(payload, selectedBarnId)

      if (response.success) {
        setShowAddSupplyModal(false)
        setEditingSupply(null)
        loadSupplies()
        alert(`Supply ${editingSupply ? 'updated' : 'created'} successfully!`)
      } else {
        throw new Error(`Failed to ${editingSupply ? 'update' : 'create'} supply`)
      }
    } catch (error) {
      console.error('Failed to save supply:', error)
      alert(`Failed to ${editingSupply ? 'update' : 'create'} supply. Please try again.`)
    }
  }

  if (loading && !dashboardData && !supplies.length) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading supplies...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Supplies & Inventory</h1>
        <p className="text-gray-600">Manage your barn supplies and inventory</p>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="border-b border-gray-200 overflow-x-auto">
          <nav className="-mb-px flex space-x-8 px-6 min-w-max">
            {[
              { id: 'dashboard', name: '📊 Dashboard' },
              { id: 'inventory', name: '📋 Inventory' },
              { id: 'scanner', name: '🧾 Receipt Scanner' },
              { id: 'analytics', name: '📈 Analytics' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`${
                  activeTab === tab.id
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-4 px-4 border-b-2 font-medium text-sm flex-shrink-0`}
              >
                {tab.name}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {/* Dashboard Tab */}
          {activeTab === 'dashboard' && (
            <div className="space-y-6">
              {dashboardData ? (
                <>
                  {/* Key Metrics */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-blue-50 rounded-lg p-4 text-center">
                      <div className="text-2xl font-bold text-blue-600">{dashboardData.total_supplies}</div>
                      <div className="text-sm text-blue-800">Total Supplies</div>
                    </div>
                    <div className="bg-yellow-50 rounded-lg p-4 text-center">
                      <div className="text-2xl font-bold text-yellow-600">{dashboardData.low_stock_count}</div>
                      <div className="text-sm text-yellow-800">Low Stock</div>
                    </div>
                    <div className="bg-red-50 rounded-lg p-4 text-center">
                      <div className="text-2xl font-bold text-red-600">{dashboardData.out_of_stock_count}</div>
                      <div className="text-sm text-red-800">Out of Stock</div>
                    </div>
                    <div className="bg-green-50 rounded-lg p-4 text-center">
                      <div className="text-2xl font-bold text-green-600">{formatCurrency(dashboardData.total_inventory_value)}</div>
                      <div className="text-sm text-green-800">Inventory Value</div>
                    </div>
                  </div>

                  {/* Low Stock Alerts */}
                  {dashboardData.low_stock_items && dashboardData.low_stock_items.length > 0 && (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                      <h3 className="text-lg font-medium text-yellow-800 mb-3">⚠️ Low Stock Alerts</h3>
                      <div className="space-y-2">
                        {dashboardData.low_stock_items.slice(0, 5).map((item) => (
                          <div key={item.id} className="flex justify-between items-center">
                            <span className="text-yellow-800">{item.name}</span>
                            <span className="text-yellow-600 text-sm">{item.current_stock} {item.unit_type}</span>
                          </div>
                        ))}
                      </div>
                      {dashboardData.low_stock_items.length > 5 && (
                        <button
                          onClick={() => setActiveTab('inventory')}
                          className="mt-3 text-yellow-700 hover:text-yellow-800 text-sm font-medium"
                        >
                          View all {dashboardData.low_stock_items.length} low stock items →
                        </button>
                      )}
                    </div>
                  )}

                  {/* Quick Actions */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <button
                      onClick={() => {
                        setActiveTab('scanner')
                        setShowReceiptScanner(true)
                      }}
                      className="bg-gradient-to-r from-blue-500 to-purple-600 text-white p-4 rounded-lg hover:from-blue-600 hover:to-purple-700 transition-colors"
                    >
                      <div className="text-2xl mb-2">📱</div>
                      <div className="font-medium">Scan Receipt</div>
                      <div className="text-sm opacity-90">AI-powered receipt processing</div>
                    </button>
                    <button
                      onClick={() => {
                        setEditingSupply(null)
                        setNewSupply({
                          name: '',
                          description: '',
                          category: '',
                          brand: '',
                          unit_type: '',
                          current_stock: '' as any,
                          min_stock_level: '' as any,
                          reorder_point: '' as any,
                          last_cost_per_unit: '' as any,
                          storage_location: ''
                        })
                        setShowAddSupplyModal(true)
                      }}
                      className="bg-green-500 text-white p-4 rounded-lg hover:bg-green-600 transition-colors"
                    >
                      <div className="text-2xl mb-2">➕</div>
                      <div className="font-medium">Add Supply</div>
                      <div className="text-sm opacity-90">Manually add inventory</div>
                    </button>
                    <button
                      onClick={() => setActiveTab('inventory')}
                      className="bg-gray-500 text-white p-4 rounded-lg hover:bg-gray-600 transition-colors"
                    >
                      <div className="text-2xl mb-2">📋</div>
                      <div className="font-medium">View Inventory</div>
                      <div className="text-sm opacity-90">Browse all supplies</div>
                    </button>
                  </div>
                </>
              ) : (
                <div className="text-center py-8">
                  <p className="text-gray-500">Loading dashboard data...</p>
                </div>
              )}
            </div>
          )}

          {/* Inventory Tab */}
          {activeTab === 'inventory' && (
            <div className="space-y-4">
              {/* Search and Filters */}
              <div className="space-y-3">
                <div className="flex space-x-3">
                  <input
                    type="text"
                    placeholder="Search supplies..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                  <button
                    onClick={loadSupplies}
                    className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                  >
                    Search
                  </button>
                </div>
                <div className="flex space-x-3">
                  <select
                    value={selectedCategory}
                    onChange={(e) => setSelectedCategory(e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="">All Categories</option>
                    {categories.map((cat) => (
                      <option key={cat.value} value={cat.value}>{cat.label}</option>
                    ))}
                  </select>
                  <select
                    value={stockFilter}
                    onChange={(e) => setStockFilter(e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="all">All Items</option>
                    <option value="low">Low Stock Only</option>
                    <option value="in_stock">In Stock Only</option>
                  </select>
                </div>
              </div>

              {/* Add Supply Button */}
              <button
                onClick={() => {
                  setEditingSupply(null)
                  setNewSupply({
                    name: '',
                    description: '',
                    category: '',
                    brand: '',
                    unit_type: '',
                    current_stock: '' as any,
                    min_stock_level: '' as any,
                    reorder_point: '' as any,
                    last_cost_per_unit: '' as any,
                    storage_location: ''
                  })
                  setShowAddSupplyModal(true)
                }}
                className="w-full bg-primary-600 text-white py-2 px-4 rounded-lg hover:bg-primary-700"
              >
                + Add New Supply
              </button>

              {/* Supplies List */}
              {supplies.length === 0 ? (
                <div className="text-center py-8">
                  <div className="text-gray-400 mb-4">
                    <svg className="w-12 h-12 mx-auto" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No supplies found</h3>
                  <p className="text-gray-600 mb-4">
                    {searchTerm || selectedCategory || stockFilter !== 'all'
                      ? 'Try adjusting your search or filters'
                      : 'Add your first supply to get started'
                    }
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {supplies.map((supply) => (
                    <div key={supply.id} className="bg-gray-50 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2">
                            <span className="text-lg">{getStockStatusIcon(supply)}</span>
                            <h3 className="text-lg font-medium text-gray-900 truncate">{supply.name}</h3>
                          </div>
                          <div className="mt-1 space-y-1">
                            <div className="flex items-center space-x-4 text-sm text-gray-600">
                              <span>{getCategoryLabel(supply.category)}</span>
                              {supply.brand && <span>• {supply.brand}</span>}
                            </div>
                            <div className="flex items-center space-x-4 text-sm">
                              <span className={`font-medium ${getStockStatusColor(supply)}`}>
                                Stock: {supply.current_stock} {supply.unit_type}
                              </span>
                              {!!supply.reorder_point && (
                                <span className="text-gray-500">
                                  Reorder at: {supply.reorder_point}
                                </span>
                              )}
                            </div>
                            {supply.storage_location && (
                              <div className="text-sm text-gray-500">
                                📍 {supply.storage_location}
                              </div>
                            )}
                            {!!supply.last_cost_per_unit && (
                              <div className="text-sm text-gray-600">
                                Cost: {formatCurrency(supply.last_cost_per_unit)} per {supply.unit_type}
                              </div>
                            )}
                            <div className="text-xs text-gray-500">
                              🕐 Updated {formatLastUpdated(supply.updated_at)}
                            </div>
                          </div>
                        </div>
                        <div className="flex flex-col space-y-2">
                          <button
                            onClick={() => {
                              setEditingSupply(supply)
                              setNewSupply({
                                name: supply.name,
                                description: supply.description || '',
                                category: supply.category,
                                brand: supply.brand || '',
                                unit_type: supply.unit_type,
                                current_stock: supply.current_stock || '' as any,
                                min_stock_level: supply.min_stock_level || '' as any,
                                reorder_point: supply.reorder_point || '' as any,
                                last_cost_per_unit: supply.last_cost_per_unit || '' as any,
                                storage_location: supply.storage_location || ''
                              })
                              setShowAddSupplyModal(true)
                            }}
                            className="text-blue-600 hover:text-blue-800 text-sm"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => deleteSupply(supply.id)}
                            className="text-red-600 hover:text-red-800 text-sm"
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Receipt Scanner Tab */}
          {activeTab === 'scanner' && (
            <div className="space-y-6">
              <div className="text-center">
                <h3 className="text-lg font-medium text-gray-900 mb-2">AI Receipt Scanner</h3>
                <p className="text-gray-600 mb-6">Upload or take a photo of your receipt to automatically add items to inventory</p>
              </div>

              {!selectedImage ? (
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-8">
                  <div className="text-center">
                    <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                      <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                    <div className="mt-4 space-y-4">
                      <div className="flex justify-center space-x-4">
                        <button
                          onClick={() => fileInputRef.current?.click()}
                          className="bg-primary-600 text-white px-6 py-2 rounded-lg hover:bg-primary-700"
                        >
                          📁 Upload Receipt
                        </button>
                        <button
                          onClick={() => cameraInputRef.current?.click()}
                          className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700"
                          title={isMobileDevice() ? "Open camera to take photo" : "Upload from device (camera not available on desktop)"}
                        >
                          📷 {isMobileDevice() ? 'Take Photo' : 'Camera/Upload'}
                        </button>
                      </div>
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/*"
                        onChange={handleImageUpload}
                        className="hidden"
                      />
                      <input
                        ref={cameraInputRef}
                        type="file"
                        accept="image/*"
                        capture="environment"
                        onChange={handleImageUpload}
                        className="hidden"
                      />
                      <p className="text-sm text-gray-500">
                        Supports JPG, PNG images. Works with receipts, invoices, and delivery slips.
                      </p>
                      {!isMobileDevice() && (
                        <p className="text-xs text-blue-600 mt-2">
                          💡 Camera button opens file picker on desktop. For best camera experience, use on mobile device.
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="relative">
                    <img
                      src={selectedImage}
                      alt="Receipt"
                      className="max-w-full h-auto rounded-lg border"
                    />
                    <button
                      onClick={clearImage}
                      className="absolute top-2 right-2 bg-red-500 text-white rounded-full w-8 h-8 flex items-center justify-center hover:bg-red-600"
                    >
                      ×
                    </button>
                  </div>

                  {!receiptResults && (
                    <div className="text-center">
                      <button
                        onClick={processReceipt}
                        disabled={processingReceipt}
                        className="bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {processingReceipt ? (
                          <div className="flex items-center space-x-2">
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                            <span>Processing with AI...</span>
                          </div>
                        ) : (
                          <div className="flex items-center space-x-2">
                            <span>🤖</span>
                            <span>Process Receipt</span>
                          </div>
                        )}
                      </button>
                    </div>
                  )}

                  {receiptResults && (
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                      <h4 className="font-medium text-green-800 mb-3">Receipt Processed Successfully!</h4>
                      <div className="space-y-2 text-sm">
                        <p><strong>Vendor:</strong> {receiptResults.vendor_name}</p>
                        <p><strong>Date:</strong> {receiptResults.purchase_date}</p>
                        {receiptResults.total_amount && (
                          <p><strong>Total:</strong> {formatCurrency(receiptResults.total_amount)}</p>
                        )}
                        <p><strong>Items Found:</strong> {receiptResults.line_items?.length || 0}</p>
                      </div>
                      {receiptResults.line_items && receiptResults.line_items.length > 0 && (
                        <div className="mt-4">
                          <h5 className="font-medium text-green-800 mb-2">Items to Add:</h5>
                          <div className="space-y-2">
                            {receiptResults.line_items.map((item: any, index: number) => {
                              // Check if this is a non-inventory item
                              const nonInventoryKeywords = ['delivery', 'shipping', 'tax', 'fee', 'charge', 'discount', 'tip', 'gratuity', 'service']
                              const itemName = item.description.toLowerCase()
                              const isNonInventoryItem = nonInventoryKeywords.some(keyword => itemName.includes(keyword))

                              return (
                                <div key={index} className={`rounded p-3 border ${isNonInventoryItem ? 'bg-gray-100 border-gray-300' : 'bg-white'}`}>
                                  <div className="flex justify-between items-start">
                                    <div className="flex-1">
                                      <div className="flex items-center space-x-2">
                                        <p className="font-medium">{item.description}</p>
                                        {isNonInventoryItem && (
                                          <span className="text-xs bg-gray-500 text-white px-2 py-1 rounded">Service Charge</span>
                                        )}
                                      </div>
                                      <p className="text-sm text-gray-600">
                                        Qty: {item.quantity} • Category: {getCategoryLabel(item.category)}
                                      </p>
                                      {item.unit_price && (
                                        <p className="text-sm text-gray-600">
                                          Price: {formatCurrency(item.unit_price)} each
                                        </p>
                                      )}
                                      {isNonInventoryItem && (
                                        <p className="text-xs text-gray-500 mt-1">
                                          This appears to be a service charge and won't be added to inventory
                                        </p>
                                      )}
                                    </div>
                                    {!isNonInventoryItem && (
                                      <button
                                        onClick={() => addReceiptItemToInventory(item, index)}
                                        disabled={addingToInventory[index]}
                                        className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700 disabled:opacity-50"
                                      >
                                        {addingToInventory[index] ? 'Adding...' : 'Add to Inventory'}
                                      </button>
                                    )}
                                  </div>
                                </div>
                              )
                            })}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Analytics Tab */}
          {activeTab === 'analytics' && (
            <div className="text-center py-8">
              <div className="text-gray-400 mb-4">
                <svg className="w-12 h-12 mx-auto" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Analytics Coming Soon</h3>
              <p className="text-gray-600">
                View spending trends, usage patterns, and inventory analytics
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Add/Edit Supply Modal */}
      {showAddSupplyModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full max-h-[85dvh] overflow-y-auto">
            <div className="p-6 pb-8">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-gray-900">
                  {editingSupply ? 'Edit Supply' : 'Add New Supply'}
                </h3>
                <button
                  onClick={() => {
                    setShowAddSupplyModal(false)
                    setEditingSupply(null)
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Name *
                  </label>
                  <input
                    type="text"
                    value={newSupply.name}
                    onChange={(e) => setNewSupply(prev => ({ ...prev, name: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="Supply name"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Category *
                  </label>
                  <select
                    value={newSupply.category}
                    onChange={(e) => setNewSupply(prev => ({ ...prev, category: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="">Select category</option>
                    {categories.map((cat) => (
                      <option key={cat.value} value={cat.value}>{cat.label}</option>
                    ))}
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Brand
                    </label>
                    <input
                      type="text"
                      value={newSupply.brand}
                      onChange={(e) => setNewSupply(prev => ({ ...prev, brand: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      placeholder="Brand name"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Unit Type *
                    </label>
                    <input
                      type="text"
                      value={newSupply.unit_type}
                      onChange={(e) => setNewSupply(prev => ({ ...prev, unit_type: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      placeholder="bags, lbs, etc."
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Current Stock
                    </label>
                    <input
                      type="number"
                      value={newSupply.current_stock}
                      onChange={(e) => setNewSupply(prev => ({ ...prev, current_stock: e.target.value === '' ? '' as any : parseFloat(e.target.value) }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      min="0"
                      step="1"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Min Stock Level
                    </label>
                    <input
                      type="number"
                      value={newSupply.min_stock_level}
                      onChange={(e) => setNewSupply(prev => ({ ...prev, min_stock_level: e.target.value === '' ? '' as any : parseFloat(e.target.value) }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      min="0"
                      step="0.1"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Reorder Point
                    </label>
                    <input
                      type="number"
                      value={newSupply.reorder_point}
                      onChange={(e) => setNewSupply(prev => ({ ...prev, reorder_point: e.target.value === '' ? '' as any : parseFloat(e.target.value) }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      min="0"
                      step="0.1"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Cost per Unit
                    </label>
                    <input
                      type="number"
                      value={newSupply.last_cost_per_unit}
                      onChange={(e) => setNewSupply(prev => ({ ...prev, last_cost_per_unit: e.target.value === '' ? '' as any : parseFloat(e.target.value) }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      min="0"
                      step="0.01"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Storage Location
                  </label>
                  <input
                    type="text"
                    value={newSupply.storage_location}
                    onChange={(e) => setNewSupply(prev => ({ ...prev, storage_location: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="Feed room, tack room, etc."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    value={newSupply.description}
                    onChange={(e) => setNewSupply(prev => ({ ...prev, description: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    rows={3}
                    placeholder="Additional details about this supply"
                  />
                </div>
              </div>

              <div className="mt-6 flex space-x-3">
                <button
                  onClick={() => {
                    setShowAddSupplyModal(false)
                    setEditingSupply(null)
                  }}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={saveSupply}
                  disabled={!newSupply.name.trim() || !newSupply.category || !newSupply.unit_type}
                  className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {editingSupply ? 'Update' : 'Add'} Supply
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}