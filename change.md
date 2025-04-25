# ShopAgent: Refactoring to an Agentic Architecture

## Core Refactoring Strategy

This document outlines the complete refactoring plan to transform the current hardcoded intent-handler shopping assistant into a fully agentic system. The focus is on replacing the core functionality while maintaining compatibility with the existing project structure.

## Current Implementation Limitations

- Intent classification with rigid, hardcoded handlers
- Brittle response flow that breaks with unexpected queries
- Expanding codebase (2000+ lines) that grows with each feature
- Limited conversational capabilities
- Poor handling of complex, multi-turn interactions
- Difficulty maintaining context across the conversation

## New Agentic Architecture

### 1. Agent Core

The central reasoning engine that:
- Takes user queries directly
- Uses LLM reasoning to understand complex shopping intents
- Dynamically decides which tools to use based on the query
- Plans multi-step processes when necessary
- Synthesizes final responses from tool outputs

The Agent Core replaces all hardcoded intent routing and handler logic with dynamic reasoning and planning.

### 2. Tool Framework

A collection of specialized tools that the agent can call:

- **ProductSearchTool**: Searches for products based on dynamic query parameters
  - Replaces hardcoded search logic
  - Dynamically extracts search parameters from natural language
  - Handles filters, price ranges, sorting preferences

- **ProductDetailsTool**: Retrieves detailed information about specific products
  - Resolves product references from conversation context
  - Gets complete product specifications
  - Extracts relevant details based on user interests

- **ReviewsTool**: Fetches and analyzes product reviews
  - Gets reviews from SearchAPI.io
  - Summarizes review sentiment
  - Extracts key pros/cons from reviews
  - Identifies common themes in customer feedback

- **ComparisonTool**: Compares multiple products
  - Identifies key differences between products
  - Highlights relative strengths and weaknesses
  - Creates feature-by-feature comparisons
  - Summarizes overall value propositions

- **CartManagementTool**: Handles shopping cart operations
  - Adds products to cart
  - Views current cart
  - Removes items from cart
  - Updates quantities

Each tool replaces corresponding hardcoded handler logic with flexible, data-driven functions.

### 3. Memory System

A comprehensive context tracking system:

- **Conversation Memory**: Maintains conversation history
  - Tracks multi-turn interactions
  - Preserves important user statements
  - Enables reference resolution

- **Product Reference Tracker**: Maintains product context
  - Tracks all products mentioned in conversation
  - Resolves references like "the first one" or "the Ninja coffee maker"
  - Links previous searches to current conversation

- **User Preference Tracker**: Captures user preferences
  - Price sensitivity
  - Feature priorities
  - Brand preferences
  - Use case information

The memory system replaces the simple state dictionary with a sophisticated context manager.

### 4. Response Generator

Creates natural, contextually appropriate responses:

- Converts tool outputs to conversational language
- Maintains consistent tone and style
- Adapts detail level based on context
- Generates relevant follow-up questions
- Creates product summaries tailored to user interests

## Implementation Flow

1. **Define Tool Interfaces**
   - Create standard interfaces for all shopping tools
   - Define input/output schemas for each tool
   - Establish error handling patterns

2. **Build Core Tools**
   - Implement basic search functionality first
   - Add product detail retrieval
   - Develop review analysis capabilities
   - Create comparison functionality
   - Implement cart management

3. **Configure Agent Framework**
   - Set up LangChain agent with appropriate system prompts
   - Connect tools to agent framework
   - Configure reasoning patterns and examples

4. **Implement Memory Management**
   - Create conversation history tracking
   - Develop product reference resolution
   - Build preference tracking system

5. **Develop Response Generation**
   - Create response templates for different scenarios
   - Implement follow-up question generation
   - Format responses for frontend compatibility

6. **Test and Refine**
   - Test with complex shopping scenarios
   - Verify context retention across turns
   - Validate response quality and relevance

## Key Advantages of New Architecture

1. **Adaptability**: Handles diverse queries without requiring new code
2. **Scalability**: Adding features means adding tools, not rewriting core logic
3. **Context Awareness**: Maintains rich conversation context
4. **Natural Interactions**: Provides conversational, helpful responses
5. **Reasoning Power**: Uses LLM capabilities for complex decisions

## Example Scenarios

### Scenario 1: Product Reviews
**User**: "What are the reviews on the Ninja coffee maker?"

**Current System**: Fails because there's no hardcoded handler for reviews.

**New Agent System**:
1. Agent analyzes query and recognizes review intent
2. Agent checks if "Ninja coffee maker" refers to a product in context
3. Agent calls ReviewsTool to fetch reviews
4. Agent synthesizes review information into a helpful response
5. Agent suggests relevant follow-up questions

### Scenario 2: Complex Comparison
**User**: "Which one has better water filtration and how does that affect taste?"

**Current System**: Likely fails or gives generic response.

**New Agent System**:
1. Agent recognizes comparison intent with specific feature focus
2. Agent resolves "which one" to previously discussed products
3. Agent calls ProductDetailsTool to get filtration specifications
4. Agent calls ComparisonTool to compare this specific feature
5. Agent provides informed response about filtration differences and taste impact

## Integration Strategy

The new agent architecture will integrate with the existing project by:
1. Maintaining the same API endpoints
2. Preserving response formats expected by the frontend
3. Using the same data models for products and search results
4. Keeping compatible with existing authentication and user management

This refactoring completely replaces the core functionality while ensuring seamless integration with the rest of the application.