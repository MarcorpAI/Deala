import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { motion } from 'framer-motion'
import { 
  X, ShoppingCart, Trash2, ArrowLeft, 
  ShoppingBag, AlertCircle, Loader2 
} from 'lucide-react'

/**
 * Cart Page Component
 * Shows saved items and allows removing them
 */
const CartPage = ({ onClose, user, sessionId }) => {
  const [cartItems, setCartItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [totalPrice, setTotalPrice] = useState(0)
  const [removingItem, setRemovingItem] = useState(null)

  // Load cart items on component mount
  useEffect(() => {
    fetchCartItems()
  }, [])

  // Fetch cart items from API
  const fetchCartItems = async () => {
    setLoading(true)
    try {
      const response = await axios.get('/api/cart/view/', {
        params: { session_id: sessionId }
      })
      setCartItems(response.data.items || [])
      setTotalPrice(response.data.total_price || 0)
      setError(null)
    } catch (err) {
      setError('Failed to load your cart. Please try again.')
      console.error('Error fetching cart:', err)
    } finally {
      setLoading(false)
    }
  }

  // Remove item from cart
  const removeItem = async (itemId) => {
    setRemovingItem(itemId)
    try {
      await axios.post('/api/cart/remove_item/', {
        item_id: itemId,
        session_id: sessionId
      })
      // Update local state
      setCartItems(cartItems.filter(item => item.id !== itemId))
      // Recalculate total price
      setTotalPrice(cartItems
        .filter(item => item.id !== itemId)
        .reduce((total, item) => total + parseFloat(item.price || 0), 0)
      )
    } catch (err) {
      setError('Failed to remove item from cart.')
      console.error('Error removing item:', err)
    } finally {
      setRemovingItem(null)
    }
  }

  // Clear entire cart
  const clearCart = async () => {
    if (!window.confirm('Are you sure you want to clear your entire cart?')) {
      return
    }
    
    setLoading(true)
    try {
      await axios.post('/api/cart/remove_item/', {
        remove_all: true,
        session_id: sessionId
      })
      setCartItems([])
      setTotalPrice(0)
    } catch (err) {
      setError('Failed to clear cart.')
      console.error('Error clearing cart:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <motion.div 
      className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 overflow-auto"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <div className="min-h-screen flex flex-col items-center justify-start py-8 px-4">
        <motion.div 
          className="w-full max-w-4xl bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden shadow-xl"
          initial={{ y: 50, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.1 }}
        >
          {/* Header */}
          <div className="relative bg-zinc-900 border-b border-zinc-800 p-5 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShoppingCart className="text-amber-400" />
              <h2 className="text-xl font-semibold text-zinc-100">Your Cart</h2>
              {cartItems.length > 0 && (
                <span className="ml-2 bg-amber-500/10 text-amber-400 text-sm px-2 py-0.5 rounded-full">
                  {cartItems.length} item{cartItems.length !== 1 ? 's' : ''}
                </span>
              )}
            </div>
            <div className="flex items-center gap-4">
              {cartItems.length > 0 && (
                <button 
                  onClick={clearCart}
                  className="text-sm text-zinc-400 hover:text-red-400 flex items-center gap-1"
                >
                  <Trash2 size={16} />
                  <span className="hidden sm:inline">Clear All</span>
                </button>
              )}
              <button 
                onClick={onClose} 
                className="p-1.5 rounded-full hover:bg-zinc-800 transition-colors text-zinc-400 hover:text-zinc-100"
              >
                <X size={20} />
              </button>
            </div>
          </div>

          {/* Cart Contents */}
          <div className="divide-y divide-zinc-800/50">
            {loading ? (
              <div className="py-12 flex flex-col items-center justify-center">
                <Loader2 className="h-10 w-10 text-amber-500/70 animate-spin mb-4" />
                <p className="text-zinc-400">Loading your cart...</p>
              </div>
            ) : cartItems.length === 0 ? (
              <div className="py-16 flex flex-col items-center justify-center">
                <div className="p-4 bg-zinc-800/30 rounded-full mb-4">
                  <ShoppingBag className="h-8 w-8 text-zinc-400" />
                </div>
                <h3 className="text-xl font-medium text-zinc-300 mb-2">Your cart is empty</h3>
                <p className="text-zinc-500 text-center max-w-md mb-6">
                  Items you save during your conversation will appear here.
                </p>
                <button 
                  onClick={onClose}
                  className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-100 rounded-lg transition-colors flex items-center gap-2"
                >
                  <ArrowLeft size={18} />
                  Return to Shopping
                </button>
              </div>
            ) : (
              <>
                {/* Cart Items */}
                <div className="divide-y divide-zinc-800/50">
                  {cartItems.map(item => (
                    <div key={item.id} className="p-4 sm:p-5 flex gap-4 relative">
                      {/* Item image */}
                      <div className="w-20 h-20 sm:w-24 sm:h-24 rounded-md overflow-hidden flex-shrink-0 bg-zinc-800">
                        <img 
                          src={item.image_url || '/placeholder-product.jpg'} 
                          alt={item.title}
                          className="w-full h-full object-cover"
                        />
                      </div>
                      
                      {/* Item details */}
                      <div className="flex-1 min-w-0">
                        <h3 className="text-zinc-100 font-medium line-clamp-2">{item.title}</h3>
                        <p className="text-amber-400 font-medium mt-1">
                          ${parseFloat(item.price).toFixed(2)}
                        </p>
                        <p className="text-zinc-500 text-sm mt-1">{item.retailer}</p>
                        
                        <div className="mt-2 flex items-center gap-3">
                          <a 
                            href={item.product_url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-sm text-amber-500 hover:text-amber-400 transition-colors"
                          >
                            View Product
                          </a>
                          
                          <button 
                            onClick={() => removeItem(item.id)}
                            disabled={removingItem === item.id}
                            className="text-sm text-zinc-400 hover:text-red-400 transition-colors flex items-center gap-1"
                          >
                            {removingItem === item.id ? (
                              <Loader2 size={14} className="animate-spin" />
                            ) : (
                              <Trash2 size={14} />
                            )}
                            Remove
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                
                {/* Cart Summary */}
                <div className="p-5 bg-zinc-900/80">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-zinc-400">Subtotal</span>
                    <span className="text-zinc-100 font-medium">${totalPrice.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-zinc-400">Items</span>
                    <span className="text-zinc-100">{cartItems.length}</span>
                  </div>
                  
                  <div className="mt-4 pt-4 border-t border-zinc-800">
                    <a 
                      href="#"
                      className="block w-full py-3 px-4 bg-amber-500 hover:bg-amber-600 text-amber-950 font-medium rounded-lg text-center transition-colors"
                    >
                      Checkout
                    </a>
                    <button 
                      onClick={onClose}
                      className="block w-full mt-2 py-2 px-4 bg-transparent border border-zinc-700 hover:border-zinc-600 text-zinc-300 rounded-lg text-center transition-colors"
                    >
                      Continue Shopping
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
          
          {/* Error message */}
          {error && (
            <div className="p-4 bg-red-950/30 border-t border-red-900/50 flex items-center gap-3">
              <AlertCircle className="text-red-400" size={20} />
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}
        </motion.div>
      </div>
    </motion.div>
  )
}

export default CartPage
