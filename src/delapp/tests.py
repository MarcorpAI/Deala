from django.test import TestCase
from delapp.llm_engine import ConversationalDealFinder, ContextResolver, ProductRanker, ProductComparator
from unittest.mock import AsyncMock, MagicMock
import json

class ConversationalDealFinderTests(TestCase):
    def setUp(self):
        self.finder = ConversationalDealFinder()
        self.sample_products = [
            {'title': 'Red Nike Shoes', 'description': 'Comfortable running shoes', 'price': 49.99},
            {'title': 'Blue Adidas Sneakers', 'description': 'Stylish sneakers', 'price': 59.99},
            {'title': 'Green Puma Trainers', 'description': 'Lightweight trainers', 'price': 39.99},
        ]

    def test_detect_intent_new_search(self):
        query = "Find me Nike shoes under $50"
        intent = self.finder.detect_intent(query)
        self.assertEqual(intent['intent'], 'filter')
        self.assertTrue(intent['requires_search'])

    def test_detect_intent_followup(self):
        query = "Which of these is cheapest?"
        intent = self.finder.detect_intent(query)
        self.assertEqual(intent['intent'], 'followup')
        self.assertFalse(intent['requires_search'])

    def test_product_storage_and_followup_usage(self):
        # Simulate a search and store products
        self.finder.conversation_state = {}
        self.finder.conversation_state['current_products'] = self.sample_products
        # Follow-up query should use stored products
        query = "Which of these is cheapest?"
        intent = self.finder.detect_intent(query)
        if intent['intent'] == 'followup':
            products = self.finder.conversation_state.get('current_products', [])
            self.assertEqual(products, self.sample_products)

    def test_relaxed_filtering(self):
        # Should allow partial matches
        query = "Nike running"
        results = [p for p in self.sample_products if self.finder._validate_result_relevance(p, query)]
        self.assertTrue(any('Nike' in r['title'] for r in results))
        self.assertTrue(any('running' in r['description'] for r in results))
        # Should not filter out all relevant products
        self.assertGreaterEqual(len(results), 1)

class ContextResolverTests(TestCase):
    async def test_resolve_context_clear_reference(self):
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value.content = '{"products":["item1"],"filters":{"price":100}}'
        
        resolver = ContextResolver(mock_llm)
        previous = {'products': ['item1'], 'filters': {'price': 50}}
        result = await resolver.resolve_context("the cheaper one", previous)
        
        self.assertEqual(result['products'], ['item1'])
        self.assertEqual(result['filters']['price'], 100)

    async def test_resolve_context_needs_clarification(self):
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value.content = 'Which "cheaper one" do you mean? The laptop or the phone?'
        
        resolver = ContextResolver(mock_llm)
        result = await resolver.resolve_context("the cheaper one", {'products': ['laptop', 'phone']})
        
        self.assertIn('needs_clarification', result)
        self.assertIn('cheaper one', result['needs_clarification'])

class ProductRankerTests(TestCase):
    async def test_rank_with_persona(self):
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value.content = '''{
            "ranked_products": ["p2", "p1"],
            "explanation": "p2 better for programmers"
        }'''
        
        ranker = ProductRanker(mock_llm)
        result = await ranker.rank_products(
            [{'id': 'p1'}, {'id': 'p2'}],
            "gaming laptop",
            "programmer"
        )
        
        self.assertEqual(result['ranked_products'], ["p2", "p1"])
        self.assertIn('programmer', result['explanation'])

class ProductComparatorTests(TestCase):
    async def test_compare_products(self):
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value.content = '''{
            "comparison": "p1 has better specs",
            "key_differences": ["RAM", "GPU"],
            "recommendation": "p1 for gaming"
        }'''
        
        comparator = ProductComparator(mock_llm)
        result = await comparator.compare(
            [{'id': 'p1'}, {'id': 'p2'}],
            "which is better for gaming?"
        )
        
        self.assertIn('specs', result['comparison'])
        self.assertIn('RAM', result['key_differences'])
        self.assertIn('gaming', result['recommendation'])

class EnhancedFollowupTests(TestCase):
    def setUp(self):
        self.finder = ConversationalDealFinder()
        self.finder.conversation_state = {
            'user_preferences': {
                'test_user': {
                    'persona': 'gamer',
                    'max_price': 1000
                }
            }
        }
    
    def test_price_aware_questions(self):
        products = [
            {'price': 500}, 
            {'price': 1200}
        ]
        questions = self.finder._generate_followup_questions(
            products, 
            "gaming laptop", 
            "test_user"
        )
        
        self.assertTrue(any("budget" in q.lower() for q in questions))
    
    def test_persona_specific_questions(self):
        products = [{'price': 500}]
        questions = self.finder._generate_followup_questions(
            products,
            "gaming laptop",
            "test_user"
        )
        
        self.assertTrue(any("gamer" in q.lower() for q in questions))

class PreferenceLearningTests(TestCase):
    def setUp(self):
        self.finder = ConversationalDealFinder()
        
    def test_track_choices(self):
        """Test that choices are properly tracked"""
        self.finder.record_user_choice(
            'user1', 
            {'id': 'p1', 'price': 100, 'brand': 'Nike'}, 
            "running shoes"
        )
        self.assertEqual(len(self.finder.preference_learner.choice_history['user1']), 1)
        
    def test_analyze_preferences(self):
        """Test preference detection from history"""
        # Simulate multiple choices
        choices = [
            ({'price': 80, 'brand': 'Nike'}, "running shoes"),
            ({'price': 120, 'brand': 'Nike'}, "gaming shoes"),
            ({'price': 90, 'brand': 'Adidas'}, "programming shoes")
        ]
        
        for product, query in choices:
            self.finder.record_user_choice('user2', product, query)
            
        # Get inferred preferences
        prefs = self.finder.preference_learner.analyze_preferences('user2')
        
        # Should detect gaming/programming persona from queries
        self.assertIn(prefs['inferred_persona'], ['gamer', 'programmer'])
        # Should calculate price sensitivity (avg ~100)
        self.assertAlmostEqual(prefs['price_sensitivity'], 0.1, delta=0.05)
        # Should detect preferred brands
        self.assertEqual(prefs['preferred_brands'][0], 'nike')
        
    def test_auto_preference_update(self):
        """Test that preferences update automatically"""
        # Simulate multiple choices
        for i in range(3):
            self.finder.record_user_choice(
                'user3',
                {'price': 50 + i*10, 'brand': f'Brand{i}'},
                "test query"
            )
        
        # Check that preferences were updated
        prefs = self.finder.get_user_preferences('user3')
        self.assertLessEqual(prefs['max_price'], 72)  # 60 * 1.2
        self.assertEqual(len(prefs['preferred_brands']), 3)
