"use client"

import { useState, useRef, useEffect } from "react"
import axios from "axios"
import { ACCESS_TOKEN } from "../constants"
import { motion, AnimatePresence } from "framer-motion"
import { 
  Star, ArrowUp, Loader2, Menu, X, 
  ChevronDown, ChevronUp, Bot, ShoppingCart
} from "lucide-react"
import { Skeleton } from "../components/ui/skeleton"
import withSubscription from "../components/withSubscription"

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

const DealCard = ({ deal, onViewDeal }) => {
  const [imageLoaded, setImageLoaded] = useState(false)

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

const Message = ({ message, onExpandProducts, expanded }) => {
  const getMessageContent = () => {
    if (typeof message.content === 'string') return message.content
    if (typeof message.content === 'object') return JSON.stringify(message.content)
    return 'No message content'
  }

  const cleanContent = getMessageContent()
    .replace(/<think>.*?<\/think>/gs, '')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .trim()

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
              <div className="mt-5">
                <button 
                  onClick={() => onExpandProducts(message.id)}
                  className="flex items-center gap-2 text-sm text-amber-400 hover:text-amber-300 transition-colors"
                >
                  {expanded ? (
                    <>
                      <ChevronUp size={16} />
                      <span>Hide options</span>
                    </>
                  ) : (
                    <>
                      <ChevronDown size={16} />
                      <span>Show options</span>
                    </>
                  )}
                </button>
                
                {expanded && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    transition={{ duration: 0.3 }}
                    className="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3"
                  >
                    {(message.products || []).map((deal, index) => (
                      <DealCard 
                        key={index} 
                        deal={deal} 
                        onViewDeal={() => window.open(deal.productLink || '#', '_blank')} 
                      />
                    ))}
                  </motion.div>
                )}
              </div>
            )}
          </div>
        </div>
      </motion.div>
    </div>
  )
}

const Hero = () => {
  const [query, setQuery] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [conversationId, setConversationId] = useState(null)
  const [messages, setMessages] = useState([])
  const [expandedMessages, setExpandedMessages] = useState({})
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const textareaRef = useRef(null)
  const messagesEndRef = useRef(null)

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
          conversation_id: conversationId
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
      
      const assistantMessage = {
        id: data.message_id || Date.now(),
        role: "assistant",
        content: data.response || "Here are some options:",
        has_products: hasDeals,
        products: data.deals || [] // Directly use the deals array from the response
      }

      setMessages((prev) => [...prev, assistantMessage])

      if (!conversationId && data.conversation_id) {
        setConversationId(data.conversation_id)
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
    setExpandedMessages(prev => ({
      ...prev,
      [messageId]: !prev[messageId]
    }))
  }

  return (
    <div className="min-h-screen bg-zinc-950 flex flex-col">
      <button
        onClick={() => setSidebarOpen(true)}
        className="fixed top-5 left-5 z-30 p-2 rounded-md bg-zinc-900/80 backdrop-blur-sm border border-zinc-800 text-zinc-400 hover:text-zinc-100 transition-colors"
      >
        <Menu size={20} />
      </button>

      <AnimatePresence>
        {sidebarOpen && (
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
                  onClick={() => setSidebarOpen(false)}
                  className="p-1.5 rounded-md hover:bg-zinc-800 text-zinc-400 hover:text-zinc-100 transition-colors"
                >
                  <X size={18} />
                </button>
              </div>
              <button 
                className="flex items-center gap-3 w-full p-2.5 rounded-lg text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/70 transition-colors text-sm font-medium"
                onClick={() => {
                  setMessages([])
                  setConversationId(null)
                  setSidebarOpen(false)
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
                />
              ))}
              {loading && <MessageSkeleton />}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
      </div>

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