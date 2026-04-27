# Food Analysis Module

Intelligently parses user food information through natural language interaction, recognizing food types and estimating weights, calculating food calories and nutrition components.

## Core Capabilities

- **Semantic Analysis** - Understanding user's natural language descriptions of food content
- **Food Recognition** - Accurately recognizing food types in user descriptions
- **Entity Extraction** - Extracting key information such as food names and quantities
- **Weight Estimation** - Intelligently estimating food weight (grams) based on descriptions
- **Nutrition Component Estimation** - Estimating food calories and nutrition components based on public information and common sense reasoning
- **Standardized Output** - Generating standardized format containing food information and nutrition components

## Food Analysis Principles

### Methodology

When analyzing food, intelligent evaluation should be based on the following principles:

1. **Call Food Search API**

Use food search interface to obtain accurate calorie and nutrition component information for foods. This service covers over 56 countries and regions, providing over 2.3 million types of authoritative certified food data, covering calories, macronutrients, micronutrients, and other information. Data is continuously maintained by professional nutritionists and review teams based on official government publications, manufacturer materials, and multi-source verification information, with systematic review and updates performed daily to ensure the highest accuracy and authority of data.

**API Information**
- Endpoint: /foods/search
- Parameters:
  - query: Food name keyword
  - region: Country codes (US, CN, JP, etc.), optional, default value is US
- Note:
  - Intelligently select region parameter based on user's current conversation language, context information, user information, etc.

**Search Result Assessment**
- **Relevance Assessment**: After obtaining search results, must assess relevance between food names and query keywords, only strictly relevant results may be used as important reference
- **Adoption Assessment**:
  - Strictly relevant: Directly adopt nutrition component data of that result
  - Relevant but not strictly: Carefully evaluate its reference value, considering possible errors

2. **Call Food Analysis API**

Use food analysis interface, which is a more advanced integrated implementation optimized for in-depth analysis of complex dietary scenarios. This interface integrates multiple authoritative certified data sources, adopts the latest large language models with high reasoning capabilities, and provides high-precision assessments of food weight, calories, and nutritional components through end-to-end semantic understanding and multimodal fusion techniques, even when local model reasoning capabilities are limited, by leveraging cloud computing resources and optimization algorithms.

**API Information**
- Endpoint: /foods/analyze
- Parameters:
  - description: Food description in natural language
  - image_url: Publicly accessible URL of the food image. Supports JPEG, PNG, and other common image formats. When provided, the system will use image recognition to analyze the food.
- Note:
  - At least one of description or image_url must be provided
  - Should fully transmit the user's original food description input, ensuring no details are lost, including food names, quantities, weights, states, cooking methods, and other relevant information, to support comprehensive and accurate analysis by the interface.

**Output Content**
- Food name, weight, calories, protein, carbohydrates, fat, and other information
- Confidence and reasoning basis, helping to decide whether to trust the result

**Multi-Food Processing Strategy**
- **Independent Food Separation**: When user description contains multiple independent foods, should be split into multiple independent requests
  - Example: "I just ate an apple, a cup of milk, and a bun" → Split into three independent calls
  - Judgment criteria: Foods have clear separation, connected by parallel conjunctions such as comma, "and", etc., and each food maintains independent form
  
- **Composite Dish Merging**: When user description is a composite food or dish, should be treated as a single whole for one call
  - Example: "I just ate a serving of potato stewed beef" → Call once directly, no splitting
  - Judgment criteria: Ingredients are mixed and integrated, forming a dish with a specific name, users regard it as a single food unit

3. **API Call Failure or No Results Handling**:
   - Roughly estimate based on public information
   - Clearly inform users of data limitations
   - When API call limit is reached, prompt users with relevant limit information and guide next steps

## Complete Processing Flow

```
User Input
    ↓
[1] Input Type Judgment
    - Text input
    - Image input
    - Text and image input
    ↓
[2] Data Acquisition
    - Call food analysis API:
        - Use large models for deep analysis and reasoning
        - Obtain accurate food weight and nutrition component data
    - Or call food search API:
        - Obtain accurate nutrition component data through keyword search
    - When API call fails:
        - Estimate weight based on common portion sizes
        - Estimate calories and nutrition components based on public information
    ↓
[3] Generate Output
    - Standardize food names
    - Determine final weight (grams)
    - Output nutrition component estimation results
    ↓
Output Results
```

## Output Format

```json
{
  "meal_type": "breakfast",
  "items": [
    {
      "food_name": "Rice Porridge",
      "weight": 250,
      "calories": 75,
      "protein": 2.5,
      "carbs": 16,
      "fat": 0.5
    },
    {
      "food_name": "Steamed Bun",
      "weight": 180,
      "calories": 360,
      "protein": 12,
      "carbs": 50,
      "fat": 12
    }
  ]
}
```

## Tips for Improving Entry Accuracy

To help the agent more accurately recognize food types and assess weights, users can adopt the following methods:

### Text Input Tips
- **Detailed Description**: Provide specific food names, cooking methods, and portion sizes
- **Quantitative Information**: Provide specific weights or quantities when possible, such as "100g chicken breast", "one bowl of 200ml porridge"
- **Avoid Ambiguous Expressions**: Use clear quantity words, such as "one medium-sized apple" instead of "one apple"

### Voice Input Tips
- **Clear Pronunciation**: Moderate speech rate to ensure numbers and quantity words are clearly distinguishable
- **Complete Description**: Include food names, portions, and cooking methods
- **Quiet Environment**: Record in quiet environments to reduce background noise interference

### Image Input Tips
- **Include Reference Objects**: Include common items (e.g., mobile phones, utensils) in images as size references
- **Photograph Food Scales**: If using food scales for weight, ensure scale numbers are clearly visible
- **Photograph Nutrition Labels**: For packaged foods, photograph nutrition labels on packaging
- **Photograph Complete Packaging**: Include weight information and product names on packaging
- **Adequate Lighting**: Ensure images have adequate lighting and food details are clearly visible
- **Multi-angle Photography**: For complex foods, photograph from multiple angles to provide more comprehensive information
