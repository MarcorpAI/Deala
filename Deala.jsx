"use client"

import { useState, useRef, useEffect } from "react"
import axios from "axios"
import { ACCESS_TOKEN } from "../constants"
import { motion, AnimatePresence } from "framer-motion"
import { 
  Star, ArrowUp, Loader2, Menu, X, 
  ChevronDown, ChevronUp, Bot, ShoppingCart,
  PlusCircle, Check, AlertCircle
} from "lucide-react"
import { Skeleton } from "../components/ui/skeleton"
import withSubscription from "../components/withSubscription"
import CartPage from "./CartPage"

const StarRating = ({ rating }) => {
  const numericRating = rating ? Number.parseFloat(rating) : 0
  const totalStars = 5
  const fullStars = Math.floor(numericRating)
  const hasHalfStar = numericRating % 1 >= 0.5

  return (
    <div className="flex items-center gap-1.5">
      <div className="flex">
        {[...Array(totalStars)].map((_, index) => (
          <Star
            key={index}
            size={18}
            className={`${
              index < fullStars
                ? "fill-amber-400 text-amber-400"
                : index === fullStars && hasHalfStar
                  ? "fill-amber-400/50 text-amber-400/50"
                  : "fill-zinc-700 text-zinc-700"
            } transition-colors`}
          />
        ))}
      </div>
      {numericRating > 0 && <span className="text-zinc-400 text-sm font-medium">{numericRating.toFixed(1)}</span>}
    </div>
  )
}

const ProductSkeleton = () => (
  <div className="relative bg-zinc-900/40 backdrop-blur-sm border border-zinc-800 rounded-xl overflow-hidden h-full">
    <div className="relative w-full pt-[75%]">
      <Skeleton className="absolute inset-0" />
    </div>
    <div className="p-6 space-y-4">
      <Skeleton className="h-6 w-3/4" />
      <Skeleton className="h-5 w-1/2" />
      <div className="flex items-center gap-1.5 mt-2">
        <div className="flex gap-0.5">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="w-4 h-4 rounded-full" />
          ))}
        </div>
      </div>
      <Skeleton className="h-4 w-1/3 mt-2" />
    </div>
  </div>
)

const MessageSkeleton = () => (
  <div className="flex justify-start mb-6">
    <div className="max-w-[85%] rounded-2xl p-6 bg-gradient-to-br from-amber-900/20 to-zinc-900/60 border border-amber-800/30 shadow-lg">
      <div className="flex items-start gap-4">
        <div className="mt-1 bg-amber-500/10 p-2 rounded-full">
          <Bot size={20} className="text-amber-400" />
        </div>
        <div className="flex-1 space-y-3">
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-5/6" />
        </div>
      </div>
    </div>
  </div>
)

const DealCard = ({ deal, onViewDeal, onAddToCart }) => {
  const [imageLoaded, setImageLoaded] = useState(false)
  const [adding, setAdding] = useState(false)
  const [added, setAdded] = useState(false)
  const [error, setError] = useState(null)

  const handleAddToCart = async (e) => {
    e.stopPropagation()  // Prevent triggering onViewDeal
    
    if (adding || added) return
    
    setAdding(true)
    setError(null)
    
    try {
      await onAddToCart(deal)
      setAdded(true)
      setTimeout(() => setAdded(false), 2000)  // Reset after 2 seconds
    } catch (err) {
      setError('Failed to add')
      setTimeout(() => setError(null), 2000)  // Clear error after 2 seconds
    } finally {
      setAdding(false)
    }
  }

  return (
    <motion.div
      className="group relative bg-zinc-900/40 backdrop-blur-sm border border-zinc-800 hover:border-zinc-700 rounded-xl overflow-hidden flex flex-col h-full transition-all duration-300"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      whileHover={{ y: -4 }}
    >
      <div className="relative w-full pt-[75%]">
        {!imageLoaded && <div className="absolute inset-0 bg-zinc-800/50 animate-pulse" />}
        <img
          src={deal.image_url || '/placeholder-product.jpg'}
          alt={deal.name}
          onLoad={() => setImageLoaded(true)}
          className={`absolute inset-0 w-full h-full object-cover transition-all duration-500 ease-out ${
            imageLoaded ? "opacity-100" : "opacity-0"
          } ${imageLoaded ? "group-hover:scale-105" : ""}`}
        />
        {deal.savings?.amount && (
          <div className="absolute top-3 right-3 z-20 bg-emerald-950/80 backdrop-blur-sm text-emerald-300 px-2.5 py-0.5 rounded-md text-xs font-medium border border-emerald-800/50">
            Save ${Number.parseFloat(deal.savings.amount).toFixed(2)}
          </div>
        )}
        
        {/* Add to cart button - top left */}
        <button
          onClick={handleAddToCart}
          className={`absolute top-3 left-3 z-20 rounded-full p-1.5 transition-all duration-200 ${
            adding ? 'bg-zinc-800/80 text-zinc-300' :
            added ? 'bg-green-800/80 text-green-300 border border-green-700/50' : 
            error ? 'bg-red-800/80 text-red-300 border border-red-700/50' :
            'bg-zinc-900/80 hover:bg-zinc-800/80 text-zinc-300 hover:text-zinc-100 backdrop-blur-sm hover:scale-110'
          }`}
          disabled={adding}
        >
          {adding ? (
            <Loader2 size={18} className="animate-spin" />
          ) : added ? (
            <Check size={18} />
          ) : error ? (
            <AlertCircle size={18} />
          ) : (
            <PlusCircle size={18} />
          )}
        </button>
      </div>

      <div className="relative z-20 p-6 flex flex-col flex-grow space-y-4">
        <h2 className="text-xl font-medium text-zinc-100 group-hover:text-zinc-200 transition-colors line-clamp-2">
          {deal.name || 'Unnamed Product'}
        </h2>

        <div className="flex-grow space-y-2">
          <StarRating rating={deal.rating} />
          <p className="text-zinc-500 text-sm">{deal.retailer || 'Unknown retailer'}</p>
        </div>

        <div className="mt-4 pt-4 border-t border-zinc-800/50">
          <div className="flex items-end justify-between mb-4">
            <div className="space-y-1">
              <p className="text-sm text-zinc-500 font-medium">Current Price</p>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-semibold text-zinc-100">
                  ${Number.parseFloat(deal.currentPrice || 0).toFixed(2)}
                </span>
                {deal.originalPrice && (
                  <span className="text-sm text-zinc-500 line-through">
                    ${Number.parseFloat(deal.originalPrice).toFixed(2)}
                  </span>
                )}
              </div>
            </div>
            {deal.savings?.percentage && (
              <div className="bg-rose-950/80 backdrop-blur-sm text-rose-300 px-3 py-1 rounded-md text-xs font-medium border border-rose-800/50">
                {Math.round(Number.parseFloat(deal.savings.percentage))}% OFF
              </div>
            )}
          </div>

          <motion.button
            onClick={() => onViewDeal(deal)}
            className="w-full py-3 px-4 rounded-md bg-zinc-800 hover:bg-zinc-700 text-zinc-100 font-medium text-sm transition-all duration-200"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            View Deal
          </motion.button>
        </div>
      </div>
    </motion.div>
  )
}

const Message = ({ message, onExpandProducts, expanded, onAddToCart }) => {
  // Process the message content for display
  const processMessageContent = () => {
    // Make sure message.content exists and is a string
    if (!message.content) {
      console.error('Missing message content');
      return { __html: 'Error displaying message' };
    }
    
    // Convert to string if it's not already
    let messageContent = message.content;
    if (typeof messageContent !== 'string') {
      console.warn('Message content is not a string, converting:', messageContent);
      try {
        messageContent = JSON.stringify(messageContent, null, 2);
      } catch (err) {
        console.error('Failed to stringify message content:', err);
        return { __html: 'Error displaying complex message' };
      }
    }
    
    // Apply basic Markdown-like formatting
    let content = messageContent
      .replace(/\n/g, "<br />")
      .replace(/<think>.*?<\/think>/gs, '')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .trim();
      
    return { __html: content };
  }
  
  const cleanContent = processMessageContent()

  return (
    <div className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} mb-6`}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className={`max-w-[85%] rounded-2xl p-6 ${
          message.role === 'user' 
            ? 'bg-gradient-to-br from-zinc-800 to-zinc-900 border border-zinc-700/50' 
            : 'bg-gradient-to-br from-amber-900/20 to-zinc-900/60 border border-amber-800/30'
        } shadow-lg`}
      >
        <div className="flex items-start gap-4">
          {message.role === 'assistant' && (
            <div className="mt-1 bg-amber-500/10 p-2 rounded-full">
              <Bot size={20} className="text-amber-400" />
            </div>
          )}
          <div className="flex-1">
            <div 
              className="text-zinc-100 whitespace-pre-wrap" 
              dangerouslySetInnerHTML={{ __html: cleanContent }}
            />
            
            {message.has_products && (
              <div className="text-amber-300 flex items-center cursor-pointer" onClick={() => onExpandProducts(message.id)}>
                <div className="flex items-center">
                  <ShoppingBag size={18} className="mr-1" />
                  <div className="font-medium">
                    {expanded ? "Hide Product Options" : `Show Product Options (${message.products?.length || 0})`}
                  </div>
                </div>
                <ChevronRight 
                  size={18} 
                  className={`ml-1 transition-transform ${expanded ? "rotate-90" : ""}`} 
                />
              </div>
            )}
            
            {expanded && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                transition={{ duration: 0.3 }}
                className="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3"
              >
                {message.products && message.products.length > 0 ? (
                  <div className="col-span-full mb-2 text-sm text-gray-400">
                    Showing {message.products.length} products
                  </div>
                ) : (
                  <div className="col-span-full mb-2 text-sm text-red-400 bg-red-900/20 p-2 rounded">
                    No products to display. Check console for details.
                  </div>
                )}
                {(message.products || []).map((deal, index) => (
                  <DealCard 
                    key={deal.id || index} 
                    deal={deal} 
                    onViewDeal={() => window.open(deal.productLink || '#', '_blank')} 
                    onAddToCart={onAddToCart}
                  />
                ))}
              </motion.div>
            )}
          </div>
        </div>
      </motion.div>
    </div>
  )
}

const Hero = () => {
  const [query, setQuery] = useState("")
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [expandedMessages, setExpandedMessages] = useState({})
  const [showMenu, setShowMenu] = useState(false)
  const [showIntro, setShowIntro] = useState(true)
  const [showCart, setShowCart] = useState(false)
  const [cartItemCount, setCartItemCount] = useState(0)
  const [sessionId, setSessionId] = useState(localStorage.getItem('dealSessionId') || null)

  const messagesEndRef = useRef(null)
  const textareaRef = useRef(null)
  const introBgRef = useRef(null)

  useEffect(() => {
    const checkScroll = () => {
      if (introBgRef.current) {
        const scrollPosition = window.scrollY
        introBgRef.current.style.transform = `translateY(${scrollPosition * 0.5}px)`
      }
    }

    window.addEventListener("scroll", checkScroll)
    return () => window.removeEventListener("scroll", checkScroll)
  }, [])
  
  // Check cart count when component mounts
  useEffect(() => {
    fetchCartCount()
  }, [])
  
  // Function to fetch cart item count
  const fetchCartCount = async () => {
    try {
      const response = await axios.get('/api/cart/view/', {
        params: { session_id: sessionId }
      })
      
      // Store the session ID if we get one back from the server
      if (response.data.session_id && !sessionId) {
        setSessionId(response.data.session_id)
        localStorage.setItem('dealSessionId', response.data.session_id)
      }
      
      setCartItemCount(response.data.item_count || 0)
    } catch (err) {
      console.error('Error fetching cart count:', err)
    }
  }

  useEffect(() => {
    const adjustHeight = () => {
      const textarea = textareaRef.current
      if (textarea) {
        textarea.style.height = "auto"
        textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`
      }
    }
    adjustHeight()
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, expandedMessages, query])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError("")

    if (!query.trim()) {
      setError("Please enter what you're looking for.")
      return
    }

    setLoading(true)

    const userMessage = {
      id: Date.now(),
      role: "user",
      content: query,
      has_products: false,
    }
    setMessages((prev) => [...prev, userMessage])
    setQuery("")

    try {
      const { data } = await axios.post(
        "http://127.0.0.1:8000/api/user-query/",
        { 
          query, 
          conversation_id: sessionId
        },
        {
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem(ACCESS_TOKEN)}`,
          },
        }
      )

      // Debug log to see the structure of the response
      console.log("API Response:", data);

      // Check if deals exist and restructure if needed
      const hasDeals = Array.isArray(data.deals) && data.deals.length > 0;
      
      // Make sure the response is a string
      let responseContent = data.response || "Here are some options:";
      
      // Handle the case where the response might be an object
      if (typeof responseContent === 'object') {
        console.warn('Response is an object instead of a string:', responseContent);
        try {
          // Try to convert to a meaningful string
          responseContent = JSON.stringify(responseContent, null, 2);
        } catch (err) {
          console.error('Failed to stringify response object:', err);
          responseContent = "[Error displaying response]";
        }
      }
      
      // Extra debugging for product data
      if (hasDeals) {
        console.log("Products found in response:", data.deals.length);
        console.log("Sample product:", data.deals[0]);
      } else {
        console.log("No product deals in response. has_products:", data.has_products);
      }
      
      const assistantMessage = {
        id: data.message_id || Date.now(),
        role: "assistant",
        content: responseContent,
        has_products: hasDeals,
        products: data.deals || [] // Directly use the deals array from the response
      }
      
      // Force double-check that products are properly structured
      if (assistantMessage.products && assistantMessage.products.length > 0) {
        console.log("Products added to message:", assistantMessage.products.length);
        // Ensure products have all required fields
        assistantMessage.products = assistantMessage.products.map(product => ({
          ...product,
          id: product.id || Math.random().toString(36).substring(7),
          name: product.name || product.title || "Product",
          currentPrice: typeof product.currentPrice === 'number' ? product.currentPrice : 0,
          image_url: product.image_url || "https://placehold.co/600x400/orange/white?text=Product"
        }));
      }

      setMessages((prev) => [...prev, assistantMessage])
      
      // Always log message to help with debugging
      console.log("Added assistant message:", {
        id: assistantMessage.id,
        has_products: assistantMessage.has_products,
        product_count: assistantMessage.products?.length || 0
      });
      
      // Auto-expand messages with products
      if (hasDeals) {
        console.log("Auto-expanding product section for message:", assistantMessage.id);
        setExpandedMessages(prev => ({
          ...prev, 
          [assistantMessage.id]: true // Automatically expand this product
        }));
      }

      if (!sessionId && data.conversation_id) {
        setSessionId(data.conversation_id)
      }
    } catch (err) {
      console.error("Error occurred:", err)
      setError(err.response?.data?.error || "An error occurred while processing your query.")
      
      setMessages(prev => [...prev, {
        id: Date.now(),
        role: "assistant",
        content: "Sorry, I encountered an error. Please try again.",
        has_products: false
      }])
    } finally {
      setLoading(false)
    }
  }

  const toggleExpandMessage = (messageId) => {
    setExpandedMessages((prev) => ({
      ...prev,
      [messageId]: !prev[messageId],
    }))
  }
  
  // Toggle cart visibility
  const toggleCart = () => {
    setShowCart(prev => !prev)
  }

  // Handle adding item to cart
  const handleAddToCart = async (product) => {
    try {
      const response = await axios.post('/api/cart/add_item/', {
        ...product,
        session_id: sessionId
      })
      
      // Update cart count
      setCartItemCount(response.data.item_count || cartItemCount + 1)
      
      // Store session ID if needed
      if (!sessionId && response.data.session_id) {
        setSessionId(response.data.session_id)
        localStorage.setItem('dealSessionId', response.data.session_id)
      }
      
      return response
    } catch (error) {
      console.error('Error adding to cart:', error)
      throw error
    }
  }

  return (
    <div className="min-h-screen bg-zinc-950 flex flex-col">
      <button
        onClick={() => setShowMenu(true)}
        className="fixed top-5 left-5 z-30 p-2 rounded-md bg-zinc-900/80 backdrop-blur-sm border border-zinc-800 text-zinc-400 hover:text-zinc-100 transition-colors"
      >
        <Menu size={20} />
      </button>

      <AnimatePresence>
        {showMenu && (
          <motion.div
            className="fixed top-0 left-0 h-full bg-zinc-900/90 backdrop-blur-md border-r border-zinc-800 z-50 w-64 shadow-xl"
            initial={{ x: "-100%" }}
            animate={{ x: 0 }}
            exit={{ x: "-100%" }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
          >
            <div className="flex flex-col h-full p-4">
              <div className="flex justify-between items-center mb-8 mt-2">
                <h2 className="text-zinc-100 text-lg font-medium">Menu</h2>
                <button
                  onClick={() => setShowMenu(false)}
                  className="p-1.5 rounded-md hover:bg-zinc-800 text-zinc-400 hover:text-zinc-100 transition-colors"
                >
                  <X size={18} />
                </button>
              </div>
              <button 
                className="flex items-center gap-3 w-full p-2.5 rounded-lg text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/70 transition-colors text-sm font-medium"
                onClick={() => {
                  setMessages([])
                  setShowMenu(false)
                }}
              >
                <ShoppingCart size={18} />
                <span>New Search</span>
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="flex-1 flex flex-col pt-16 pb-32 px-4 md:px-8 lg:px-12 overflow-y-auto">
        <div className="flex-1 flex flex-col justify-center w-full max-w-4xl mx-auto">
          {messages.length === 0 ? (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="text-center mb-8 relative min-h-[60vh] flex flex-col items-center justify-center"
            >
              <h1 className="text-4xl md:text-5xl font-medium text-zinc-100 mb-8">
                What are you buying today?
              </h1>

              <motion.div
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ duration: 0.3, delay: 0.2 }}
                className="max-w-xl mx-auto w-full"
              >
                <form onSubmit={handleSubmit} className="relative w-full">
                  <div className="relative w-full overflow-hidden rounded-xl border border-zinc-800 bg-zinc-900/90 backdrop-blur-md shadow-lg shadow-black/20 hover:border-zinc-700 transition-all duration-200">
                    <textarea
                      ref={textareaRef}
                      placeholder="I'm ready to find deals for you..."
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" && !e.shiftKey) {
                          e.preventDefault()
                          handleSubmit(e)
                        }
                      }}
                      rows={1}
                      className="w-full px-5 py-4 pr-14 text-base md:text-lg bg-transparent text-zinc-100 placeholder-zinc-500 focus:outline-none resize-none overflow-hidden min-h-[56px] max-h-[200px]"
                    />
                    <motion.button
                      type="submit"
                      disabled={loading}
                      className="absolute right-4 top-[50%] -translate-y-1/2 w-10 h-10 rounded-md bg-zinc-800 text-zinc-100 flex items-center justify-center hover:bg-zinc-700 transition-all duration-200 disabled:opacity-50"
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                    >
                      {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <ArrowUp className="w-5 h-5" />}
                    </motion.button>
                  </div>
                </form>
              </motion.div>
            </motion.div>
          ) : (
            <div className="space-y-6 w-full">
              {messages.map((message) => (
                <Message
                  key={message.id}
                  message={message}
                  onExpandProducts={toggleExpandMessage}
                  expanded={expandedMessages[message.id] || false}
                  onAddToCart={handleAddToCart}
                />
              ))}
              {loading && <MessageSkeleton />}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
      </div>
      
      {/* Cart Modal */}
      <AnimatePresence>
        {showCart && (
          <CartPage 
            onClose={toggleCart} 
            sessionId={sessionId}
            onCartUpdate={fetchCartCount}
          />
        )}
      </AnimatePresence>

      {messages.length > 0 && (
        <motion.div
          className="fixed bottom-8 left-0 right-0 z-40 px-4 md:px-8 pointer-events-none"
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.3 }}
        >
          <div className="max-w-4xl mx-auto pointer-events-auto">
            <form onSubmit={handleSubmit} className="relative w-full">
              <div className="relative w-full overflow-hidden rounded-xl border border-zinc-800 bg-zinc-900/90 backdrop-blur-md shadow-lg shadow-black/20 hover:border-zinc-700 transition-all duration-200">
                <textarea
                  ref={textareaRef}
                  placeholder="Ask a follow-up question..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault()
                      handleSubmit(e)
                    }
                  }}
                  rows={1}
                  className="w-full px-5 py-4 pr-14 text-base md:text-lg bg-transparent text-zinc-100 placeholder-zinc-500 focus:outline-none resize-none overflow-hidden min-h-[56px] max-h-[200px]"
                />
                <motion.button
                  type="submit"
                  disabled={loading}
                  className="absolute right-4 top-[50%] -translate-y-1/2 w-10 h-10 rounded-md bg-zinc-800 text-zinc-100 flex items-center justify-center hover:bg-zinc-700 transition-all duration-200 disabled:opacity-50"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <ArrowUp className="w-5 h-5" />}
                </motion.button>
              </div>
            </form>

            {error && (
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="mt-3 text-red-400 text-sm text-center"
              >
                {error}
              </motion.p>
            )}
          </div>
        </motion.div>
      )}
    </div>
  )
}

export default withSubscription(Hero)