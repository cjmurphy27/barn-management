import { useState, useEffect, useRef } from 'react'
import { Link, useParams, useNavigate } from 'react-router-dom'

interface ImageWithAuthProps {
  src: string
  alt: string
  className?: string
  onError?: (src: string) => void
  onLoad?: () => void
}

function ImageWithAuth({ src, alt, className, onError, onLoad }: ImageWithAuthProps) {
  const [imageSrc, setImageSrc] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    const loadImage = async () => {
      try {
        setLoading(true)
        setError(false)

        const accessToken = localStorage.getItem('access_token')
        const headers: Record<string, string> = accessToken === 'dev_token_placeholder'
          ? {}
          : { 'Authorization': `Bearer ${accessToken}` }

        console.log('Loading image with Bearer auth:', { src, hasToken: !!accessToken })

        const response = await fetch(src, {
          headers,
          credentials: 'include'
        })

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }

        const blob = await response.blob()
        const objectUrl = URL.createObjectURL(blob)
        setImageSrc(objectUrl)
        onLoad?.()
      } catch (err) {
        console.error('Failed to load image with Bearer auth:', err)
        setError(true)
        onError?.(src)
      } finally {
        setLoading(false)
      }
    }

    loadImage()

    // Cleanup function to revoke object URL
    return () => {
      if (imageSrc) {
        URL.revokeObjectURL(imageSrc)
      }
    }
  }, [src])

  if (loading) {
    return (
      <div className={`${className} flex items-center justify-center bg-gray-100 min-h-48`}>
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (error || !imageSrc) {
    return (
      <div className={`${className} flex items-center justify-center bg-gray-100 min-h-48 text-gray-500`}>
        <div className="text-center">
          <svg className="w-12 h-12 mx-auto mb-2" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd" />
          </svg>
          <p className="text-sm">Failed to load image</p>
        </div>
      </div>
    )
  }

  return <img src={imageSrc} alt={alt} className={className} />
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

interface Post {
  id: number
  uuid: string
  title: string
  content: string
  category: string
  status: string
  is_pinned: boolean
  tags: string
  author_name: string
  author_email: string
  author_user_id: string
  organization_id: string
  created_at: string
  updated_at: string
  attachment?: {
    id: number
    uuid: string
    filename: string
    original_filename: string
    file_size: number
    mime_type: string
  }
  comment_count?: number
}

interface Comment {
  id: number
  uuid: string
  content: string
  post_id: number
  parent_comment_id?: number
  author_name: string
  author_email: string
  author_user_id: string
  organization_id: string
  created_at: string
  updated_at: string
  replies?: Comment[]
}

interface MessagesProps {
  user: User
  selectedBarnId: string | null
}

const categories = [
  { value: 'general', label: 'General', emoji: '💬' },
  { value: 'announcement', label: 'Announcement', emoji: '📢' },
  { value: 'maintenance', label: 'Maintenance', emoji: '🔧' },
  { value: 'health_alert', label: 'Health Alert', emoji: '🚨' },
  { value: 'training', label: 'Training', emoji: '🏇' },
  { value: 'supplies', label: 'Supplies', emoji: '📦' },
  { value: 'weather', label: 'Weather', emoji: '🌤️' },
  { value: 'emergency', label: 'Emergency', emoji: '🆘' },
  { value: 'other', label: 'Other', emoji: '📝' }
]

export default function Messages({ user, selectedBarnId }: MessagesProps) {
  const { postId } = useParams()
  const navigate = useNavigate()

  // State management
  const [activeTab, setActiveTab] = useState('posts')
  const [posts, setPosts] = useState<Post[]>([])
  const [selectedPost, setSelectedPost] = useState<Post | null>(null)
  const [comments, setComments] = useState<Comment[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('')
  const [showPinnedOnly, setShowPinnedOnly] = useState(false)
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(true)

  // Create post form state
  const [newPost, setNewPost] = useState({
    title: '',
    content: '',
    category: 'general',
    is_pinned: false,
    tags: ''
  })
  const [selectedImage, setSelectedImage] = useState<string | null>(null)
  const [uploadingImage, setUploadingImage] = useState(false)
  const [submittingPost, setSubmittingPost] = useState(false)

  // Comment form state
  const [newComment, setNewComment] = useState('')
  const [submittingComment, setSubmittingComment] = useState(false)
  const [replyingTo, setReplyingTo] = useState<number | null>(null)

  // File upload refs
  const fileInputRef = useRef<HTMLInputElement>(null)
  const cameraInputRef = useRef<HTMLInputElement>(null)

  // Check if device has camera capability
  const isMobileDevice = () => {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
  }

  useEffect(() => {
    if (selectedBarnId) {
      if (postId) {
        // Always load the post when postId changes, but try all barns until we find it
        loadPost(postId)
      } else {
        loadPosts()
      }
    }
  }, [selectedBarnId, postId, selectedCategory, showPinnedOnly, searchTerm])

  const loadPosts = async (pageNum = 1, append = false) => {
    if (!selectedBarnId) return

    setLoading(!append)
    try {
      const accessToken = localStorage.getItem('access_token')
      if (!accessToken) return

      const headers: Record<string, string> = accessToken === 'dev_token_placeholder'
        ? {}
        : { 'Authorization': `Bearer ${accessToken}` }

      const params = new URLSearchParams({
        organization_id: selectedBarnId,
        page: pageNum.toString(),
        page_size: '20'
      })

      if (selectedCategory) params.append('category', selectedCategory)
      if (showPinnedOnly) params.append('pinned_only', 'true')
      if (searchTerm) params.append('search', searchTerm)

      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/api/v1/whiteboard/posts?${params.toString()}`,
        { headers }
      )

      if (response.ok) {
        const data = await response.json()
        if (append) {
          setPosts(prev => [...prev, ...data.posts])
        } else {
          setPosts(data.posts || [])
        }
        setHasMore(data.has_more || false)
        setPage(pageNum)
      }
    } catch (error) {
      console.error('Failed to load posts:', error)
    }
    setLoading(false)
  }

  const loadPost = async (postId: string) => {
    if (!user?.organizations?.length) return

    setLoading(true)
    try {
      const accessToken = localStorage.getItem('access_token')
      if (!accessToken) return

      const headers: Record<string, string> = accessToken === 'dev_token_placeholder'
        ? {}
        : { 'Authorization': `Bearer ${accessToken}` }

      // Try to load the post from each organization until we find it
      for (const org of user.organizations) {
        try {
          const response = await fetch(
            `${import.meta.env.VITE_API_URL}/api/v1/whiteboard/posts/${postId}?organization_id=${org.barn_id}&include_attachments=true`,
            { headers }
          )

          if (response.ok) {
            const data = await response.json()
            console.log('Full API response:', data)

            // Check if data has post property or if data itself is the post
            const post = data.post || data
            const comments = data.comments || []

            // Check if post has attachments in different possible structures
            if (data.attachments && data.attachments.length > 0) {
              post.attachment = data.attachments[0] // Use first attachment
            } else if (post.attachments && post.attachments.length > 0) {
              post.attachment = post.attachments[0] // Use first attachment
            }

            console.log('Processed post with attachment:', {
              postId: post.id,
              hasAttachment: !!post.attachment,
              attachment: post.attachment,
              attachments: data.attachments || post.attachments
            })

            setSelectedPost(post)
            setComments(comments)
            console.log(`Post ${postId} found in barn: ${org.barn_name}`)
            return // Found the post, exit
          }
        } catch (error) {
          // Continue to next organization
          console.log(`Post ${postId} not found in barn: ${org.barn_name}`)
        }
      }

      // If we get here, post wasn't found in any organization
      console.error(`Post ${postId} not found in any accessible barn`)
      setSelectedPost(null)
      setComments([])
    } catch (error) {
      console.error('Failed to load post:', error)
    }
    setLoading(false)
  }

  const loadMorePosts = () => {
    if (!loading && hasMore) {
      loadPosts(page + 1, true)
    }
  }

  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setUploadingImage(true)
    const reader = new FileReader()
    reader.onload = (e) => {
      setSelectedImage(e.target?.result as string)
      setUploadingImage(false)
    }
    reader.readAsDataURL(file)
  }

  const clearImage = () => {
    setSelectedImage(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
    if (cameraInputRef.current) cameraInputRef.current.value = ''
  }

  const createPost = async () => {
    if (!selectedBarnId || !newPost.title.trim() || !newPost.content.trim()) return

    setSubmittingPost(true)
    try {
      const accessToken = localStorage.getItem('access_token')
      if (!accessToken) return

      const headers: Record<string, string> = accessToken === 'dev_token_placeholder'
        ? {}
        : { 'Authorization': `Bearer ${accessToken}` }

      let endpoint = `${import.meta.env.VITE_API_URL}/api/v1/whiteboard/posts`
      let body: FormData | string

      if (selectedImage) {
        // Use multipart form for image upload
        const response = await fetch(selectedImage)
        const blob = await response.blob()

        const formData = new FormData()
        formData.append('title', newPost.title)
        formData.append('content', newPost.content)
        formData.append('category', newPost.category)
        formData.append('is_pinned', newPost.is_pinned.toString())
        formData.append('tags', newPost.tags)
        formData.append('organization_id', selectedBarnId)
        formData.append('image', blob, 'post-image.jpg')

        endpoint += '/with-image'
        body = formData
      } else {
        // JSON for text-only posts
        headers['Content-Type'] = 'application/json'
        body = JSON.stringify({
          ...newPost,
          organization_id: selectedBarnId
        })
      }

      const apiResponse = await fetch(endpoint, {
        method: 'POST',
        headers: selectedImage ? headers : { ...headers, 'Content-Type': 'application/json' },
        body
      })

      if (apiResponse.ok) {
        // Reset form
        setNewPost({
          title: '',
          content: '',
          category: 'general',
          is_pinned: false,
          tags: ''
        })
        setSelectedImage(null)
        setActiveTab('posts')

        // Reload posts
        loadPosts()
        alert('Post created successfully!')
      } else {
        throw new Error('Failed to create post')
      }
    } catch (error) {
      console.error('Failed to create post:', error)
      alert('Failed to create post. Please try again.')
    }
    setSubmittingPost(false)
  }

  const createComment = async () => {
    if (!selectedPost || !newComment.trim()) return

    const barnId = selectedPost.organization_id || selectedBarnId
    if (!barnId) return

    setSubmittingComment(true)
    try {
      const accessToken = localStorage.getItem('access_token')
      if (!accessToken) return

      const headers: Record<string, string> = accessToken === 'dev_token_placeholder'
        ? { 'Content-Type': 'application/json' }
        : {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        }

      const commentData: any = {
        content: newComment,
        post_id: selectedPost.id
      }

      if (replyingTo) {
        commentData.parent_comment_id = replyingTo
      }

      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/api/v1/whiteboard/posts/${selectedPost.id}/comments?organization_id=${barnId}`,
        {
          method: 'POST',
          headers,
          body: JSON.stringify(commentData)
        }
      )

      if (response.ok) {
        setNewComment('')
        setReplyingTo(null)
        // Reload post to get updated comments
        loadPost(selectedPost.id.toString())
      } else {
        const errorText = await response.text()
        console.error('Comment creation failed:', {
          status: response.status,
          statusText: response.statusText,
          errorText
        })
        throw new Error(`Failed to create comment: ${response.status} ${errorText}`)
      }
    } catch (error) {
      console.error('Failed to create comment:', error)
      console.error('Comment submission error details:', {
        error,
        postId: selectedPost.id,
        barnId,
        commentContent: newComment,
        replyingTo
      })
      alert('Failed to create comment. Please try again.')
    }
    setSubmittingComment(false)
  }

  const deletePost = async (post: Post) => {
    if (!selectedBarnId || post.author_user_id !== user.user_id) return
    if (!confirm('Are you sure you want to delete this post?')) return

    try {
      const accessToken = localStorage.getItem('access_token')
      if (!accessToken) return

      const headers: Record<string, string> = accessToken === 'dev_token_placeholder'
        ? {}
        : { 'Authorization': `Bearer ${accessToken}` }

      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/api/v1/whiteboard/posts/${post.id}?organization_id=${selectedBarnId}`,
        {
          method: 'DELETE',
          headers
        }
      )

      if (response.ok) {
        if (selectedPost?.id === post.id) {
          setSelectedPost(null)
          navigate('/messages')
        }
        loadPosts()
        alert('Post deleted successfully!')
      } else {
        throw new Error('Failed to delete post')
      }
    } catch (error) {
      console.error('Failed to delete post:', error)
      alert('Failed to delete post. Please try again.')
    }
  }

  const getCategoryEmoji = (category: string) => {
    const cat = categories.find(c => c.value === category)
    return cat ? cat.emoji : '📝'
  }

  const getCategoryLabel = (category: string) => {
    const cat = categories.find(c => c.value === category)
    return cat ? cat.label : category
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMins / 60)
    const diffDays = Math.floor(diffHours / 24)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString()
  }

  if (loading && !posts.length && !selectedPost) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading messages...</p>
        </div>
      </div>
    )
  }

  // Post detail view
  if (selectedPost) {
    return (
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <button
            onClick={() => {
              setSelectedPost(null)
              navigate('/messages')
            }}
            className="flex items-center text-primary-600 hover:text-primary-700"
          >
            <svg className="w-5 h-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Messages
          </button>
          {selectedPost.author_user_id === user.user_id && (
            <button
              onClick={() => deletePost(selectedPost)}
              className="text-red-600 hover:text-red-700 text-sm"
            >
              Delete
            </button>
          )}
        </div>

        {/* Post Content */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-start space-x-3">
            <div className="text-2xl">{getCategoryEmoji(selectedPost.category)}</div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2 mb-2">
                {selectedPost.is_pinned && (
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                    📌 Pinned
                  </span>
                )}
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  {getCategoryLabel(selectedPost.category)}
                </span>
              </div>
              <h1 className="text-lg font-semibold text-gray-900 mb-2">{selectedPost.title}</h1>
              <p className="text-gray-700 whitespace-pre-wrap mb-3">{selectedPost.content}</p>


              {selectedPost.attachment && (
                <div className="mb-3">
                  <ImageWithAuth
                    src={`${import.meta.env.VITE_API_URL}/api/v1/whiteboard/images/${selectedPost.attachment.id}?organization_id=${selectedPost.organization_id}`}
                    alt={selectedPost.attachment.original_filename}
                    className="max-w-full h-auto rounded-lg border"
                    onError={(src) => {
                      console.error('Image failed to load:', {
                        src: src,
                        uuid: selectedPost.attachment?.uuid,
                        barnId: selectedPost.organization_id
                      })
                    }}
                    onLoad={() => {
                      console.log('Image loaded successfully:', selectedPost.attachment?.uuid)
                    }}
                  />
                </div>
              )}

              {selectedPost.tags && typeof selectedPost.tags === 'string' && selectedPost.tags.trim() && (
                <div className="mb-3">
                  <div className="flex flex-wrap gap-1">
                    {selectedPost.tags.split(',').map((tag, index) => (
                      <span key={index} className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700">
                        #{tag.trim()}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="text-sm text-gray-500">
                By {selectedPost.author_name} • {formatDate(selectedPost.created_at)}
              </div>
            </div>
          </div>
        </div>

        {/* Comments Section */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Comments ({comments.length})
          </h3>

          {/* Comment Form */}
          <div className="mb-4">
            {replyingTo && (
              <div className="flex items-center justify-between bg-blue-50 p-2 rounded-lg mb-2">
                <span className="text-sm text-blue-800">Replying to comment</span>
                <button
                  onClick={() => setReplyingTo(null)}
                  className="text-blue-600 hover:text-blue-800"
                >
                  Cancel
                </button>
              </div>
            )}
            <div className="flex space-x-3">
              <textarea
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                placeholder="Write a comment..."
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                rows={3}
                disabled={submittingComment}
              />
              <button
                onClick={createComment}
                disabled={!newComment.trim() || submittingComment}
                className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submittingComment ? 'Posting...' : 'Post'}
              </button>
            </div>
          </div>

          {/* Comments List */}
          <div className="space-y-4">
            {comments.map((comment) => (
              <div key={comment.id} className="border-l-2 border-gray-200 pl-4">
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-gray-700 whitespace-pre-wrap mb-2">{comment.content}</p>
                  <div className="flex items-center justify-between text-sm text-gray-500">
                    <span>By {comment.author_name} • {formatDate(comment.created_at)}</span>
                    <button
                      onClick={() => setReplyingTo(comment.id)}
                      className="text-primary-600 hover:text-primary-700"
                    >
                      Reply
                    </button>
                  </div>
                </div>

                {/* Nested replies would go here if needed */}
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  // Main posts list view
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Message Board</h1>
        <p className="text-gray-600">Share updates and discuss with your barn community</p>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="border-b border-gray-200 overflow-x-auto">
          <nav className="-mb-px flex space-x-8 px-6 min-w-max">
            {[
              { id: 'posts', name: '💬 Messages' },
              { id: 'create', name: '✏️ Create Post' }
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
          {/* Posts Tab */}
          {activeTab === 'posts' && (
            <div className="space-y-4">
              {/* Search and Filters */}
              <div className="space-y-3">
                <div className="flex space-x-3">
                  <input
                    type="text"
                    placeholder="Search posts..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                  <button
                    onClick={() => loadPosts()}
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
                      <option key={cat.value} value={cat.value}>
                        {cat.emoji} {cat.label}
                      </option>
                    ))}
                  </select>
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={showPinnedOnly}
                      onChange={(e) => setShowPinnedOnly(e.target.checked)}
                      className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                    />
                    <span className="text-sm text-gray-700">Pinned only</span>
                  </label>
                </div>
              </div>

              {/* Posts List */}
              {posts.length === 0 ? (
                <div className="text-center py-8">
                  <div className="text-gray-400 mb-4">
                    <svg className="w-12 h-12 mx-auto" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M18 13V5a2 2 0 00-2-2H4a2 2 0 00-2 2v8a2 2 0 002 2h3l3 3 3-3h3a2 2 0 002-2zM5 7a1 1 0 011-1h8a1 1 0 110 2H6a1 1 0 01-1-1zm1 3a1 1 0 100 2h3a1 1 0 100-2H6z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No messages found</h3>
                  <p className="text-gray-600 mb-4">
                    {searchTerm || selectedCategory || showPinnedOnly
                      ? 'Try adjusting your search or filters'
                      : 'Be the first to start a conversation'
                    }
                  </p>
                  <button
                    onClick={() => setActiveTab('create')}
                    className="btn-primary"
                  >
                    Create First Post
                  </button>
                </div>
              ) : (
                <div className="space-y-3">
                  {posts.map((post) => (
                    <Link
                      key={post.id}
                      to={`/messages/${post.id}`}
                      className="block bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-colors"
                    >
                      <div className="flex items-start space-x-3">
                        <div className="text-2xl">{getCategoryEmoji(post.category)}</div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2 mb-1">
                            {post.is_pinned && (
                              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                                📌 Pinned
                              </span>
                            )}
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                              {getCategoryLabel(post.category)}
                            </span>
                          </div>
                          <h3 className="text-lg font-medium text-gray-900 truncate mb-1">
                            {post.title}
                          </h3>
                          <p className="text-gray-600 text-sm line-clamp-2 mb-2">
                            {post.content}
                          </p>
                          {post.attachment && (
                            <div className="mb-2">
                              <span className="inline-flex items-center text-xs text-gray-500">
                                📎 Image attached
                              </span>
                            </div>
                          )}
                          <div className="flex items-center justify-between text-sm text-gray-500">
                            <span>By {post.author_name} • {formatDate(post.created_at)}</span>
                            <span>{post.comment_count || 0} comments</span>
                          </div>
                        </div>
                      </div>
                    </Link>
                  ))}

                  {/* Load More Button */}
                  {hasMore && (
                    <div className="text-center pt-4">
                      <button
                        onClick={loadMorePosts}
                        disabled={loading}
                        className="px-6 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50"
                      >
                        {loading ? 'Loading...' : 'Load More'}
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Create Post Tab */}
          {activeTab === 'create' && (
            <div className="space-y-4">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Title *
                  </label>
                  <input
                    type="text"
                    value={newPost.title}
                    onChange={(e) => setNewPost(prev => ({ ...prev, title: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="Enter post title"
                    maxLength={200}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Category *
                  </label>
                  <select
                    value={newPost.category}
                    onChange={(e) => setNewPost(prev => ({ ...prev, category: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    {categories.map((cat) => (
                      <option key={cat.value} value={cat.value}>
                        {cat.emoji} {cat.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Content *
                  </label>
                  <textarea
                    value={newPost.content}
                    onChange={(e) => setNewPost(prev => ({ ...prev, content: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    rows={6}
                    placeholder="Write your message..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Tags (optional)
                  </label>
                  <input
                    type="text"
                    value={newPost.tags}
                    onChange={(e) => setNewPost(prev => ({ ...prev, tags: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="Enter tags separated by commas"
                  />
                </div>

                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="pinned"
                    checked={newPost.is_pinned}
                    onChange={(e) => setNewPost(prev => ({ ...prev, is_pinned: e.target.checked }))}
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <label htmlFor="pinned" className="text-sm text-gray-700">
                    Pin this post to the top
                  </label>
                </div>

                {/* Image Upload */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Attach Image (optional)
                  </label>

                  {!selectedImage ? (
                    <div className="border-2 border-dashed border-gray-300 rounded-lg p-6">
                      <div className="text-center">
                        <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                          <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                        <div className="mt-4 space-y-4">
                          <div className="flex justify-center space-x-4">
                            <button
                              type="button"
                              onClick={() => fileInputRef.current?.click()}
                              className="bg-primary-600 text-white px-6 py-2 rounded-lg hover:bg-primary-700"
                            >
                              📁 Upload Image
                            </button>
                            <button
                              type="button"
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
                            Supports JPG, PNG images up to 10MB
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
                    <div className="relative">
                      <img
                        src={selectedImage}
                        alt="Preview"
                        className="max-w-full h-auto rounded-lg border max-h-64 object-cover"
                      />
                      <button
                        type="button"
                        onClick={clearImage}
                        className="absolute top-2 right-2 bg-red-500 text-white rounded-full w-8 h-8 flex items-center justify-center hover:bg-red-600"
                      >
                        ×
                      </button>
                    </div>
                  )}
                </div>
              </div>

              <div className="flex space-x-3">
                <button
                  onClick={() => setActiveTab('posts')}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={createPost}
                  disabled={!newPost.title.trim() || !newPost.content.trim() || submittingPost}
                  className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {submittingPost ? 'Creating...' : 'Create Post'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}